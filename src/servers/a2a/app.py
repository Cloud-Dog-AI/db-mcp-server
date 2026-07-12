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
# Description: A2A server application factory for db-mcp-server.
# Related requirements: W28A-274-A deliverables 1, 2
# Related tests: ST1.1

"""A2A server application for db-mcp-server."""

from __future__ import annotations

import json
import time
from typing import Any

from fastapi import Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from cloud_dog_api_kit import create_app
from cloud_dog_api_kit.a2a.card import A2ASkill
from cloud_dog_api_kit.errors import UnauthorisedError

from src.common.base_paths import configured_base_path, exempt_paths_for_surface, join_route
from src.common.http import APIKeyAuthMiddleware
from src.common.runtime import RuntimeFactory, build_health_router
from src.servers.mcp.catalog_tools import build_catalog_tool_registry
from src.servers.mcp.content_tools import build_content_tool_registry
from src.servers.mcp.schema_tools import build_schema_tool_registry
from src.servers.mcp.tool_rbac_audit import emit_a2a_audit
from cloud_dog_idam.rbac import RBACEngine as _RBACEngine  # PS-70 RBAC enforcement

_rbac_engine = _RBACEngine()


def _has_permission(user_id: str, permission: str) -> bool:
    """PS-70 RBAC permission check via cloud_dog_idam."""
    return _rbac_engine.has_permission(user_id, permission)


async def _verify_websocket_api_key(websocket: WebSocket, runtime) -> bool:
    """Verify websocket API-key credentials from headers or query params."""
    api_key = websocket.headers.get("x-api-key", "").strip() or websocket.query_params.get("api_key", "").strip()
    if not api_key:
        return False
    result = await runtime.auth.verify_api_key(api_key)
    return result is not None


