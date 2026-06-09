# Copyright 2026 Cloud-Dog, Viewdeck Engineering Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Description: API server application factory for db-mcp-server.
# Related requirements: W28A-274-A deliverables 1, 2, AC-01, AC-02, AC-03
# Related tests: UT1.2, ST1.1, ST1.2, IT1.1

"""API server application for db-mcp-server."""

from __future__ import annotations

import json
import os
import resource
from collections.abc import Mapping
from datetime import datetime, timezone
from types import MappingProxyType

from fastapi import APIRouter

from cloud_dog_api_kit import create_app, success_envelope
from cloud_dog_logging.middleware.audit import AuditMiddleware

from src.common.base_paths import configured_base_path, exempt_paths_for_surface
from src.common.http import APIKeyAuthMiddleware
from src.common.runtime import RuntimeFactory, build_health_router
from src.common.storage_paths import read_text_file, storage_exists, storage_for_path
from src.servers.api.access_control import create_access_control_router
from cloud_dog_idam.rbac import RBACEngine as _RBACEngine  # PS-70 RBAC enforcement

_rbac_engine = _RBACEngine()


def _has_permission(user_id: str, permission: str) -> bool:
    """PS-70 RBAC permission check via cloud_dog_idam."""
    return _rbac_engine.has_permission(user_id, permission)


def _checked_out_connections(runtime) -> int:
    """Return the current checked-out SQLAlchemy connection count."""
    total = 0
    for engine in (runtime.metadata_engine, runtime.audit_engine):
        pool = getattr(engine, "pool", None)
        checked_out = getattr(pool, "checkedout", None)
        if callable(checked_out):
            total += int(checked_out())
    return total


def _resource_metrics(runtime) -> dict[str, object]:
    """Build structured host and service metrics for the dashboard."""
    uptime_seconds = int((datetime.now(timezone.utc) - runtime.started_at).total_seconds())
    rss_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    memory_mb = round(rss_kb / 1024, 2)
    cpu_count = os.cpu_count() or 1
    try:
        cpu_percent = round((os.getloadavg()[0] / cpu_count) * 100, 2)
    except OSError:
        cpu_percent = 0.0
    disk_total, disk_used, _disk_free = storage_for_path("runtime-placeholder")[0].disk_usage()
    disk_percent = round((disk_used / disk_total) * 100, 2) if disk_total else 0.0
    return {
        "uptime": uptime_seconds,
        "memory_mb": memory_mb,
        "cpu_percent": cpu_percent,
        "disk_percent": disk_percent,
        "active_connections": _checked_out_connections(runtime),
    }


def _serialise_job(job) -> dict[str, object]:
    """Convert a platform job record into a JSON-safe response payload."""
    status = getattr(job.status, "value", str(job.status))
    created_at = job.created_at.isoformat() if job.created_at else None
    updated_at = job.updated_at.isoformat() if job.updated_at else None
    progress = {
        "queued": 0,
        "running": 50,
        "completed": 100,
        "failed": 100,
        "cancelled": 100,
    }.get(str(status), None)
    duration_seconds = None
    if job.created_at and job.updated_at:
        duration_seconds = max(int((job.updated_at - job.created_at).total_seconds()), 0)
    return {
        "id": job.job_id,
        "name": job.job_type,
        "queue_name": job.queue_name,
        "status": status,
        "progress": progress,
        "created_at": created_at,
        "updated_at": updated_at,
        "duration_seconds": duration_seconds,
        "correlation_id": job.correlation_id,
        "user_id": job.user_id,
        "payload": job.payload,
    }


def _read_log_entries(surface: str, limit: int) -> list[dict[str, object]]:
    """Read JSON log entries for a server surface from the local log file."""
    log_path = f"logs/{surface}.log"
    if not storage_exists(log_path):
        return []
    entries: list[dict[str, object]] = []
    for line in read_text_file(log_path, encoding="utf-8").splitlines():
        record = line.strip()
        if not record.startswith("{"):
            continue
        try:
            payload = json.loads(record)
        except json.JSONDecodeError:
            continue
        message = str(payload.get("message", "")).strip()
        if not message:
            continue
        logger_name = str(payload.get("logger", surface))
        correlation_id = str(payload.get("correlation_id", "")).strip() or "-"
        entries.append(
            {
                "id": correlation_id if correlation_id != "-" else f"{surface}:{len(entries)}",
                "timestamp": payload.get("timestamp"),
                "level": payload.get("level", "INFO"),
                "logger": logger_name,
                "message": message,
                "correlation_id": correlation_id,
                "source": logger_name,
            }
        )
    return list(reversed(entries[-max(1, min(limit, 500)):]))


def _mask_runtime_config(value, parent_key: str = ""):
    """Redact secret-like values before returning config to the Web UI."""
    if isinstance(value, MappingProxyType):
        value = dict(value)
    if isinstance(value, Mapping):
        masked = {}
        for key, item in value.items():
            lowered = str(key).lower()
            if any(fragment in lowered for fragment in ("password", "secret", "token", "api_key", "apikey", "credential", "private_key", "key_hash")):
                masked[key] = item if item in (None, "", [], {}) else "****"
                continue
            masked[key] = _mask_runtime_config(item, lowered)
        return masked
    if isinstance(value, list):
        return [_mask_runtime_config(item, parent_key) for item in value]
    if isinstance(value, tuple):
        return [_mask_runtime_config(item, parent_key) for item in value]
    if isinstance(value, set):
        return sorted(_mask_runtime_config(item, parent_key) for item in value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, "model_dump"):
        return _mask_runtime_config(value.model_dump(mode="json"), parent_key)
    return str(value)


