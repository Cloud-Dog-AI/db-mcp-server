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
# Description: Shared HTTP middleware helpers for db-mcp-server.
# Related requirements: W28A-274-A deliverables 1, 2, AC-01, AC-02
# Related tests: UT1.2, UT1.3, ST1.1, ST1.2, IT1.1

"""HTTP middleware helpers for db-mcp-server."""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.common.base_paths import normalise_base_path


class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    """Protect non-exempt HTTP routes with API-key authentication."""

    # JSON-RPC methods that are allowed without authentication on MCP
    # transport paths.  ``tools/list`` is the MCP catalogue discovery
    # method used by gate/health probes that carry no credentials.
    _PUBLIC_MCP_METHODS: frozenset[str] = frozenset({"tools/list"})
    _MCP_PATHS: frozenset[str] = frozenset({"/mcp", "/messages"})

    def __init__(
        self,
        app,
        *,
        verify_api_key: Callable[[str], Awaitable[dict[str, Any] | None]],
        exempt_paths: set[str] | None = None,
        api_key_header: str = "X-API-Key",
        public_mcp_paths: set[str] | None = None,
        resolve_web_user: Callable[[str], Any] | None = None,
    ) -> None:
        super().__init__(app)
        self._verify_api_key = verify_api_key
        self._exempt_paths = exempt_paths or set()
        self._api_key_header = api_key_header
        # W28A-889-B-R2 / W28A-890: optional resolver that maps a forwarded
        # X-Request-User (webui-trusted) to that user's OWN RBAC principal, so the
        # web tier no longer collapses every session to the service principal.
        self._resolve_web_user = resolve_web_user
        self._public_mcp_paths = frozenset(
            normalise_base_path(path) or "/"
            for path in (public_mcp_paths or set(self._MCP_PATHS))
        )

    async def _is_public_mcp_request(self, request: Request) -> bool:
        """Return True when the request is an unauthenticated-safe MCP method."""
        if request.method != "POST" or request.url.path not in self._public_mcp_paths:
            return False
        try:
            body = await request.body()
            payload = json.loads(body)
            if isinstance(payload, dict):
                return str(payload.get("method", "")) in self._PUBLIC_MCP_METHODS
        except Exception:
            pass
        return False

    async def dispatch(self, request: Request, call_next):
        """Check the inbound API key unless the path is public."""
        if request.url.path in self._exempt_paths:
            return await call_next(request)

        if await self._is_public_mcp_request(request):
            return await call_next(request)

        api_key = request.headers.get(self._api_key_header, "").strip()
        if not api_key:
            authorisation = request.headers.get("Authorization", "").strip()
            if authorisation.lower().startswith("bearer "):
                api_key = authorisation[7:].strip()
        if not api_key:
            return JSONResponse(
                status_code=401,
                content={"ok": False, "error": {"code": "UNAUTHENTICATED", "message": "Missing API key"}},
            )

        auth_result = await self._verify_api_key(api_key)
        if auth_result is None:
            return JSONResponse(
                status_code=401,
                content={"ok": False, "error": {"code": "UNAUTHENTICATED", "message": "Invalid API key"}},
            )

        request.state.user = auth_result.get("user_id")
        request.state.username = auth_result.get("username")
        request.state.roles = auth_result.get("roles", [])
        request.state.permissions = auth_result.get("permissions", [])
        request.state.tenant_id = auth_result.get("tenant_id")
        request.state.api_key_id = auth_result.get("api_key_id")
        request.state.profile_ids = auth_result.get("profile_ids", [])
        request.state.scopes = auth_result.get("scopes", [])
        request.state.principal = auth_result.get("principal")

        # W28A-889-B-R2 / W28A-890: web-tier identity forwarding. The web origin
        # authenticates with the service api-key (transport trust); authorization
        # MUST be the forwarded caller's own RBAC, never the service principal.
        # Only an admin/service-key transport principal ("*") may forward identity,
        # so a non-admin api-key holder cannot escalate by sending the header.
        forwarded_source = request.headers.get("X-Request-Source", "").strip().lower()
        forwarded_user = request.headers.get("X-Request-User", "").strip()
        transport_permissions = auth_result.get("permissions", []) or []
        if (
            forwarded_source == "webui"
            and forwarded_user
            and self._resolve_web_user is not None
            and "*" in transport_permissions
        ):
            forwarded_principal = self._resolve_web_user(forwarded_user)
            if forwarded_principal is None:
                return JSONResponse(
                    status_code=401,
                    content={"ok": False, "error": {"code": "UNAUTHENTICATED", "message": "Unknown forwarded web user"}},
                )
            request.state.user = forwarded_principal.user_id
            request.state.username = forwarded_principal.username
            request.state.roles = forwarded_principal.roles
            request.state.permissions = forwarded_principal.permissions
            request.state.tenant_id = forwarded_principal.tenant_id
            request.state.api_key_id = forwarded_principal.api_key_id
            request.state.profile_ids = forwarded_principal.profile_ids
            request.state.scopes = forwarded_principal.scopes
            request.state.principal = forwarded_principal
        return await call_next(request)
