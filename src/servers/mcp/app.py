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

from typing import Any

from cloud_dog_api_kit import create_app
from cloud_dog_api_kit.middleware import TimeoutMiddleware
from cloud_dog_api_kit.mcp.transport import register_mcp_routes
from cloud_dog_api_kit.mcp.tool_router import register_tool_router

from src.common.base_paths import configured_base_path, exempt_paths_for_surface, join_route
from src.common.http import APIKeyAuthMiddleware
from src.common.runtime import RuntimeFactory, build_health_router, request_timeout_seconds
from src.servers.mcp.access_control_tools import build_access_control_tool_registry
from src.servers.mcp.audit_tools import build_audit_tool_registry
from src.servers.mcp.catalog_tools import build_catalog_tool_registry
from src.servers.mcp.content_tools import build_content_tool_registry
from src.servers.mcp.e2e_tools import build_e2e_tool_registry, e2e_tools_enabled
from src.servers.mcp.relationship_tools import build_relationship_tool_registry
from src.servers.mcp.schema_tools import build_schema_tool_registry
from src.servers.mcp.search_tools import build_search_tool_registry
from src.servers.mcp.tool_rbac_audit import (
    TOOL_RBAC_MAP,
    audit_tool_call,
    check_tool_permission,
    wrap_tool_contract,
    wrap_tool_with_audit,
)


def _apply_request_timeout(app, timeout_seconds: float) -> None:
    """Override the platform API-kit timeout budget for this surface."""
    for middleware in app.user_middleware:
        if middleware.cls is TimeoutMiddleware:
            middleware.kwargs["timeout_seconds"] = timeout_seconds
            return


def create_mcp_app(explicit_env_files: list[str] | None = None):
    """Create the db-mcp-server MCP application."""
    runtime = RuntimeFactory.create(explicit_env_files)
    mcp_base_path = configured_base_path(runtime.config, "mcp")
    mcp_messages_path = "/messages"
    timeout_seconds = request_timeout_seconds(runtime.config, scope="mcp_server")
    app = create_app(
        title="db-mcp-server MCP",
        version=str(runtime.config.get("app.version", "0.1.0")),
        api_prefix=mcp_base_path or "",
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
    if e2e_tools_enabled(runtime.env_files):
        tool_registry.update(build_e2e_tool_registry(runtime))
    # TD-001 (W28E-1808B): wrap every MCP tool with full NIST AU-3 audit emission
    # (actor/ip/roles/target/outcome/correlation/session) via the platform AuditLogger.
    tool_registry = {name: wrap_tool_contract(runtime, contract) for name, contract in tool_registry.items()}
    app.include_router(build_health_router(runtime, "db-mcp-server-mcp"))
    if mcp_base_path:
        app.include_router(build_health_router(runtime, "db-mcp-server-mcp"), prefix=mcp_base_path)
    app.add_middleware(
        APIKeyAuthMiddleware,
        verify_api_key=runtime.auth.verify_api_key,
        exempt_paths=exempt_paths_for_surface(mcp_base_path),
        public_mcp_paths={mcp_base_path, mcp_messages_path},
    )
    contracts = register_tool_router(app, tool_registry, base_path=join_route(mcp_base_path, "/tools"))
    register_mcp_routes(
        app,
        contracts,
        transport_modes=list(runtime.config.get("mcp_server.transport_modes", [])),
        transport_base_path=mcp_base_path,
        transport_messages_path=mcp_messages_path,
        session_termination_mode="204_idempotent",
        error_response_mode="jsonrpc_200",
    )

    @app.get("/tools", tags=["mcp"])
    async def legacy_tools_alias() -> dict[str, list[dict[str, Any]]]:
        return {
            "tools": [
                {
                    "name": contract.name,
                    "description": contract.description,
                    "input_schema": contract.input_schema,
                    "output_schema": contract.output_schema,
                }
                for contract in contracts.values()
            ]
        }

    @app.get("/")
    async def root() -> dict[str, object]:
        """Return basic MCP server metadata."""
        return {
            "status": "ok",
            "surface": "mcp",
            "base_path": mcp_base_path,
            "tools": sorted(contracts.keys()),
        }

    return app
