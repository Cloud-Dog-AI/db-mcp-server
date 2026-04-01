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
from pathlib import Path
from typing import Any, Callable

from sqlalchemy import Engine

from cloud_dog_api_kit.auth import create_auth_dependency
from cloud_dog_api_kit.routers.health import create_health_router
from cloud_dog_db import DatabaseSettings, build_sync_engine, probe_database
from cloud_dog_jobs import JobQueue, SQLQueueBackend
from cloud_dog_logging import get_audit_logger, get_logger, setup_logging

from src.common.auth import APIKeyAuthoriser
from src.common.config_loader import load_runtime_config
from src.common.env_loader import resolve_env_files
from src.core.audit import AuditEventService
from src.core.access_control.service import AccessControlService
from src.core.connectors.service import ConnectorManager
from src.core.connectors.mongodb import MongoDBConnectorService
from src.core.relationships import RelationshipService
from src.core.schema import SchemaChangeService
from src.core.search import DiscoverySearchService


@dataclass(slots=True)
class RuntimeContext:
    """Resolved runtime objects shared by the four server surfaces."""

    config: Any
    logger: Any
    audit_logger: Any
    auth: APIKeyAuthoriser
    metadata_engine: Engine
    audit_engine: Engine
    job_backend: Any
    job_backend_name: str
    job_queue: JobQueue
    access_control: AccessControlService
    connectors: ConnectorManager
    mongodb_connectors: MongoDBConnectorService
    relationships: RelationshipService
    audit_events: AuditEventService
    schema_changes: SchemaChangeService
    search: DiscoverySearchService
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

        Path("logs").mkdir(parents=True, exist_ok=True)
        Path("data").mkdir(parents=True, exist_ok=True)

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
        auth = APIKeyAuthoriser(access_control)
        job_database_url = str(
            config.get("jobs.sql_database_url") or config.get("metadata_store.uri") or ""
        ).strip()
        if not job_database_url:
            raise RuntimeError("Missing required configuration: jobs.sql_database_url or metadata_store.uri")

        job_backend = SQLQueueBackend(database_url=job_database_url)
        job_backend_name = "sql"
        job_queue = JobQueue(
            job_backend,
            payload_max_bytes=int(config.get("jobs.payload_max_bytes", 16384)),
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
            access_control=access_control,
            connectors=None,  # type: ignore[arg-type]
            mongodb_connectors=None,  # type: ignore[arg-type]
            relationships=None,  # type: ignore[arg-type]
            audit_events=None,  # type: ignore[arg-type]
            schema_changes=None,  # type: ignore[arg-type]
            search=None,  # type: ignore[arg-type]
            env_files=env_files,
            started_at=datetime.now(timezone.utc),
        )
        runtime.connectors = ConnectorManager(runtime)
        runtime.mongodb_connectors = MongoDBConnectorService(runtime)
        runtime.relationships = RelationshipService(runtime)
        runtime.audit_events = AuditEventService(runtime)
        runtime.schema_changes = SchemaChangeService(runtime)
        runtime.search = DiscoverySearchService(runtime)
        return runtime


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
