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
# Description: Web server application factory for db-mcp-server.
# Related requirements: W28A-274-A deliverables 1, 2, W28A-274-J deliverables 2, 4
# Related tests: UT1.1, UT1.11, ST1.1, ST1.8

"""Web server application for db-mcp-server."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import httpx
from fastapi import Request, Response
from fastapi.responses import PlainTextResponse

from cloud_dog_api_kit import create_app

from src.common.runtime import RuntimeFactory, build_health_router
from src.servers.web.ui_spa import is_spa_entry_path, serve_runtime_config, serve_spa_asset, serve_spa_index

_HOP_BY_HOP_HEADERS = {
    "connection",
    "content-length",
    "host",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
}


def create_web_app(explicit_env_files: list[str] | None = None):
    """Create the db-mcp-server web application."""
    runtime = RuntimeFactory.create(explicit_env_files)
    app = create_app(
        title="db-mcp-server Web",
        version=str(runtime.config.get("app.version", "0.1.0")),
        enable_health=False,
    )
    app.state.runtime = runtime
    app.include_router(build_health_router(runtime, "db-mcp-server-web"))

    @app.get("/runtime-config.js", response_class=Response)
    async def runtime_config(request: Request) -> Response:
        """Return runtime configuration for the SPA bootstrap contract."""
        return serve_runtime_config(runtime, request)

    @app.api_route("/api", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    @app.api_route("/api/{full_path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    async def proxy_api(request: Request, full_path: str = "") -> Response:
        """Proxy same-origin API requests to the dedicated API server."""
        return await _proxy_request(
            request,
            target_base=_server_base(runtime.config.get("api_server.host", "127.0.0.1"), runtime.config.get("api_server.port", 8086)),
            strip_prefix="",
        )

    @app.api_route("/mcp", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    @app.api_route("/mcp/{full_path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    async def proxy_mcp(request: Request, full_path: str = "") -> Response:
        """Proxy same-origin MCP requests to the dedicated MCP server."""
        return await _proxy_request(
            request,
            target_base=_server_base(runtime.config.get("mcp_server.host", "127.0.0.1"), runtime.config.get("mcp_server.port", 8088)),
            strip_prefix="",
        )

    @app.get("/")
    async def root() -> Response:
        """Serve the SPA entrypoint for the application root."""
        return serve_spa_index(Path.cwd())

    @app.get("/robots.txt")
    async def robots() -> Response:
        """Disable indexing for local admin surfaces."""
        return PlainTextResponse("User-agent: *\nDisallow: /\n")

    @app.get("/{path:path}")
    async def spa(path: str, request: Request) -> Response:
        """Serve static SPA assets and browser-history routes from ui/dist."""
        project_root = Path.cwd()
        cleaned = "/" + path.lstrip("/")
        if is_spa_entry_path(cleaned):
            return serve_spa_index(project_root)
        return serve_spa_asset(project_root, path)

    return app


async def _proxy_request(request: Request, *, target_base: str, strip_prefix: str) -> Response:
    target_path = request.url.path
    if strip_prefix and target_path.startswith(strip_prefix):
        target_path = target_path[len(strip_prefix):] or "/"
    target_url = httpx.URL(target_base.rstrip("/") + target_path).copy_merge_params(request.query_params)
    body = await request.body()
    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in _HOP_BY_HOP_HEADERS
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        proxied = await client.request(
            request.method,
            target_url,
            content=body,
            headers=headers,
        )
    return Response(
        content=proxied.content,
        status_code=proxied.status_code,
        headers=_filtered_response_headers(proxied.headers),
        media_type=proxied.headers.get("content-type"),
    )


def _filtered_response_headers(headers: Iterable[tuple[str, str]] | httpx.Headers) -> dict[str, str]:
    output: dict[str, str] = {}
    items = headers.items() if hasattr(headers, "items") else headers
    for key, value in items:
        if key.lower() in _HOP_BY_HOP_HEADERS:
            continue
        output[key] = value
    return output


def _server_base(host: str | int | None, port: str | int | None) -> str:
    resolved_host = str(host or "127.0.0.1")
    if resolved_host in {"0.0.0.0", "::"}:
        resolved_host = "127.0.0.1"
    return f"http://{resolved_host}:{int(port or 0)}"
