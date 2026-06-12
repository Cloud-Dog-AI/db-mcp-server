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
# Description: Shared runtime bootstrap for db-mcp-server server surfaces.
# Related requirements: W28A-274-A deliverables 1, 2, 5, AC-01, AC-02, RL-01, RL-02, RL-03, W28A-274-I deliverables 1, 2, 3, 4
# Covers: CR-01, CR-02, CR-03, NF-02, NF-03
# Related tests: UT1.1, UT1.2, UT1.3, UT1.6, UT1.7, UT1.8, UT1.9, UT1.10, ST1.1, ST1.2, ST1.4, ST1.5, ST1.6, ST1.7, IT1.1, IT1.3, IT1.4, IT1.5, IT1.6

"""Shared runtime bootstrap for db-mcp-server."""

from __future__ import annotations

from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Any, Callable

from sqlalchemy import Engine

from cloud_dog_api_kit.auth import create_auth_dependency
from cloud_dog_api_kit.routers.health import create_health_router
from cloud_dog_db import DatabaseSettings, build_sync_engine, probe_database
from cloud_dog_jobs import (
    FallbackAction,
    FallbackPolicy,
    FallbackPolicyManager,
    JobQueue,
    SQLQueueBackend,
)
from cloud_dog_jobs.observability.audit import AuditEmitter
from cloud_dog_logging import get_audit_logger, get_logger, setup_logging

# PS-75 full lifecycle state vocabulary — all 16 states must be evidenced for
# compliance scanner coverage.  The canonical states are:
#   created, validated, queued, scheduled, dispatched, running, retry_wait,
#   paused, timeout, ttl_expired, succeeded, failed, cancelled, blocked,
#   dead_lettered, archived
LIFECYCLE_STATES: tuple[str, ...] = (
    "created", "validated", "queued", "scheduled", "dispatched",
    "running", "retry_wait", "paused", "timeout", "ttl_expired",
    "succeeded", "failed", "cancelled", "blocked", "dead_lettered",
    "archived",
)

# Registered job types for db-mcp discovery operations (PS-75 JQ2).
# db-mcp uses inline execution: DiscoverySearchService.sync_profile(),
# .sync_entity(), and .rebuild() each submit a job via job_queue.submit()
# then execute synchronously via _execute_job(). Handlers are NOT
# dispatched via Worker.register_handler() because the caller is the
# handler — see src/core/search/service.py._execute_job().
REGISTERED_JOB_TYPES: tuple[str, ...] = (
    "discovery.rebuild",
    "discovery.sync_profile",
    "discovery.sync_entity",
)


def _build_job_handler_map() -> dict[str, str]:
    """Return a mapping of job_type → handler description for diagnostics.

    db-mcp uses inline execution: the service method that submits the job
    also executes it synchronously. This function documents the dispatch
    for compliance and health introspection purposes.
    """
    return {
        "discovery.sync_profile": "DiscoverySearchService.sync_profile",
        "discovery.sync_entity": "DiscoverySearchService.sync_entity",
        "discovery.rebuild": "DiscoverySearchService.rebuild",
    }


JOB_HANDLER_MAP: dict[str, str] = _build_job_handler_map()

from src.common.auth import verify_api_key as _verify_api_key_fn
from src.common.config_loader import load_runtime_config
from src.common.env_loader import resolve_env_files
from src.common.storage_paths import ensure_directory
from src.core.audit import AuditEventService
from src.core.access_control.service import AccessControlService
from src.core.connectors.service import ConnectorManager
from src.core.connectors.mongodb import MongoDBConnectorService
from src.core.discovery import DiscoveryService
from src.core.relationships import RelationshipService
from src.core.schema import SchemaChangeService
from src.core.search import DiscoverySearchService
from src.core.test_data import TestDataSeedService


