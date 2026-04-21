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

import inspect
import json
from typing import Any, Awaitable, Callable

from fastapi import FastAPI, Request
from starlette.responses import JSONResponse, Response, StreamingResponse

from cloud_dog_api_kit import create_app
from cloud_dog_api_kit.envelopes import error_envelope, success_envelope
from cloud_dog_api_kit.middleware import TimeoutMiddleware
from cloud_dog_api_kit.mcp.error_mapper import map_legacy_mcp_payload
from cloud_dog_api_kit.mcp.session import SESSION_HEADER, McpSessionManager
from cloud_dog_api_kit.mcp.tool_router import ToolContract, register_tool_router

from src.common.base_paths import configured_base_path, exempt_paths_for_surface, join_route
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
SUPPORTED_TRANSPORT_MODES = frozenset({"streamable_http", "http_jsonrpc", "legacy_sse", "stdio"})
ToolCallable = Callable[[dict[str, Any], Request], Awaitable[Any] | Any]


def _has_permission(user_id: str, permission: str) -> bool:
    """PS-70 RBAC permission check via cloud_dog_idam."""
    return _rbac_engine.has_permission(user_id, permission)


def _apply_request_timeout(app, timeout_seconds: float) -> None:
    """Override the platform API-kit timeout budget for this surface."""
    for middleware in app.user_middleware:
        if middleware.cls is TimeoutMiddleware:
            middleware.kwargs["timeout_seconds"] = timeout_seconds
            return


def _normalise_transport_modes(transport_modes: list[str] | set[str] | tuple[str, ...] | None) -> set[str]:
    modes = set(transport_modes or SUPPORTED_TRANSPORT_MODES)
    unknown = modes - SUPPORTED_TRANSPORT_MODES
    if unknown:
        unknown_str = ", ".join(sorted(unknown))
        raise ValueError(f"Unsupported transport mode(s): {unknown_str}")
    return modes


async def _call_tool(tool: ToolContract, payload: dict[str, Any], request: Request) -> Any:
    parameter_count = len(inspect.signature(tool.handler).parameters)
    if parameter_count <= 1:
        result = tool.handler(payload)  # type: ignore[call-arg]
    else:
        result = tool.handler(payload, request)
    if inspect.isawaitable(result):
        return await result
    return result


async def _dispatch_payload(
    tools: dict[str, ToolContract],
    payload: dict[str, Any],
    request: Request,
) -> tuple[int, dict[str, Any]]:
    request_id = getattr(request.state, "request_id", "")
    correlation_id = getattr(request.state, "correlation_id", None)

    if payload.get("jsonrpc") == "2.0":
        method = str(payload.get("method", ""))
        params = dict(payload.get("params") or {})
        if method == "tools/list":
            result = success_envelope(
                data=[
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.input_schema,
                        "output_schema": tool.output_schema,
                    }
                    for tool in tools.values()
                ],
                request_id=request_id,
                correlation_id=correlation_id,
            )
            return 200, result
        if method != "tools/call":
            return (
                400,
                error_envelope(
                    code="INVALID_REQUEST",
                    message=f"Unsupported JSON-RPC method: {method}",
                    request_id=request_id,
                    correlation_id=correlation_id,
                ),
            )
        tool_name = str(params.get("name", ""))
        arguments = dict(params.get("arguments") or {})
    else:
        tool_name = str(payload.get("tool", payload.get("name", "")))
        arguments = dict(payload.get("arguments") or payload.get("input") or {})

    tool = tools.get(tool_name)
    if tool is None:
        return (
            404,
            error_envelope(
                code="NOT_FOUND",
                message=f"Unknown MCP tool: {tool_name}",
                request_id=request_id,
                correlation_id=correlation_id,
            ),
        )

    result = await _call_tool(tool, arguments, request)
    mapped = map_legacy_mcp_payload(result, request_id=request_id, correlation_id=correlation_id)
    status = 200 if mapped.get("ok", True) else 400
    return status, mapped


def _register_configurable_mcp_routes(
    app: FastAPI,
    tools: dict[str, ToolContract],
    *,
    transport_modes: list[str] | set[str] | tuple[str, ...] | None,
    mcp_path: str,
) -> McpSessionManager:
    enabled_modes = _normalise_transport_modes(transport_modes)
    manager = McpSessionManager()

    app.state.mcp_transport_modes = sorted(enabled_modes)
    app.state.mcp_session_manager = manager

    async def _handle_mcp(request: Request) -> JSONResponse:
        try:
            payload = await request.json()
            if not isinstance(payload, dict):
                payload = {}
        except Exception:
            payload = {}

        existing_session_id = request.headers.get(SESSION_HEADER)
        session, created = manager.ensure(existing_session_id)
        status, body = await _dispatch_payload(tools, payload, request)
        response = JSONResponse(status_code=status, content=body)
        response.headers[SESSION_HEADER] = session.session_id
        response.headers["X-Mcp-Session-Created"] = "true" if created else "false"
        return response

    @app.post(mcp_path, tags=["mcp"])
    async def mcp_transport(request: Request) -> JSONResponse:
        return await _handle_mcp(request)

    @app.post("/messages", tags=["mcp"])
    async def mcp_messages(request: Request) -> JSONResponse:
        return await _handle_mcp(request)

    @app.get(mcp_path, tags=["mcp"], response_model=None)
    async def mcp_legacy_sse() -> Response:
        if "legacy_sse" not in enabled_modes:
            return JSONResponse(status_code=404, content=error_envelope(code="NOT_FOUND", message="Route not enabled"))

        async def _event_stream() -> Any:
            payload = {
                "type": "ready",
                "modes": sorted(enabled_modes),
                "tools": sorted(tools.keys()),
            }
            yield f"event: ready\ndata: {json.dumps(payload)}\n\n"

        return StreamingResponse(_event_stream(), media_type="text/event-stream")

    return manager


def create_mcp_app(explicit_env_files: list[str] | None = None):
    """Create the db-mcp-server MCP application."""
    runtime = RuntimeFactory.create(explicit_env_files)
    mcp_base_path = configured_base_path(runtime.config, "mcp")
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
    app.include_router(build_health_router(runtime, "db-mcp-server-mcp"))
    if mcp_base_path:
        app.include_router(build_health_router(runtime, "db-mcp-server-mcp"), prefix=mcp_base_path)
    app.add_middleware(
        APIKeyAuthMiddleware,
        verify_api_key=runtime.auth.verify_api_key,
        exempt_paths=exempt_paths_for_surface(mcp_base_path),
        public_mcp_paths={mcp_base_path, "/messages"},
    )
    contracts = register_tool_router(app, tool_registry, base_path=join_route(mcp_base_path, "/tools"))
    _register_configurable_mcp_routes(
        app,
        contracts,
        transport_modes=list(runtime.config.get("mcp_server.transport_modes", [])),
        mcp_path=mcp_base_path,
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