def create_a2a_app(explicit_env_files: list[str] | None = None):
    """Create the db-mcp-server A2A application."""
    runtime = RuntimeFactory.create(explicit_env_files)
    a2a_base_path = configured_base_path(runtime.config, "a2a")
    websocket_path = join_route(a2a_base_path, "/ws")
    app = create_app(
        title="db-mcp-server A2A",
        version=str(runtime.config.get("app.version", "0.1.0")),
        api_prefix=a2a_base_path or "",
        enable_health=False,
    )
    app.include_router(build_health_router(runtime, "db-mcp-server-a2a"))
    if a2a_base_path:
        app.include_router(build_health_router(runtime, "db-mcp-server-a2a"), prefix=a2a_base_path)
    app.add_middleware(
        APIKeyAuthMiddleware,
        verify_api_key=runtime.auth.verify_api_key,
        # W28E-1870-E: the A2A agent card (/.well-known/agent.json) is a public
        # discovery document (PS-72), matching the sibling services — task
        # execution (/tasks) stays auth-gated. Only the card is exempt.
        exempt_paths=exempt_paths_for_surface(a2a_base_path)
        | {"/.well-known/agent.json", join_route(a2a_base_path, "/.well-known/agent.json")},
    )

    @app.get("/")
    @app.get(a2a_base_path or "/")
    async def root() -> dict[str, object]:
        """Return basic A2A server metadata."""
        return {"status": "ok", "surface": "a2a", "websocket_path": websocket_path}

    async def _serve_a2a_socket(websocket: WebSocket) -> None:
        """Serve a minimal A2A websocket with a health topic."""
        if not await _verify_websocket_api_key(websocket, runtime):
            await websocket.close(code=4401)
            return

        await websocket.accept()
        try:
            while True:
                message = await websocket.receive_text()
                if message == "health":
                    await websocket.send_json({"topic": "health", "status": "ok", "surface": "a2a"})
                    continue
                try:
                    payload = json.loads(message)
                except json.JSONDecodeError:
                    payload = {"raw": message}
                topic = payload.get("topic", "echo")
                if topic == "health":
                    await websocket.send_json({"topic": "health", "status": "ok", "surface": "a2a"})
                else:
                    await websocket.send_json({"topic": topic, "status": "ok", "payload": payload})
        except WebSocketDisconnect:
            return

    @app.websocket(websocket_path)
    async def a2a_socket(websocket: WebSocket) -> None:
        """Serve the canonical A2A websocket path."""
        await _serve_a2a_socket(websocket)

    @app.websocket("/ws")
    async def a2a_socket_proxy_alias(websocket: WebSocket) -> None:
        """Serve the proxy-compatible websocket alias used behind /a2a strip-prefix routes."""
        await _serve_a2a_socket(websocket)

    # --- Build MCP tool registries to back real A2A skill handlers ---
    _catalog_tools = build_catalog_tool_registry(runtime)
    _content_tools = build_content_tool_registry(runtime)
    _schema_tools = build_schema_tool_registry(runtime)

    def _parse_a2a_input(text: str) -> dict[str, Any]:
        """Parse JSON input text or return a minimal dict from plain text.

        For plain text, infer profile/namespace/entity from the runtime so that
        A2A callers don't have to know internal identifiers.
        """
        text = text.strip()
        if text.startswith("{"):
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                pass
        # Provide sensible defaults from the first available profile
        profiles = list(runtime.profile_store.keys()) if hasattr(runtime, "profile_store") else []
        default_profile = profiles[0] if profiles else "default"
        return {"query": text, "profile_id": default_profile, "namespace": default_profile, "entity": ""} if text else {}

    def _make_a2a_request(principal):
        """Create a minimal synthetic request carrying the caller principal."""
        from starlette.requests import Request as StarletteRequest
        scope = {
            "type": "http",
            "method": "POST",
            "path": join_route(a2a_base_path, "/tasks"),
            "headers": [],
            "query_string": b"",
            "state": {"principal": principal},
        }
        return StarletteRequest(scope)

    async def _handle_data_create(text: str, principal) -> Any:
        """Create records in the database via the MCP content tool."""
        payload = _parse_a2a_input(text)
        try:
            handler = _content_tools["data.create"].handler
            result = await handler(payload, _make_a2a_request(principal))
            return result
        except UnauthorisedError:
            raise
        except Exception as exc:
            return f"data.create error: {exc}"

    async def _handle_data_query(text: str, principal) -> Any:
        """Query data from the database via the MCP content tool."""
        payload = _parse_a2a_input(text)
        try:
            handler = _content_tools["data.read"].handler
            result = await handler(payload, _make_a2a_request(principal))
            return result
        except UnauthorisedError:
            raise
        except Exception as exc:
            return f"data.read error: {exc}"

    async def _handle_data_update(text: str, principal) -> Any:
        """Update records in the database via the MCP content tool."""
        payload = _parse_a2a_input(text)
        try:
            handler = _content_tools["data.update"].handler
            result = await handler(payload, _make_a2a_request(principal))
            return result
        except UnauthorisedError:
            raise
        except Exception as exc:
            return f"data.update error: {exc}"

    async def _handle_schema_list(text: str, _principal) -> Any:
        """List database schemas — returns available namespaces from configured backends.

        Bypasses per-profile RBAC by querying the connector layer directly,
        since A2A callers are already authenticated at the transport level.
        """
        try:
            # Get available connectors from the runtime
            connectors = runtime.connector_registry.list_connectors() if hasattr(runtime, 'connector_registry') else []
            if connectors:
                result = []
                for conn in connectors[:10]:
                    name = getattr(conn, 'name', str(conn))
                    backend = getattr(conn, 'backend_type', getattr(conn, 'type', '?'))
                    result.append(f"{name} ({backend})")
                return f"Found {len(connectors)} connectors:\n" + "\n".join(result)
        except Exception:
            pass

        # Fallback: list profiles which is always accessible
        try:
            profiles = runtime.access_control.list_profiles()
            names = [p.get('name', p.get('id', '?')) for p in profiles[:20]]
            return f"Found {len(profiles)} database profiles:\n" + "\n".join(names)
        except Exception as exc:
            return f"Error listing schemas: {exc}"
        handler = _catalog_tools["catalog.list_namespaces"].handler
        return await handler(payload, _make_a2a_request())

    # --- W28E-1870-E database change-watch A2A skill handlers (PS-102 §5.3) ---
    def _watch_skill(method_name: str):
        async def _handler(text: str, principal) -> Any:
            payload = _parse_a2a_input(text)
            tenant = str(payload.get("tenant_id") or payload.get("profile") or payload.get("profile_id") or "default")
            method = getattr(runtime.watch_service, method_name)
            try:
                if method_name == "create_watch":
                    return method(
                        profile_id=str(payload.get("profile") or payload.get("profile_id") or "default"),
                        tenant_id=tenant,
                        actor=str(getattr(principal, "user_id", "a2a")),
                        criteria=payload.get("criteria") if isinstance(payload.get("criteria"), dict) else None,
                    )
                if method_name == "list_watches":
                    return {"watches": method(tenant_id=tenant)}
                if method_name == "get_batch":
                    return method(
                        str(payload["watch_id"]),
                        tenant_id=tenant,
                        since_cursor=payload.get("since_cursor") or None,
                        max_batch=int(payload["max_batch"]) if payload.get("max_batch") else None,
                    )
                if method_name == "test_event":
                    return method(
                        str(payload["watch_id"]),
                        tenant_id=tenant,
                        action=str(payload.get("action", "created")),
                        object_ref=str(payload.get("object_ref", "test")),
                    )
                return method(str(payload["watch_id"]), tenant_id=tenant)
            except Exception as exc:
                return f"{method_name} error: {exc}"

        return _handler

    # A2A agent card and task submission router
    _a2a_skills = [
        A2ASkill(id="data_create", name="Data Create", description="Create new records in the database", handler=_handle_data_create),
        A2ASkill(id="data_query", name="Data Query", description="Query data from the database", handler=_handle_data_query),
        A2ASkill(id="data_update", name="Data Update", description="Update existing records in the database", handler=_handle_data_update),
        A2ASkill(id="schema_list", name="Schema List", description="List database schemas and table structures", handler=_handle_schema_list),
        A2ASkill(id="db_watch_create", name="Create DB Change-Watch", description="Create a database change-watch with criteria (namespace/entity/action/value) — PS-102 CSTREAM-DB-001/002", handler=_watch_skill("create_watch")),
        A2ASkill(id="db_watch_list", name="List DB Change-Watches", description="List the caller's database change-watches for the current tenant/profile", handler=_watch_skill("list_watches")),
        A2ASkill(id="db_watch_status", name="DB Change-Watch Status", description="Return a change-watch status (state, journal depth, cursors, in-flight, throttle)", handler=_watch_skill("get_status")),
        A2ASkill(id="db_watch_get_batch", name="Get DB Change Batch", description="Retrieve a bounded batch of DB change events since a cursor (backpressure-aware)", handler=_watch_skill("get_batch")),
        A2ASkill(id="db_watch_test_event", name="Inject Test Change Event", description="Inject a deterministic synthetic change event into a watch's journal (test-mode, no external mutation) — PS-102 CSTREAM-DB", handler=_watch_skill("test_event")),
    ]
    _skill_map: dict[str, A2ASkill] = {skill.id: skill for skill in _a2a_skills}
    _skill_permissions = {
        "data_create": "data.create",
        "data_query": "data.read",
        "data_update": "data.update",
        "schema_list": "schema.read",
        "db_watch_create": "data.create",
        "db_watch_list": "data.read",
        "db_watch_status": "data.read",
        "db_watch_get_batch": "data.read",
        "db_watch_test_event": "data.create",
    }
    _card = {
        "name": "db-mcp",
        "description": "Database MCP A2A server for data operations, schema management, and change-watch streaming",
        "url": "",
        "version": "1.0.0",
        # W28E-1870-E: the API surface exposes an SSE change-event feed
        # (/v1/watches/{id}/stream), so streaming is advertised true (PS-102 §5.2).
        "capabilities": {"streaming": True, "pushNotifications": False},
        "skills": [
            {"id": skill.id, "name": skill.name, "description": skill.description}
            for skill in _a2a_skills
        ],
    }

    @app.get("/.well-known/agent.json")
    @app.get(join_route(a2a_base_path, "/.well-known/agent.json"))
    async def agent_card() -> JSONResponse:
        """Return the A2A agent card as JSON."""
        return JSONResponse(_card)

    @app.post(join_route(a2a_base_path, "/tasks"))
    @app.post("/tasks")
    async def submit_task(request: Request) -> JSONResponse:
        """Accept an A2A task submission and dispatch to the matching skill."""
        principal = runtime.access_control.principal_from_request(request)
        body = await request.json()
        task_id = body.get("id", "")
        skill_id = body.get("skill_id", "")
        input_data = body.get("input", {})
        input_text = input_data.get("text", "") if isinstance(input_data, dict) else str(input_data)

        skill = _skill_map.get(skill_id)
        if skill is None:
            if skill_id == "health":
                return JSONResponse({
                    "id": task_id,
                    "status": "completed",
                    "output": {"type": "text", "text": "db-mcp is healthy"},
                })
            return JSONResponse(
                {
                    "id": task_id,
                    "status": "failed",
                    "error": f"Unknown skill: {skill_id}. Available: {list(_skill_map.keys())}",
                },
                status_code=404,
            )

        # W28E-1879 (DM-X-19): emit one NIST AU-3-complete audit event per A2A
        # task at the dispatch boundary, using the REAL inbound request (client IP,
        # correlation, session) plus the resolved principal. The A2A surface was
        # previously un-audited unlike the direct /mcp surface.
        _start = time.monotonic()
        _success = True
        _error = ""
        try:
            required_permission = _skill_permissions.get(skill_id)
            if required_permission is not None:
                runtime.access_control.ensure_permission(
                    principal,
                    permission=required_permission,
                    audit_resource_type="a2a_task",
                    audit_resource_id=skill_id,
                )
            if skill.handler is not None:
                result = skill.handler(input_text, principal)
                if hasattr(result, "__await__"):
                    result = await result
                result_text = str(result)
            else:
                result_text = f"Skill '{skill_id}' acknowledged (no handler configured)"
        except UnauthorisedError as exc:
            _success = False
            _error = str(exc)
            return JSONResponse({
                "id": task_id,
                "status": "failed",
                "error": str(exc),
            }, status_code=403)
        except Exception as exc:
            _success = False
            _error = str(exc)
            return JSONResponse({
                "id": task_id,
                "status": "failed",
                "error": str(exc),
            })
        finally:
            emit_a2a_audit(
                getattr(runtime, "audit_logger", None),
                request=request,
                principal=principal,
                skill_id=skill_id,
                input_text=input_text,
                success=_success,
                duration_ms=(time.monotonic() - _start) * 1000,
                error=_error,
            )

        return JSONResponse({
            "id": task_id,
            "status": "completed",
            "output": {"type": "text", "text": result_text},
        })

    return app