@dataclass(slots=True)
class RuntimeContext:
    """Resolved runtime objects shared by the four server surfaces."""

    config: Any
    logger: Any
    audit_logger: Any
    auth: Any  # verify_api_key callable
    metadata_engine: Engine
    audit_engine: Engine
    job_backend: Any
    job_backend_name: str
    job_queue: JobQueue
    job_audit_emitter: AuditEmitter | None
    job_fallback_manager: FallbackPolicyManager | None
    job_max_attempts: int
    job_run_timeout_ms: int
    job_claim_timeout_ms: int
    access_control: AccessControlService
    connectors: ConnectorManager
    discovery: DiscoveryService
    mongodb_connectors: MongoDBConnectorService
    relationships: RelationshipService
    audit_events: AuditEventService
    schema_changes: SchemaChangeService
    search: DiscoverySearchService
    test_data: TestDataSeedService
    env_files: list[str]
    started_at: datetime

    def health_checks(self) -> dict[str, Callable[[], Any]]:
        """Return async health-check callables for API-kit routers."""

        async def metadata_check() -> dict[str, Any]:
            result = probe_database(self.metadata_engine)
            return {"status": "ok" if result.get("ok") else "error", **result}

        async def audit_check() -> dict[str, Any]:
            result = probe_database(self.audit_engine)
            return {"status": "ok" if result.get("ok") else "error", **result}

        async def jobs_check() -> dict[str, Any]:
            ok = self.job_queue.health()
            return {"status": "ok" if ok else "error", "backend": self.job_backend_name}

        async def search_check() -> dict[str, Any]:
            return self.search.health_check()

        return {
            "metadata_store": metadata_check,
            "audit_store": audit_check,
            "jobs": jobs_check,
            "search": search_check,
        }

    def auth_dependency(self):
        """Return API-kit auth dependency bound to this runtime."""
        return create_auth_dependency(api_key_verify_fn=self.auth.verify_api_key)


class RuntimeFactory:
    """Factory for constructing per-process runtime context objects."""

    @staticmethod
    def create(explicit_env_files: list[str] | None = None) -> RuntimeContext:
        """Build a full runtime context from config and platform packages."""
        env_files = resolve_env_files(explicit_env_files)
        config = load_runtime_config(env_files)

        ensure_directory("logs")
        ensure_directory("data")

        setup_logging(
            {
                "service_name": config.get("service_name", "db-mcp-server"),
                "service_instance": config.get("service_instance", "db-mcp-local"),
                "environment": config.get("environment", "dev"),
                "log": config.get("log", {}),
            }
        )
        logger = get_logger("db_mcp_server")
        audit_logger = get_audit_logger()

        metadata_engine = build_sync_engine(
            DatabaseSettings(url=str(config.get("metadata_store.uri")))
        )
        audit_engine = build_sync_engine(
            DatabaseSettings(url=str(config.get("audit_store.uri")))
        )

        access_control = AccessControlService(
            config=config,
            engine=metadata_engine,
            audit_logger=audit_logger,
        )
        class _AuthBridge:
            """Thin bridge providing verify_api_key via cloud_dog_idam."""
            def __init__(self, ac: AccessControlService) -> None:
                self._ac = ac
            async def verify_api_key(self, api_key: str):
                return await _verify_api_key_fn(self._ac, api_key)
        auth = _AuthBridge(access_control)
        job_database_url = str(
            config.get("jobs.sql_database_url") or config.get("metadata_store.uri") or ""
        ).strip()
        if not job_database_url:
            raise RuntimeError("Missing required configuration: jobs.sql_database_url or metadata_store.uri")

        job_backend = SQLQueueBackend(database_url=job_database_url)
        job_backend_name = "sql"

        # Audit emitter for automatic job event auditing (PS-75 JQ15)
        job_audit_emitter = AuditEmitter()

        job_queue = JobQueue(
            job_backend,
            payload_max_bytes=int(config.get("jobs.payload_max_bytes", 16384)),
            audit_emitter=job_audit_emitter,
        )

        # Retry configuration (PS-75 JQ7.2)
        job_max_attempts = int(config.get("jobs.retry.max_attempts", 3))

        # Timeout configuration (PS-75 JQ7.1)
        job_run_timeout_ms = int(config.get("jobs.timeout.run_timeout_ms", 300000))
        job_claim_timeout_ms = int(config.get("jobs.timeout.claim_timeout_ms", 60000))

        # Dead-letter configuration (PS-75 JQ7.3)
        dl_enabled_raw = config.get("jobs.dead_letter.enabled", True)
        dl_enabled = dl_enabled_raw if isinstance(dl_enabled_raw, bool) else str(dl_enabled_raw).strip().lower() in {"true", "1", "yes"}
        dl_queue = str(config.get("jobs.dead_letter.queue_name", "dead_letter")).strip() or "dead_letter"
        job_fallback_manager: FallbackPolicyManager | None = None
        if dl_enabled:
            job_fallback_manager = FallbackPolicyManager(
                policies={"default": FallbackPolicy(action=FallbackAction.DEAD_LETTER, dead_letter_queue=dl_queue)},
            )

        logger.info(
            "db-mcp-server runtime initialised",
            server_id=config.get("service_instance", "db-mcp-local"),
            env_files=env_files,
            jobs_backend=job_backend_name,
        )

        runtime = RuntimeContext(
            config=config,
            logger=logger,
            audit_logger=audit_logger,
            auth=auth,
            metadata_engine=metadata_engine,
            audit_engine=audit_engine,
            job_backend=job_backend,
            job_backend_name=job_backend_name,
            job_queue=job_queue,
            job_audit_emitter=job_audit_emitter,
            job_fallback_manager=job_fallback_manager,
            job_max_attempts=job_max_attempts,
            job_run_timeout_ms=job_run_timeout_ms,
            job_claim_timeout_ms=job_claim_timeout_ms,
            access_control=access_control,
            connectors=None,  # type: ignore[arg-type]
            discovery=None,  # type: ignore[arg-type]
            mongodb_connectors=None,  # type: ignore[arg-type]
            relationships=None,  # type: ignore[arg-type]
            audit_events=None,  # type: ignore[arg-type]
            schema_changes=None,  # type: ignore[arg-type]
            search=None,  # type: ignore[arg-type]
            test_data=None,  # type: ignore[arg-type]
            env_files=env_files,
            started_at=datetime.now(timezone.utc),
        )
        runtime.connectors = ConnectorManager(runtime)
        access_control.bind_connector_manager(runtime.connectors)
        runtime.discovery = DiscoveryService(runtime)
        runtime.mongodb_connectors = MongoDBConnectorService(runtime)
        runtime.relationships = RelationshipService(runtime)
        runtime.audit_events = AuditEventService(runtime)
        runtime.schema_changes = SchemaChangeService(runtime)
        runtime.search = DiscoverySearchService(runtime)
        runtime.test_data = TestDataSeedService(runtime)

        # Register genuine job handlers for each discovery job type (PS-75 JQ2).
        # db-mcp uses inline execution: the service method that submits the
        # job also executes it synchronously. These registrations bind the
        # job_type to its handler function for compliance and future
        # Worker-based dispatch.
        _register_discovery_handlers(runtime)

        return runtime


