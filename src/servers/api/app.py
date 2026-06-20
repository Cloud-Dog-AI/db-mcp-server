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

from cloud_dog_jobs import JobStatus
from fastapi import APIRouter, Request

from cloud_dog_api_kit import create_app, success_envelope
from cloud_dog_api_kit.errors import UnauthorisedError
from cloud_dog_logging import Actor, Target
from cloud_dog_logging.middleware.audit import AuditMiddleware

from src.common.base_paths import configured_base_path, exempt_paths_for_surface
from src.common.http import APIKeyAuthMiddleware
from src.common.runtime import RuntimeFactory, build_health_router
from src.common.storage_paths import read_text_file, storage_exists, storage_for_path
from src.servers.api.access_control import create_access_control_router
from src.servers.api.discovery import create_discovery_router
from src.servers.api.saved_queries import create_saved_queries_router
from src.servers.api.schema_changes import create_schema_changes_router
from src.servers.api.source_connections import create_source_connections_router
from src.servers.api.test_data import create_test_data_router
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
        "request_auth_identity": job.request_auth_identity,
        "request_source": job.request_source,
        "request_auth_method": job.request_auth_method,
        "payload": job.payload,
    }


def _normalise_identity(value: object) -> str:
    """Normalise optional actor identifiers for owner checks."""
    return str(value or "").strip().casefold()


def _principal_is_jobs_admin(principal) -> bool:
    """Return whether a principal can administer all jobs."""
    roles = {_normalise_identity(role) for role in getattr(principal, "roles", []) or []}
    permissions = {str(permission or "").strip() for permission in getattr(principal, "permissions", []) or []}
    return bool({"admin", "system_admin"} & roles) or "*" in permissions or "jobs.delete" in permissions


def _principal_job_identities(principal) -> set[str]:
    """Return the actor identifiers that may own jobs for a principal."""
    return {
        identity
        for identity in (
            _normalise_identity(getattr(principal, "username", "")),
            _normalise_identity(getattr(principal, "user_id", "")),
        )
        if identity
    }


def _job_owner_identities(job) -> set[str]:
    """Return the owner identifiers recorded on a job."""
    return {
        identity
        for identity in (
            _normalise_identity(getattr(job, "request_auth_identity", "")),
            _normalise_identity(getattr(job, "user_id", "")),
        )
        if identity
    }


def _principal_can_access_job(principal, job) -> bool:
    """Return whether the principal can see or act on a job."""
    return _principal_is_jobs_admin(principal) or bool(_principal_job_identities(principal) & _job_owner_identities(job))


def _recent_jobs(runtime, *, limit: int = 50, job_type: str | None = None, principal=None) -> list[object]:
    """Return recent jobs without filtering out non-queued lifecycle states."""
    jobs = list(runtime.job_backend.all_jobs())
    jobs = [
        job
        for job in jobs
        if getattr(getattr(job, "status", None), "value", str(getattr(job, "status", "")))
        != JobStatus.ARCHIVED.value
    ]
    if principal is not None and not _principal_is_jobs_admin(principal):
        jobs = [job for job in jobs if _principal_can_access_job(principal, job)]
    if job_type:
        jobs = [job for job in jobs if str(getattr(job, "job_type", "")) == job_type]
    jobs.sort(
        key=lambda job: job.created_at.timestamp() if getattr(job, "created_at", None) else 0.0,
        reverse=True,
    )
    return jobs[: max(1, min(int(limit), 500))]


def _hard_delete_job_from_backend(backend, job_id: str) -> bool | None:
    """Remove a job from known backend implementations when a public delete API is absent."""
    sql_backend = getattr(backend, "_sql", None)
    redis_backend = getattr(backend, "_redis", None)
    if sql_backend is not None or redis_backend is not None:
        redis_deleted = _hard_delete_job_from_backend(redis_backend, job_id) if redis_backend is not None else None
        sql_deleted = _hard_delete_job_from_backend(sql_backend, job_id) if sql_backend is not None else None
        return bool(sql_deleted or redis_deleted)

    repo = getattr(backend, "_repo", None)
    if repo is not None and all(hasattr(repo, attr) for attr in ("engine", "jobs")):
        with repo.engine.begin() as conn:
            for table_name in ("job_call_logs", "job_deliveries", "job_callbacks"):
                table = getattr(repo, table_name, None)
                if table is not None:
                    conn.execute(table.delete().where(table.c.job_id == job_id))
            result = conn.execute(repo.jobs.delete().where(repo.jobs.c.job_id == job_id))
        return result.rowcount == 1

    jobs = getattr(backend, "_jobs", None)
    lock = getattr(backend, "_lock", None)
    if isinstance(jobs, dict):
        if lock is not None:
            with lock:
                return jobs.pop(job_id, None) is not None
        return jobs.pop(job_id, None) is not None

    redis_client = getattr(backend, "_client", None)
    job_key = getattr(backend, "_job_key", None)
    queue_key = getattr(backend, "_queue_key", None)
    if redis_client is not None and callable(job_key):
        key = job_key(job_id)
        redis_client.zrem(queue_key, job_id) if queue_key is not None else None
        return bool(redis_client.delete(key))

    return None


