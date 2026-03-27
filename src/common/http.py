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
    ) -> None:
        super().__init__(app)
        self._verify_api_key = verify_api_key
        self._exempt_paths = exempt_paths or set()
        self._api_key_header = api_key_header

    async def _is_public_mcp_request(self, request: Request) -> bool:
        """Return True when the request is an unauthenticated-safe MCP method."""
        if request.method != "POST" or request.url.path not in self._MCP_PATHS:
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
        return await call_next(request)
