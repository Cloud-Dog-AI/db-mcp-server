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

import secrets
import time
from collections.abc import Iterable

import httpx
from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse, PlainTextResponse, RedirectResponse

from cloud_dog_api_kit import create_app
from cloud_dog_api_kit.middleware import TimeoutMiddleware
from cloud_dog_api_kit.web.proxy import WebApiProxy

from src.common.runtime import RuntimeFactory, build_health_router, request_timeout_seconds
from src.servers.web.ui_spa import is_spa_entry_path, serve_runtime_config, serve_spa_asset, serve_spa_index
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


class _ProxyConfigAdapter:
    """Bridge target-specific values into the WebApiProxy config contract."""

    def __init__(self, *, target_base: str, api_key: str = "") -> None:
        self._values = {
            "web_server.api_base_url": target_base,
            "api_server.base_url": target_base,
            "api_server.api_key": api_key,
            "api_server.api_key_header": "X-API-Key",
            "web_server.verify_tls": False,
            "web_server.proxy_timeout": 60.0,
        }

    def get(self, key: str, default: object = None) -> object:
        return self._values.get(key, default)


def create_web_app(explicit_env_files: list[str] | None = None):
    """Create the db-mcp-server web application."""
    runtime = RuntimeFactory.create(explicit_env_files)
    timeout_seconds = request_timeout_seconds(runtime.config, scope="web_server")
    app = create_app(
        title="db-mcp-server Web",
        version=str(runtime.config.get("app.version", "0.1.0")),
        enable_health=False,
    )
    _apply_request_timeout(app, timeout_seconds)
    app.state.runtime = runtime
    app.include_router(build_health_router(runtime, "db-mcp-server-web"))

    # In-memory token session store (no itsdangerous dependency).
    _sessions: dict[str, dict] = {}
    _admin_username = str(runtime.config.get("web_login.username", "admin") or "admin").strip() or "admin"
    _admin_password = str(runtime.config.get("web_login.password", "") or "")
    _service_api_key = str(runtime.config.get("auth.api_key", "") or "").strip()
    _cookie_name = "db_web_session"
    api_base = _server_base(runtime.config.get("api_server.host"), runtime.config.get("api_server.port"))
    mcp_base = _server_base(runtime.config.get("mcp_server.host"), runtime.config.get("mcp_server.port"))
    a2a_base = _server_base(runtime.config.get("a2a_server.host"), runtime.config.get("a2a_server.port"))
    api_proxy = _build_proxy(api_base)
    api_session_proxy = _build_proxy(api_base, api_key=_service_api_key)

    def _get_session(request: Request) -> dict | None:
        token = request.cookies.get(_cookie_name)
        if token and token in _sessions:
            sess = _sessions[token]
            if time.time() - sess.get("_created", 0) < 3600:
                return sess
            del _sessions[token]
        return None

    @app.post("/auth/login")
    async def auth_login(request: Request) -> JSONResponse:
        body = await request.json()
        username = str(body.get("username", "")).strip()
        password = str(body.get("password", "")).strip()
        if not username or not password:
            raise HTTPException(status_code=400, detail="Username and password required")
        if username != _admin_username or password != _admin_password:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        token = secrets.token_urlsafe(32)
        _sessions[token] = {"user": username, "user_id": "1", "role": "admin", "_created": time.time()}
        resp = JSONResponse({"user": {"id": "1", "displayName": username, "email": None, "roles": ["admin"], "permissions": ["*"]}})
        resp.set_cookie(_cookie_name, token, httponly=True, samesite="lax", max_age=3600, path="/")
        return resp

    @app.get("/auth/me")
    async def auth_me(request: Request) -> JSONResponse:
        sess = _get_session(request)
        if not sess:
            raise HTTPException(status_code=401, detail="Not authenticated")
        return JSONResponse({"user": {"id": sess["user_id"], "displayName": sess["user"], "email": None, "roles": [sess["role"]], "permissions": ["*"]}})

    @app.post("/auth/logout")
    async def auth_logout(request: Request) -> JSONResponse:
        token = request.cookies.get(_cookie_name)
        if token:
            _sessions.pop(token, None)
        resp = JSONResponse({"ok": True})
        resp.delete_cookie(_cookie_name, path="/")
        return resp

    @app.get("/runtime-config.js", response_class=Response)
    async def runtime_config(request: Request) -> Response:
        """Return runtime configuration for the SPA bootstrap contract."""
        return serve_runtime_config(runtime, request)

    @app.api_route("/api", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    @app.api_route("/api/{full_path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    async def proxy_api(request: Request, full_path: str = "") -> Response:
        """Proxy same-origin API requests to the dedicated API server."""
        return await _proxy_via(
            request,
            proxy=api_session_proxy if _get_session(request) else api_proxy,
            strip_prefix="",
        )

    @app.api_route("/webapi", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    @app.api_route("/webapi/{full_path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    async def proxy_web_api(request: Request, full_path: str = "") -> Response:
        """Proxy cookie-authenticated browser API requests on a dedicated path.

        Rewrites /webapi/v1/… → /api/v1/… so the API server receives the
        correct route prefix.
        """
        return await _proxy_via(
            request,
            proxy=api_session_proxy if _get_session(request) else api_proxy,
            strip_prefix="/webapi",
            rewrite_prefix="/api",
        )

    @app.api_route("/webapi-docs", methods=["GET"])
    async def proxy_web_api_docs(request: Request) -> Response:
        """Proxy the API Swagger UI without the /api prefix rewrite."""
        return await _proxy_via(
            request,
            proxy=api_session_proxy if _get_session(request) else api_proxy,
            strip_prefix="/webapi-docs",
            rewrite_prefix="/docs",
        )

    @app.api_route("/webapi-openapi.json", methods=["GET"])
    async def proxy_web_api_openapi(request: Request) -> Response:
        """Proxy the API OpenAPI schema without the /api prefix rewrite."""
        return await _proxy_via(
            request,
            proxy=api_session_proxy if _get_session(request) else api_proxy,
            strip_prefix="/webapi-openapi.json",
            rewrite_prefix="/openapi.json",
        )

    @app.api_route("/mcp", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    @app.api_route("/mcp/{full_path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    async def proxy_mcp(request: Request, full_path: str = "") -> Response:
        """Proxy same-origin MCP requests to the dedicated MCP server."""
        return await _proxy_request(
            request,
            target_base=mcp_base,
            strip_prefix="",
            session_api_key=_service_api_key if _get_session(request) else "",
        )

    @app.api_route("/webmcp", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    @app.api_route("/webmcp/{full_path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    async def proxy_web_mcp(request: Request, full_path: str = "") -> Response:
        """Proxy cookie-authenticated browser MCP requests on a dedicated path.

        Rewrites /webmcp/tools/… → /mcp/tools/… so the MCP server receives the
        correct route prefix.
        """
        return await _proxy_request(
            request,
            target_base=mcp_base,
            strip_prefix="/webmcp",
            rewrite_prefix="/mcp",
            session_api_key=_service_api_key if _get_session(request) else "",
        )

    @app.api_route("/weba2a", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    @app.api_route("/weba2a/{full_path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    async def proxy_web_a2a(request: Request, full_path: str = "") -> Response:
        """Proxy cookie-authenticated browser A2A requests on a dedicated path."""
        return await _proxy_request(
            request,
            target_base=a2a_base,
            strip_prefix="/weba2a",
            session_api_key=_service_api_key if _get_session(request) else "",
        )

    @app.get("/")
    async def root() -> Response:
        """Serve the SPA entrypoint for the application root."""
        return serve_spa_index()

    @app.get("/robots.txt")
    async def robots() -> Response:
        """Disable indexing for local admin surfaces."""
        return PlainTextResponse("User-agent: *\nDisallow: /\n")

    @app.get("/api-docs")
    async def api_docs_spa() -> Response:
        """Serve the SPA shell for the /api-docs route."""
        return serve_spa_index()

    @app.get("/{path:path}")
    async def spa(path: str, request: Request) -> Response:
        """Serve static SPA assets and browser-history routes from ui/dist."""
        cleaned = "/" + path.lstrip("/")
        if is_spa_entry_path(cleaned):
            return serve_spa_index()
        return serve_spa_asset(path)

    return app


def _build_proxy(target_base: str, *, api_key: str = "") -> WebApiProxy:
    """Build a WebApiProxy with explicit target overrides."""
    return WebApiProxy.from_config(_ProxyConfigAdapter(target_base=target_base, api_key=api_key))


async def _proxy_via(
    request: Request,
    *,
    proxy: WebApiProxy,
    strip_prefix: str,
    rewrite_prefix: str = "",
) -> Response:
    """Proxy JSON-capable web requests through the platform WebApiProxy."""
    target_path = request.url.path
    if strip_prefix and target_path.startswith(strip_prefix):
        target_path = target_path[len(strip_prefix):] or "/"
    if rewrite_prefix:
        target_path = rewrite_prefix + target_path

    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in _HOP_BY_HOP_HEADERS
    }
    body = await request.body()
    payload = None
    if body:
        content_type = str(headers.get("content-type") or "").lower()
        if "application/json" in content_type:
            payload = await request.json()
        else:
            return await _proxy_request(
                request,
                target_base=getattr(proxy, "_base_url", ""),
                strip_prefix=strip_prefix,
                rewrite_prefix=rewrite_prefix,
                session_api_key=str(getattr(proxy, "_api_key", "") or ""),
            )

    proxied = await proxy.request(
        request.method,
        target_path,
        json=payload,
        params=dict(request.query_params),
        headers=headers,
        cookies=dict(request.cookies),
    )
    response_headers = _filtered_response_headers(proxied.headers)
    if isinstance(proxied.data, (dict, list)):
        return JSONResponse(
            content=proxied.data,
            status_code=proxied.status_code,
            headers=response_headers,
        )
    content = proxied.data if proxied.data is not None else proxied.error or ""
    return Response(
        content=content,
        status_code=proxied.status_code,
        headers=response_headers,
        media_type=response_headers.get("content-type"),
    )


async def _proxy_request(
    request: Request,
    *,
    target_base: str,
    strip_prefix: str,
    rewrite_prefix: str = "",
    session_api_key: str = "",
) -> Response:
    target_path = request.url.path
    if strip_prefix and target_path.startswith(strip_prefix):
        target_path = target_path[len(strip_prefix):] or "/"
    if rewrite_prefix:
        target_path = rewrite_prefix + target_path
    target_url = httpx.URL(target_base.rstrip("/") + target_path).copy_merge_params(request.query_params)
    body = await request.body()
    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in _HOP_BY_HOP_HEADERS
    }
    lower_headers = {key.lower() for key in headers}
    if session_api_key:
        if "x-api-key" not in lower_headers:
            headers["x-api-key"] = session_api_key
        if "authorization" not in lower_headers:
            headers["authorization"] = f"Bearer {session_api_key}"
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