def _delete_job(runtime, job_id: str) -> bool:
    """Delete a platform job from the WebUI's administrative view."""
    if runtime.job_backend.get(job_id) is None:
        return False
    deleted = _hard_delete_job_from_backend(runtime.job_backend, job_id)
    if deleted is not None:
        return deleted
    return runtime.job_backend.update_status(job_id, JobStatus.ARCHIVED.value)


def _require_job_access(runtime, request: Request, job_id: str, *, permission: str) -> tuple[object, object | None]:
    """Require permission and same-actor access for non-admin job operations."""
    principal = runtime.access_control.require_request_permission(
        request,
        permission=permission,
        audit_resource_type="job",
        audit_resource_id=job_id,
    )
    job = runtime.job_queue.get(job_id)
    if job is not None and not _principal_can_access_job(principal, job):
        raise UnauthorisedError(message="Forbidden: only own jobs can be accessed")
    return principal, job


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


_SECRET_KEY_FRAGMENTS = (
    "password",
    "secret",
    "token",
    "api_key",
    "apikey",
    "credential",
    "private_key",
    "key_hash",
)


def _is_secret_config_key(path: str) -> bool:
    """Return True when a config path names a secret-like value."""
    lowered = path.lower()
    return any(fragment in lowered for fragment in _SECRET_KEY_FRAGMENTS)


def _servers_for_config_path(path: str) -> list[str]:
    """Return the db-mcp surface(s) that own a top-level config namespace."""
    top_key = path.split(".", 1)[0].split("[", 1)[0]
    return {
        "api_server": ["api"],
        "mcp_server": ["mcp"],
        "a2a_server": ["a2a"],
        "web_server": ["webui"],
        "web_login": ["webui"],
    }.get(top_key, ["api", "mcp", "a2a", "webui"])


def _build_config_source_map(value, path: str = "") -> tuple[dict[str, dict[str, object]], int, int]:
    """Build PS-73 source metadata for effective runtime config leaves."""
    if isinstance(value, MappingProxyType):
        value = dict(value)
    if isinstance(value, Mapping):
        sources: dict[str, dict[str, object]] = {}
        total = 0
        secret = 0
        for key, item in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            child_sources, child_total, child_secret = _build_config_source_map(item, child_path)
            sources.update(child_sources)
            total += child_total
            secret += child_secret
        return sources, total, secret
    if isinstance(value, list):
        sources: dict[str, dict[str, object]] = {}
        total = 0
        secret = 0
        for index, item in enumerate(value):
            child_sources, child_total, child_secret = _build_config_source_map(item, f"{path}[{index}]")
            sources.update(child_sources)
            total += child_total
            secret += child_secret
        return sources, total, secret

    is_secret = _is_secret_config_key(path)
    return (
        {
            path: {
                "source": "default",
                "secret": is_secret,
                "servers": _servers_for_config_path(path),
            }
        },
        1,
        1 if is_secret else 0,
    )