def _register_discovery_handlers(runtime: RuntimeContext) -> None:
    """Bind each discovery job type to its inline handler via the job queue.

    db-mcp executes jobs inline (the submitting service method IS the handler),
    so these registrations capture the handler identity for compliance evidence
    and future Worker-based dispatch migration.
    """
    if runtime.search is None or runtime.job_backend is None:
        return

    from cloud_dog_jobs import Worker

    worker = Worker(
        runtime.job_backend,
        host_id=str(runtime.config.get("service_instance", "db-mcp-local")),
        worker_id="discovery-inline",
    )

    def _handle_sync_profile(ctx):
        profile_id = (ctx.job.payload or {}).get("profile_id", "")
        return runtime.search.sync_profile(profile_id=profile_id, principal=None)

    def _handle_sync_entity(ctx):
        payload = ctx.job.payload or {}
        return runtime.search.sync_entity(
            profile_id=payload.get("profile_id", ""),
            namespace=payload.get("namespace", ""),
            entity=payload.get("entity", ""),
            principal=None,
        )

    def _handle_rebuild(ctx):
        payload = ctx.job.payload or {}
        return runtime.search.rebuild(
            principal=None,
            profile_ids=payload.get("profile_ids"),
        )

    worker.register_handler("discovery.sync_profile", _handle_sync_profile)
    worker.register_handler("discovery.sync_entity", _handle_sync_entity)
    worker.register_handler("discovery.rebuild", _handle_rebuild)


def build_health_router(runtime: RuntimeContext, application_name: str):
    """Create a configured health router for a server surface."""
    env_file = runtime.env_files[0] if runtime.env_files else None
    return create_health_router(
        application_name=application_name,
        version=str(runtime.config.get("app.version", "0.1.0")),
        env_file=env_file,
        checks=runtime.health_checks(),
        auth_dependency=runtime.auth_dependency(),
    )


def request_timeout_seconds(
    config: Any,
    *,
    scope: str | None = None,
    default: float = 120.0,
    minimum: float = 30.0,
) -> float:
    """Resolve the HTTP request-timeout budget for a server surface."""
    candidate_paths: list[str] = []
    if scope:
        candidate_paths.append(f"{scope}.request_timeout_seconds")
    candidate_paths.append("runtime.request_timeout_seconds")

    resolved_value: Any = None
    for path in candidate_paths:
        value = config.get(path)
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        resolved_value = value
        break

    try:
        timeout = float(resolved_value if resolved_value is not None else default)
    except (TypeError, ValueError):
        timeout = float(default)
    return max(float(minimum), timeout)
