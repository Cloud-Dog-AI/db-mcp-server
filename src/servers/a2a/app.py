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

from fastapi import WebSocket, WebSocketDisconnect

from cloud_dog_api_kit import create_app

from src.common.http import APIKeyAuthMiddleware
from src.common.runtime import RuntimeFactory, build_health_router


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
    app = create_app(
        title="db-mcp-server A2A",
        version=str(runtime.config.get("app.version", "0.1.0")),
        enable_health=False,
    )
    app.include_router(build_health_router(runtime, "db-mcp-server-a2a"))
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

    @app.get("/")
    async def root() -> dict[str, object]:
        """Return basic A2A server metadata."""
        return {"status": "ok", "surface": "a2a", "websocket_path": runtime.config.get("a2a_server.websocket_path")}

    @app.websocket("/a2a/ws")
    async def a2a_socket(websocket: WebSocket) -> None:
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

    return app