def _current_principal(request: Request) -> dict[str, object]:
    """Return the authenticated principal fields used by the WebUI."""
    return {
        "user_id": getattr(request.state, "user", None),
        "username": getattr(request.state, "username", None),
        "roles": list(getattr(request.state, "roles", []) or []),
        "permissions": list(getattr(request.state, "permissions", []) or []),
        "api_key_id": getattr(request.state, "api_key_id", None),
        "profile_ids": list(getattr(request.state, "profile_ids", []) or []),
        "scopes": list(getattr(request.state, "scopes", []) or []),
        "tenant_id": getattr(request.state, "tenant_id", None),
    }


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

    @router.get("/auth/me")
    async def auth_me(request: Request) -> dict:
        """Return the authenticated API-key principal."""
        principal = runtime.access_control.principal_from_request(request)
        return success_envelope(runtime.access_control.principal_summary(principal))

    @router.get("/jobs/status")
    async def jobs_status() -> dict:
        """Return queue status counters from the configured platform backend."""
        return success_envelope(
            {
                "backend": runtime.job_backend_name,
                "queue_status": runtime.job_backend.get_queue_status(),
            }
        )

    @router.get("/jobs/health")
    async def jobs_health() -> dict:
        """Return queue health using the legacy WebUI route name."""
        return success_envelope(
            {
                "status": "ok",
                "backend": runtime.job_backend_name,
                "queue_status": runtime.job_backend.get_queue_status(),
            }
        )

    @router.get("/jobs/queue/status")
    async def jobs_queue_status() -> dict:
        """Return queue status counters for the Web UI jobs dashboard."""
        return success_envelope(runtime.job_backend.get_queue_status())

    @router.get("/jobs/queue-status")
    async def jobs_queue_status_legacy() -> dict:
        """Return queue status for older deployment evidence probes."""
        return success_envelope(runtime.job_backend.get_queue_status())

    @router.get("/metrics")
    async def metrics() -> dict:
        """Return structured resource metrics for the db-mcp dashboard."""
        return success_envelope(_resource_metrics(runtime))

    @router.get("/config")
    async def config_dump() -> dict:
        """Return the effective runtime configuration with secrets masked."""
        return success_envelope(_mask_runtime_config(runtime.config.data))

    @router.get("/config/sources")
    async def config_sources() -> dict:
        """Return per-leaf source metadata for the effective runtime config."""
        sources, total, secret = _build_config_source_map(_mask_runtime_config(runtime.config.data))
        return success_envelope(
            {
                "sources": sources,
                "counts": {
                    "total": total,
                    "secret": secret,
                    "by_source": {"default": total},
                },
            }
        )

    @router.post("/config/audit-reveal")
    async def audit_config_reveal(request: Request) -> dict:
        """Audit an admin reveal of masked Settings secrets."""
        principal = _current_principal(request)
        try:
            runtime.audit_logger.log_privileged(
                actor=Actor(
                    type="user",
                    id=str(principal.get("user_id") or principal.get("username") or "unknown"),
                    roles=list(principal.get("roles") or []),
                ),
                action="config.reveal",
                target=Target(type="config", id="effective-runtime"),
                outcome="success",
                command_text="settings reveal secrets",
                secret_paths=[
                    path
                    for path, meta in _build_config_source_map(_mask_runtime_config(runtime.config.data))[0].items()
                    if bool(meta.get("secret"))
                ],
            )
        except Exception:
            pass
        return success_envelope({"audited": True})

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
    async def jobs(request: Request, limit: int = 50, job_type: str | None = None) -> dict:
        """Return recent platform jobs for the jobs page."""
        principal = runtime.access_control.require_request_permission(
            request,
            permission="data.read",
            audit_resource_type="job",
            audit_resource_id="jobs",
        )
        return success_envelope(
            {
                "items": [
                    _serialise_job(job)
                    for job in _recent_jobs(runtime, limit=limit, job_type=job_type, principal=principal)
                ],
            }
        )

    @router.get("/jobs/{job_id}")
    async def get_job(job_id: str, request: Request) -> dict:
        """Return a single platform job by identifier."""
        _principal, job = _require_job_access(runtime, request, job_id, permission="data.read")
        return success_envelope(_serialise_job(job) if job else {})

    @router.post("/jobs/{job_id}/cancel")
    async def cancel_job(job_id: str, request: Request) -> dict:
        """Cancel a running or queued platform job."""
        _require_job_access(runtime, request, job_id, permission="index.manage")
        return success_envelope({"cancelled": runtime.job_queue.cancel(job_id), "job_id": job_id})

    @router.post("/jobs/{job_id}/retry")
    async def retry_job(job_id: str, request: Request) -> dict:
        """Return a failed or waiting platform job to the queued state."""
        _require_job_access(runtime, request, job_id, permission="index.manage")
        return success_envelope(
            {
                "retried": runtime.job_backend.update_status(job_id, JobStatus.QUEUED.value),
                "job_id": job_id,
            }
        )

    @router.delete("/jobs/{job_id}")
    async def delete_job(job_id: str, request: Request) -> dict:
        """Delete a platform job from the administrative jobs view."""
        principal, job = _require_job_access(runtime, request, job_id, permission="index.manage")
        if not _principal_is_jobs_admin(principal):
            raise UnauthorisedError(message="Forbidden: delete requires admin")
        deleted = _delete_job(runtime, job_id)
        if deleted:
            runtime.audit_logger.log_crud(
                actor=Actor(type="user", id=principal.user_id, roles=principal.roles),
                action="delete",
                target=Target(type="job", id=job_id),
                outcome="success",
                job_type=getattr(job, "job_type", None),
                job_status=getattr(getattr(job, "status", None), "value", None),
            )
        return success_envelope({"deleted": deleted, "job_id": job_id})

    app.include_router(router)
    app.include_router(create_access_control_router(runtime, api_base_path))
    # W28A-876: mirror the IDAM access-control routes under /v1/admin/* so the
    # shared @cloud-dog/idam pages (which call /v1/admin/<entity> via the web
    # /webapi cookie bridge) resolve against the same handlers + auth.
    app.include_router(create_access_control_router(runtime, (api_base_path or "") + "/admin"))
    # W28A-876: mount the canonical SHARED cloud_dog_idam /idam/v1 router
    # (resource-registry + rbac-bindings) so the shared @cloud-dog/idam RBAC
    # page resolves /v1/idam/v1/*.
    from cloud_dog_idam.api.fastapi.router import idam_v1_router

    app.include_router(idam_v1_router, prefix=api_base_path or "")
    # W28A-871-R2: register the data-admin backend routers (source connections,
    # discovery, saved queries, schema-change approval, gated test-data seed)
    # consumed by the W28A-871 db-mcp WebUI (apps/db-mcp api.ts).
    app.include_router(create_discovery_router(runtime, api_base_path))
    app.include_router(create_saved_queries_router(runtime, api_base_path))
    app.include_router(create_schema_changes_router(runtime, api_base_path))
    app.include_router(create_source_connections_router(runtime, api_base_path))
    app.include_router(create_test_data_router(runtime, api_base_path))
    return app
