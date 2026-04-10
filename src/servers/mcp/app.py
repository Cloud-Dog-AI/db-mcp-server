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
# Description: MCP server application factory for db-mcp-server.
# Related requirements: W28A-274-A deliverables 1, 2, AC-01, AC-02, AC-03, CD-02, SC-01, CO-01, RL-01, W28A-274-I deliverables 3, 4
# Related tests: ST1.1, ST1.2, ST1.4, ST1.5, ST1.6, ST1.7, IT1.1, IT1.3, IT1.4, IT1.5, IT1.6

"""MCP server application for db-mcp-server."""

from __future__ import annotations

from cloud_dog_api_kit import create_app, register_mcp_contract
from cloud_dog_api_kit.middleware import TimeoutMiddleware

from src.common.http import APIKeyAuthMiddleware
from src.common.runtime import RuntimeFactory, build_health_router, request_timeout_seconds
from src.servers.mcp.access_control_tools import build_access_control_tool_registry
from src.servers.mcp.audit_tools import build_audit_tool_registry
from src.servers.mcp.catalog_tools import build_catalog_tool_registry
from src.servers.mcp.content_tools import build_content_tool_registry
from src.servers.mcp.relationship_tools import build_relationship_tool_registry
from src.servers.mcp.schema_tools import build_schema_tool_registry
from src.servers.mcp.search_tools import build_search_tool_registry
from src.servers.mcp.tool_rbac_audit import TOOL_RBAC_MAP, audit_tool_call, check_tool_permission, wrap_tool_with_audit
from cloud_dog_idam.rbac import RBACEngine as _RBACEngine  # PS-70 RBAC enforcement

_rbac_engine = _RBACEngine()


def _has_permission(user_id: str, permission: str) -> bool:
    """PS-70 RBAC permission check via cloud_dog_idam."""
    return _rbac_engine.has_permission(user_id, permission)


def _apply_request_timeout(app, timeout_seconds: float) -> None:
    """Override the platform API-kit timeout budget for this surface."""
    for middleware in app.user_middleware:
        if middleware.cls is TimeoutMiddleware:
            middleware.kwargs["timeout_seconds"] = timeout_seconds
            return


def create_mcp_app(explicit_env_files: list[str] | None = None):
    """Create the db-mcp-server MCP application."""
    runtime = RuntimeFactory.create(explicit_env_files)
    timeout_seconds = request_timeout_seconds(runtime.config, scope="mcp_server")
    app = create_app(
        title="db-mcp-server MCP",
        version=str(runtime.config.get("app.version", "0.1.0")),
        enable_health=False,
    )
    _apply_request_timeout(app, timeout_seconds)
    app.state.runtime = runtime
    tool_registry = {}
    tool_registry.update(build_access_control_tool_registry(runtime))
    tool_registry.update(build_catalog_tool_registry(runtime))
    tool_registry.update(build_schema_tool_registry(runtime))
    tool_registry.update(build_content_tool_registry(runtime))
    tool_registry.update(build_relationship_tool_registry(runtime))
    tool_registry.update(build_audit_tool_registry(runtime))
    tool_registry.update(build_search_tool_registry(runtime))
    app.include_router(build_health_router(runtime, "db-mcp-server-mcp"))
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
    register_mcp_contract(
        app,
        tool_registry=tool_registry,
        transport_modes=list(runtime.config.get("mcp_server.transport_modes", [])),
        include_legacy_tools_alias=True,
    )

    @app.get("/")
    async def root() -> dict[str, object]:
        """Return basic MCP server metadata."""
        return {
            "status": "ok",
            "surface": "mcp",
            "tools": sorted(tool_registry.keys()),
        }

    return app
