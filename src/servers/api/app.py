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

from fastapi import APIRouter

from cloud_dog_api_kit import create_app, success_envelope

from src.common.http import APIKeyAuthMiddleware
from src.common.runtime import RuntimeFactory, build_health_router
from src.servers.api.access_control import create_access_control_router


def create_api_app(explicit_env_files: list[str] | None = None):
    """Create the db-mcp-server API application."""
    runtime = RuntimeFactory.create(explicit_env_files)
    app = create_app(
        title="db-mcp-server API",
        version=str(runtime.config.get("app.version", "0.1.0")),
        enable_health=False,
        cors_origins=list(runtime.config.get("api_server.cors_origins", [])),
    )
    app.state.runtime = runtime
    app.include_router(build_health_router(runtime, "db-mcp-server-api"))
    app.add_middleware(
        APIKeyAuthMiddleware,
        verify_api_key=runtime.auth.verify_api_key,
        exempt_paths={
            "/health",
            "/ready",
            "/live",
            "/status",
            "/docs",
            "/redoc",
            "/openapi.json",
        },
    )

    router = APIRouter(prefix="/api/v1", tags=["api"])

    @router.get("/ping")
    async def ping() -> dict:
        """Return a minimal authenticated runtime summary."""
        return success_envelope(
            {
                "service": "db-mcp-server",
                "surface": "api",
                "jobs_backend": "memory",
                "metadata_store": str(runtime.config.get("metadata_store.uri")),
            }
        )

    @router.get("/jobs/health")
    async def jobs_health() -> dict:
        """Return queue health and current queue counters."""
        return success_envelope(
            {
                "ok": runtime.job_queue.health(),
                "queue_status": runtime.job_backend.get_queue_status(),
            }
        )

    app.include_router(router)
    app.include_router(create_access_control_router(runtime))
    return app