def create_api_app(explicit_env_files: list[str] | None = None):
    """Create the db-mcp-server API application."""
    runtime = RuntimeFactory.create(explicit_env_files)
    api_base_path = configured_base_path(runtime.config, "api")
    app = create_app(
        title="db-mcp-server API",
        version=str(runtime.config.get("app.version", "0.1.0")),
        api_prefix=api_base_path or "",
        enable_health=False,
        cors_origins=list(runtime.config.get("api_server.cors_origins", [])),
        enable_audit_logging=False,
    )
    app.state.runtime = runtime
    app.include_router(build_health_router(runtime, "db-mcp-server-api"))
    if api_base_path:
        app.include_router(build_health_router(runtime, "db-mcp-server-api"), prefix=api_base_path)
    app.add_middleware(
        APIKeyAuthMiddleware,
        verify_api_key=runtime.auth.verify_api_key,
        exempt_paths=exempt_paths_for_surface(api_base_path),
        # W28A-889-B-R2 / W28A-890: resolve a forwarded webui user to its own RBAC
        # principal so the web tier cannot collapse every session to service-admin.
        resolve_web_user=runtime.access_control.principal_for_username,
    )
    # W28A-529: Outermost audit middleware — captures auth failures (401/403)
    # that are returned by APIKeyAuthMiddleware before reaching create_app()'s
    # inner AuditMiddleware.  The inner copy is skipped for paths already
    # audited here (duplicate suppression is handled by the ASGI ordering).
    app.add_middleware(AuditMiddleware)

    router = APIRouter(prefix=api_base_path, tags=["api"])

    @router.get("/ping")
    async def ping() -> dict:
        """Return a minimal authenticated runtime summary."""
        return success_envelope(
            {
                "service": "db-mcp-server",
                "surface": "api",
                "jobs_backend": runtime.job_backend_name,
                "metadata_store": str(runtime.config.get("metadata_store.uri")),
            }
        )

    @router.get("/jobs/status")
    async def jobs_status() -> dict:
        """Return queue status counters from the configured platform backend."""
        return success_envelope(
            {
                "backend": runtime.job_backend_name,
                "queue_status": runtime.job_backend.get_queue_status(),
            }
        )

    @router.get("/jobs/queue/status")
    async def jobs_queue_status() -> dict:
        """Return queue status counters for the Web UI jobs dashboard."""
        return success_envelope(runtime.job_backend.get_queue_status())

    @router.get("/metrics")
    async def metrics() -> dict:
        """Return structured resource metrics for the db-mcp dashboard."""
        return success_envelope(_resource_metrics(runtime))

    @router.get("/config")
    async def config_dump() -> dict:
        """Return the effective runtime configuration with secrets masked."""
        return success_envelope(_mask_runtime_config(runtime.config.data))

    @router.get("/logs")
    async def logs(surface: str = "api", limit: int = 200) -> dict:
        """Return parsed JSON log entries for the requested server surface."""
        return success_envelope(
            {
                "surface": surface,
                "items": _read_log_entries(surface, limit),
            }
        )

    @router.get("/jobs")
    async def jobs(limit: int = 50, job_type: str | None = None) -> dict:
        """Return recent platform jobs for the jobs page."""
        return success_envelope(
            {
                "items": [_serialise_job(job) for job in runtime.job_queue.list(limit=limit, job_type=job_type)],
            }
        )

    @router.get("/jobs/{job_id}")
    async def get_job(job_id: str) -> dict:
        """Return a single platform job by identifier."""
        job = runtime.job_queue.get(job_id)
        return success_envelope(_serialise_job(job) if job else {})

    @router.post("/jobs/{job_id}/cancel")
    async def cancel_job(job_id: str) -> dict:
        """Cancel a running or queued platform job."""
        return success_envelope({"cancelled": runtime.job_queue.cancel(job_id), "job_id": job_id})

    app.include_router(router)
    app.include_router(create_access_control_router(runtime, api_base_path))
    # W28A-876: mirror the IDAM access-control routes under /v1/admin/* so the
    # shared @cloud-dog/idam pages (which call /v1/admin/<entity> via the web
    # /webapi cookie bridge) resolve against the same handlers + auth.
    app.include_router(create_access_control_router(runtime, (api_base_path or "") + "/admin"))
    # W28A-876: mount the canonical SHARED cloud_dog_idam /idam/v1 router (resource-registry +
    # rbac-bindings) so the shared @cloud-dog/idam RBAC page resolves /v1/idam/v1/*. ONE
    # implementation for the whole estate (cloud_dog_idam>=0.4.1); bound to this service's engine.
    from cloud_dog_idam.api.fastapi.router import idam_v1_router, set_idam_v1_engine
    set_idam_v1_engine(runtime.metadata_engine)
    app.include_router(idam_v1_router, prefix=api_base_path or "")
    return app
