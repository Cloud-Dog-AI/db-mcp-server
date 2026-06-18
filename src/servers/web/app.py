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
from pathlib import Path

import httpx
from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse, PlainTextResponse, RedirectResponse
from starlette.requests import ClientDisconnect

from cloud_dog_api_kit import create_app
from cloud_dog_api_kit.middleware import TimeoutMiddleware
from cloud_dog_api_kit.web.proxy import WebApiProxy

from src.common.base_paths import configured_base_path, join_route
from src.common.runtime import RuntimeFactory, build_health_router, request_timeout_seconds
from src.servers.web.ui_spa import is_spa_entry_path, serve_runtime_config, serve_spa_asset, serve_spa_index
from cloud_dog_idam.rbac import RBACEngine as _RBACEngine  # PS-70 RBAC enforcement

_rbac_engine = _RBACEngine()

# W28A-732-R5 (login-contract reopen): platform flat WebUI roles.
_WRITE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
_ADMIN_ROLE = "admin"
_READ_WRITE_ROLE = "read-write"
_READ_ONLY_ROLE = "read-only"
_WEBUI_LEGACY_REDIRECTS = {
    "/ui/login": "/login",
    "/auth/login": "/login",
    "/audit": "/audit-log",
    "/diagnostics-audit": "/audit-log",
    "/observability": "/audit-log",
    "/logs": "/audit-log",
    "/idam/users": "/admin/users",
    "/idam/groups": "/admin/groups",
    "/idam/api-keys": "/admin/api-keys",
    "/apikeys": "/admin/api-keys",
    "/api-keys": "/admin/api-keys",
    "/idam/roles": "/admin/roles",
    "/idam/rbac": "/admin/rbac",
    "/rbac": "/admin/rbac",
    "/api-docs": "/developer/api-docs",
    "/docs": "/developer/api-docs",
    "/openapi": "/developer/api-docs",
    "/redoc": "/developer/api-docs",
    "/mcp-console": "/developer/mcp-console",
    "/a2a-console": "/developer/a2a-console",
    "/jobs": "/system/jobs",
    "/settings": "/system/settings",
    "/about": "/system/about",
}


def _role_can_write(role: str | None) -> bool:
    """Flat-role write capability: admin and read-write may mutate; read-only may not."""
    return str(role or "").strip().lower() in {_ADMIN_ROLE, _READ_WRITE_ROLE}


def _has_permission(user_id: str, permission: str) -> bool:
    """PS-70 RBAC permission check via cloud_dog_idam."""
    return _rbac_engine.has_permission(user_id, permission)


def _apply_request_timeout(app, timeout_seconds: float) -> None:
    """Override the platform API-kit timeout budget for this surface."""
    for middleware in app.user_middleware:
        if middleware.cls is TimeoutMiddleware:
            middleware.kwargs["timeout_seconds"] = timeout_seconds
            return


def _webui_redirect(request: Request, target_path: str) -> RedirectResponse:
    """Return a canonical WebUI redirect while preserving the query string."""
    location = target_path
    if request.url.query:
        location = f"{location}?{request.url.query}"
    return RedirectResponse(location, status_code=308)

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
    web_base_path = configured_base_path(runtime.config, "web")
    api_base_path = configured_base_path(runtime.config, "api")
    mcp_base_path = configured_base_path(runtime.config, "mcp")
    a2a_base_path = configured_base_path(runtime.config, "a2a")
    # Traefik strips /api before forwarding to the API server, so
    # api_base_path is already the post-strip prefix (e.g. "/v1").
    # The webapi proxy strips /webapi, leaving e.g. /v1/users which
    # matches the API server directly — no rewrite needed.
    api_alias_rewrite_prefix = ""
    timeout_seconds = request_timeout_seconds(runtime.config, scope="web_server")
    app = create_app(
        title="db-mcp-server Web",
        version=str(runtime.config.get("app.version", "0.1.0")),
        api_prefix=web_base_path or "",
        enable_docs=False,
        enable_health=False,
    )
    _apply_request_timeout(app, timeout_seconds)
    app.state.runtime = runtime
    app.include_router(build_health_router(runtime, "db-mcp-server-web"))
    if web_base_path:
        app.include_router(build_health_router(runtime, "db-mcp-server-web"), prefix=web_base_path)

    # In-memory token session store (no itsdangerous dependency).
    _sessions: dict[str, dict] = {}
    _admin_username = str(runtime.config.get("web_login.username", "admin") or "admin").strip() or "admin"
    _admin_password = str(runtime.config.get("web_login.password", "") or "")
    _service_api_key = str(runtime.config.get("auth.api_key", "") or "").strip()

    # W28A-732-R5 (login-contract reopen): the platform flat WebUI login contract —
    # three username/password roles admin / read-write / read-only. admin keeps its
    # Vault/TF-env credential (CLOUD_DOG_WEB_LOGIN_*); read-write/read-only carry the
    # estate-canonical in-code demo defaults (BlueRiverChair / GreenRiverDesk) —
    # mirroring git-mcp (W28A-731-R5), chat-client (727) and notification-agent (730) —
    # so all three flat roles log in out-of-the-box without a Terraform/Vault write.
    _rw_username = str(runtime.config.get("web_login.read_write_username", "read-write") or "read-write").strip() or "read-write"
    _rw_password = str(runtime.config.get("web_login.read_write_password", "") or "").strip() or "BlueRiverChair"
    _ro_username = str(runtime.config.get("web_login.read_only_username", "read-only") or "read-only").strip() or "read-only"
    _ro_password = str(runtime.config.get("web_login.read_only_password", "") or "").strip() or "GreenRiverDesk"
    # username -> (password, flat-role, forwarded-IDAM-principal). The forwarded
    # principal is the seeded IDAM user (src/core/access_control FLAT_DEMO_ROLES) whose
    # OWN RBAC the API tier resolves (W28A-889-B-R2) — so read-only data writes are
    # denied at the API tier natively, and read-write/admin are authorised to mutate.
    # All three bind to the seeded flat-* principals (flat-admin/flat-read-write/
    # flat-read-only): unlike the bootstrap-admin user, every flat-* user is enrolled
    # in the repository by username, so principal_for_username resolves it.
    _flat_accounts: dict[str, tuple[str, str, str]] = {
        _admin_username: (_admin_password, _ADMIN_ROLE, "flat-admin"),
        _rw_username: (_rw_password, _READ_WRITE_ROLE, "flat-read-write"),
        _ro_username: (_ro_password, _READ_ONLY_ROLE, "flat-read-only"),
    }
    _user_ids = {_ADMIN_ROLE: "1", _READ_WRITE_ROLE: "2", _READ_ONLY_ROLE: "3"}
    _flat_key_dir = str(runtime.config.get("flat_login.demo_keys_dir", "data/flat_role_keys") or "data/flat_role_keys")
    _cookie_name = "db_web_session"
    api_base = _server_base(runtime.config.get("api_server.host"), runtime.config.get("api_server.port"))
    mcp_base = _server_base(runtime.config.get("mcp_server.host"), runtime.config.get("mcp_server.port"))
    a2a_base = _server_base(runtime.config.get("a2a_server.host"), runtime.config.get("a2a_server.port"))
    api_proxy = _build_proxy(api_base)
    api_session_proxy = _build_proxy(api_base, api_key=_service_api_key)
    cookie_path = web_base_path or "/"
    api_proxy_prefix = join_route(web_base_path, "/api")
    webapi_prefix = join_route(web_base_path, "/webapi")
    webapi_docs_prefix = join_route(web_base_path, "/webapi-docs")
    webapi_openapi_prefix = join_route(web_base_path, "/webapi-openapi.json")
    mcp_proxy_prefix = join_route(web_base_path, mcp_base_path)
    webmcp_prefix = join_route(web_base_path, "/webmcp")
    weba2a_prefix = join_route(web_base_path, "/weba2a")

    @app.get(join_route(web_base_path, "/web-ready"))
    async def web_ready() -> JSONResponse:
        """Report WebUI readiness only after every proxied backend is reachable."""
        targets = {
            "api": f"{api_base}/health",
            "mcp": f"{mcp_base}/health",
            "a2a": f"{a2a_base}/health",
        }
        checks: dict[str, dict[str, object]] = {}
        async with httpx.AsyncClient(timeout=2.0) as client:
            for name, url in targets.items():
                try:
                    response = await client.get(url)
                    checks[name] = {"status_code": response.status_code, "ok": response.status_code < 500}
                except httpx.RequestError as exc:
                    checks[name] = {"status_code": None, "ok": False, "error": exc.__class__.__name__}
        ready = all(bool(item.get("ok")) for item in checks.values())
        return JSONResponse({"status": "ready" if ready else "starting", "checks": checks}, status_code=200 if ready else 503)

    def _get_session(request: Request) -> dict | None:
        token = request.cookies.get(_cookie_name)
        if token and token in _sessions:
            sess = _sessions[token]
            if time.time() - sess.get("_created", 0) < 3600:
                return sess
            del _sessions[token]
        return None

    def _webui_identity_headers(sess: dict | None) -> dict[str, str]:
        """Forward the authenticated caller identity to the API (webui-trusted).

        W28A-889-B-R2 / W28A-890: the API resolves this user's OWN RBAC; the
        service api-key is transport trust only, never the authorization identity.
        """
        if not sess:
            return {}
        return {
            "X-Request-Source": "webui",
            "X-Request-User": str(sess.get("idam_username") or sess.get("user") or ""),
        }

    def _role_permissions(role: str) -> list[str]:
        """Resolve a flat role's permission list for /auth/me (cosmetic SPA hints)."""
        if str(role).strip().lower() == _ADMIN_ROLE:
            return ["*"]
        perms = runtime.config.get(f"access_control.roles.{role}", [])
        return list(perms) if isinstance(perms, (list, tuple)) else []

    def _session_downstream_key(sess: dict | None) -> str:
        """Forward the session role's seeded flat demo api-key to the MCP/A2A tiers
        so they enforce per-role RBAC natively (read-only write tools -> 403).

        W28A-732-R5: those tiers authorise by the api-key's ROLE (they do not
        resolve the webui-trusted X-Request-User the API tier honours). A cookie
        session carries no key, so the web tier injects the role's flat demo key
        (``<flat_login.demo_keys_dir>/<role>.key``, seeded by access_control).
        admin/read-write fall back to the service key if their key file is absent;
        read-only NEVER falls back to a write-capable key — a missing read-only key
        yields an empty key (downstream 401), fail-closed, so the read-only write
        contract can never silently regress on the MCP/A2A surfaces.
        """
        if not sess:
            return ""
        role = str(sess.get("role") or "")
        try:
            key = Path(_flat_key_dir, f"{role}.key").read_text(encoding="utf-8").strip()
        except OSError:
            key = ""
        if key:
            return key
        return "" if role == _READ_ONLY_ROLE else _service_api_key

    def _read_only_write_block(sess: dict | None, request: Request) -> JSONResponse | None:
        """W28A-732-R5: web-tier read-only write-gate (defence in depth).

        A logged-in read-only visitor may VIEW every data surface but any write
        method on a non-health data path resolves to 403-inline (not 401, not a
        blank UI). admin / read-write fall through; the API tier's own per-user
        RBAC (forwarded X-Request-User) is the backstop on the same surface.
        """
        if sess is None:
            return None
        if (
            request.method.upper() in _WRITE_METHODS
            and not _role_can_write(sess.get("role"))
            and not request.url.path.endswith("/health")
        ):
            return JSONResponse(
                {"detail": "read-only role: write operations are not permitted", "role": _READ_ONLY_ROLE},
                status_code=403,
            )
        return None

    def _request_api_key(request: Request) -> str:
        """Extract an API key from the configured browser auth headers."""
        api_key = request.headers.get("X-API-Key", "").strip()
        if api_key:
            return api_key
        authorisation = request.headers.get("Authorization", "").strip()
        if authorisation.lower().startswith("bearer "):
            return authorisation[7:].strip()
        return ""

    def _compat_session_or_principal(request: Request) -> tuple[dict | None, object | None]:
        """Resolve compatibility endpoints from either cookie session or API key."""
        sess = _get_session(request)
        if sess:
            return sess, None
        api_key = _request_api_key(request)
        if api_key:
            principal = runtime.access_control.verify_api_key(api_key)
            if principal is not None:
                return None, principal
        return None, None

    def _principal_is_system_admin(principal: object) -> bool:
        roles = {str(role).strip().lower() for role in getattr(principal, "roles", []) or []}
        permissions = {str(permission).strip() for permission in getattr(principal, "permissions", []) or []}
        return "admin" in roles or "system_admin" in roles or "*" in permissions

    def _principal_can_write(principal: object) -> bool:
        permissions = {str(permission).strip() for permission in getattr(principal, "permissions", []) or []}
        return "*" in permissions or bool({"admin.write", "index.manage", "profile.manage"} & permissions)

    @app.post(join_route(web_base_path, "/auth/login"))
    async def auth_login(request: Request) -> JSONResponse:
        """Validate username/password and mint a flat-role cookie session.

        W28A-732-R5: the WebUI front door is username/password (cookie). Compare
        against EVERY flat account with secrets.compare_digest so a wrong username
        and a wrong password are indistinguishable (no enumeration). The matched
        account decides the flat role and the forwarded IDAM principal.
        """
        body = await request.json()
        username = str(body.get("username", "")).strip()
        password = str(body.get("password", "")).strip()
        if not username or not password:
            raise HTTPException(status_code=400, detail="Username and password required")
        matched: tuple[str, str] | None = None  # (flat_role, idam_principal)
        for cand_user, (cand_pw, cand_role, cand_principal) in _flat_accounts.items():
            user_ok = secrets.compare_digest(username, cand_user)
            pw_ok = bool(cand_pw) and secrets.compare_digest(password, cand_pw)
            if user_ok and pw_ok:
                matched = (cand_role, cand_principal)
                break
        if matched is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        role, idam_principal = matched
        user_id = _user_ids[role]
        token = secrets.token_urlsafe(32)
        _sessions[token] = {
            "user": username,
            "user_id": user_id,
            "role": role,
            # W28A-889-B-R2 / W28A-890: bind the session to the real seeded IDAM
            # principal so the API authorizes per-user RBAC (not the service principal).
            "idam_username": idam_principal,
            "_created": time.time(),
        }
        resp = JSONResponse({"user": {"id": user_id, "displayName": username, "email": None, "roles": [role], "permissions": _role_permissions(role)}})
        resp.set_cookie(_cookie_name, token, httponly=True, samesite="lax", max_age=3600, path=cookie_path)
        return resp

    @app.get(join_route(web_base_path, "/auth/me"))
    async def auth_me(request: Request) -> JSONResponse:
        sess = _get_session(request)
        if not sess:
            api_key = _request_api_key(request)
            if api_key:
                principal = runtime.access_control.verify_api_key(api_key)
                if principal is not None:
                    return JSONResponse({"user": runtime.access_control.principal_summary(principal)})
            return JSONResponse(None)
        return JSONResponse({"user": {"id": sess["user_id"], "displayName": sess["user"], "email": None, "roles": [sess["role"]], "permissions": _role_permissions(sess["role"])}})

    @app.post(join_route(web_base_path, "/auth/logout"))
    async def auth_logout(request: Request) -> JSONResponse:
        token = request.cookies.get(_cookie_name)
        if token:
            _sessions.pop(token, None)
        resp = JSONResponse({"ok": True})
        resp.delete_cookie(_cookie_name, path=cookie_path)
        return resp

    @app.get(join_route(web_base_path, "/webapi/auth/status"))
    async def webapi_auth_status(request: Request) -> JSONResponse:
        """Compatibility status endpoint for shared IDAM WebUI pages."""
        sess, principal = _compat_session_or_principal(request)
        if not sess and principal is None:
            raise HTTPException(status_code=401, detail="Not authenticated")
        if principal is not None:
            return JSONResponse(
                {
                    "username": str(getattr(principal, "username", "") or getattr(principal, "user_id", "")),
                    "role": ",".join(str(role) for role in getattr(principal, "roles", []) or []),
                    "is_system_admin": _principal_is_system_admin(principal),
                    "can_write": _principal_can_write(principal),
                }
            )
        role = str(sess.get("role") or "")
        return JSONResponse(
            {
                "username": str(sess.get("user") or ""),
                "role": role,
                "is_system_admin": role == _ADMIN_ROLE,
                "can_write": _role_can_write(role),
            }
        )

    @app.get(join_route(web_base_path, "/webapi/v1/admin/permissions"))
    async def webapi_idam_permissions(request: Request) -> JSONResponse:
        """Compatibility permission list for shared IDAM Roles WebUI."""
        sess, principal = _compat_session_or_principal(request)
        if not sess and principal is None:
            raise HTTPException(status_code=401, detail="Not authenticated")
        permissions: set[str] = set()
        for role in (_ADMIN_ROLE, _READ_WRITE_ROLE, _READ_ONLY_ROLE):
            role_permissions = runtime.config.get(f"access_control.roles.{role}", [])
            if isinstance(role_permissions, (list, tuple, set)):
                permissions.update(str(item) for item in role_permissions if str(item).strip())
        return JSONResponse({"permissions": sorted(permissions) or ["*"]})

    @app.get(join_route(web_base_path, "/webapi/v1/idam/v1/rbac-bindings"))
    async def webapi_idam_rbac_bindings(request: Request) -> JSONResponse:
        """Compatibility RBAC bindings list for shared IDAM RBAC WebUI."""
        sess, principal = _compat_session_or_principal(request)
        if not sess and principal is None:
            raise HTTPException(status_code=401, detail="Not authenticated")
        return JSONResponse({"bindings": []})

    @app.get(join_route(web_base_path, "/runtime-config.js"), response_class=Response)
    async def runtime_config(request: Request) -> Response:
        """Return runtime configuration for the SPA bootstrap contract."""
        return serve_runtime_config(runtime, request)

    @app.get(join_route(web_base_path, "/apikeys"))
    @app.get(join_route(web_base_path, "/api-keys"))
    async def api_keys_legacy_alias(request: Request) -> Response:
        """Redirect API-key WebUI aliases before the /api proxy can claim them."""
        return _webui_redirect(request, join_route(web_base_path, "/admin/api-keys"))

    @app.get(join_route(web_base_path, "/api-docs"))
    async def api_docs_legacy_alias(request: Request) -> Response:
        """Redirect the legacy API docs route before the /api proxy can claim it."""
        return _webui_redirect(request, join_route(web_base_path, "/developer/api-docs"))

    @app.api_route(api_proxy_prefix, methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    @app.api_route(f"{api_proxy_prefix}/{{full_path:path}}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    async def proxy_api(request: Request, full_path: str = "") -> Response:
        """Proxy same-origin API requests to the dedicated API server.

        Strips the /api prefix so the API server receives /v1/…
        (mirroring the Traefik stripprefix on the api_path router).
        """
        sess = _get_session(request)
        blocked = _read_only_write_block(sess, request)
        if blocked is not None:
            return blocked
        return await _proxy_via(
            request,
            proxy=api_session_proxy if sess else api_proxy,
            strip_prefix=api_proxy_prefix,
            extra_headers=_webui_identity_headers(sess),
        )

    @app.api_route(webapi_prefix, methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    @app.api_route(f"{webapi_prefix}/{{full_path:path}}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    async def proxy_web_api(request: Request, full_path: str = "") -> Response:
        """Proxy cookie-authenticated browser API requests on a dedicated path.

        Strips /webapi → /v1/… so the API server receives the
        correct route prefix (matching api_server.base_path).
        """
        sess = _get_session(request)
        blocked = _read_only_write_block(sess, request)
        if blocked is not None:
            return blocked
        return await _proxy_via(
            request,
            proxy=api_session_proxy if sess else api_proxy,
            strip_prefix=webapi_prefix,
            rewrite_prefix=api_alias_rewrite_prefix,
            extra_headers=_webui_identity_headers(sess),
        )

    @app.api_route(webapi_docs_prefix, methods=["GET"])
    async def proxy_web_api_docs(request: Request) -> Response:
        """Proxy the API Swagger UI without the /api prefix rewrite."""
        return await _proxy_via(
            request,
            proxy=api_session_proxy if _get_session(request) else api_proxy,
            strip_prefix=webapi_docs_prefix,
            rewrite_prefix="/docs",
        )

    @app.api_route(webapi_openapi_prefix, methods=["GET"])
    async def proxy_web_api_openapi(request: Request) -> Response:
        """Proxy the API OpenAPI schema without the /api prefix rewrite."""
        return await _proxy_via(
            request,
            proxy=api_session_proxy,
            strip_prefix=webapi_openapi_prefix,
            rewrite_prefix="/openapi.json",
        )

    @app.api_route(mcp_proxy_prefix, methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    @app.api_route(f"{mcp_proxy_prefix}/{{full_path:path}}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    async def proxy_mcp(request: Request, full_path: str = "") -> Response:
        """Proxy same-origin MCP requests to the dedicated MCP server."""
        return await _proxy_request(
            request,
            target_base=mcp_base,
            strip_prefix=web_base_path,
            session_api_key=_session_downstream_key(_get_session(request)),
        )

    @app.api_route(webmcp_prefix, methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    @app.api_route(f"{webmcp_prefix}/{{full_path:path}}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    async def proxy_web_mcp(request: Request, full_path: str = "") -> Response:
        """Proxy cookie-authenticated browser MCP requests on a dedicated path.

        Rewrites /webmcp/tools/… → /mcp/tools/… so the MCP server receives the
        correct route prefix.
        """
        return await _proxy_request(
            request,
            target_base=mcp_base,
            strip_prefix=webmcp_prefix,
            rewrite_prefix=mcp_base_path,
            session_api_key=_session_downstream_key(_get_session(request)),
        )

    @app.api_route(weba2a_prefix, methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    @app.api_route(f"{weba2a_prefix}/{{full_path:path}}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    async def proxy_web_a2a(request: Request, full_path: str = "") -> Response:
        """Proxy cookie-authenticated browser A2A requests on a dedicated path."""
        return await _proxy_request(
            request,
            target_base=a2a_base,
            strip_prefix=weba2a_prefix,
            rewrite_prefix=a2a_base_path,
            session_api_key=_session_downstream_key(_get_session(request)),
        )

    @app.get(join_route(web_base_path, "/"))
    async def root() -> Response:
        """Serve the SPA entrypoint for the application root."""
        return serve_spa_index()

    @app.get(join_route(web_base_path, "/robots.txt"))
    async def robots() -> Response:
        """Disable indexing for local admin surfaces."""
        return PlainTextResponse("User-agent: *\nDisallow: /\n")

    @app.get(join_route(web_base_path, "/developer/api-docs"))
    async def api_docs_spa() -> Response:
        """Serve the SPA shell for the canonical API docs route."""
        return serve_spa_index()

    @app.get(join_route(web_base_path, "/{path:path}"))
    async def spa(path: str, request: Request) -> Response:
        """Serve static SPA assets and browser-history routes from ui/dist."""
        cleaned = "/" + path.lstrip("/")
        redirect_target = _WEBUI_LEGACY_REDIRECTS.get(cleaned)
        if redirect_target:
            return _webui_redirect(request, join_route(web_base_path, redirect_target))
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
    extra_headers: dict[str, str] | None = None,
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
    if extra_headers:
        headers.update(extra_headers)
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
                extra_headers=extra_headers,
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
    extra_headers: dict[str, str] | None = None,
) -> Response:
    target_path = request.url.path
    if strip_prefix and target_path.startswith(strip_prefix):
        target_path = target_path[len(strip_prefix):] or "/"
    if rewrite_prefix:
        target_path = rewrite_prefix + target_path
    target_url = httpx.URL(target_base.rstrip("/") + target_path).copy_merge_params(request.query_params)
    try:
        body = await request.body()
    except ClientDisconnect:
        return Response(status_code=499)
    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in _HOP_BY_HOP_HEADERS
    }
    if extra_headers:
        headers.update(extra_headers)
    lower_headers = {key.lower() for key in headers}
    if session_api_key:
        if "x-api-key" not in lower_headers:
            headers["x-api-key"] = session_api_key
        if "authorization" not in lower_headers:
            headers["authorization"] = f"Bearer {session_api_key}"
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            proxied = await client.request(
                request.method,
                target_url,
                content=body,
                headers=headers,
            )
    except httpx.RequestError as exc:
        return JSONResponse(
            {
                "detail": "Upstream service unavailable",
                "target": str(target_url),
                "error": exc.__class__.__name__,
            },
            status_code=503,
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
