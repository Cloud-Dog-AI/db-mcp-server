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
# Description: API-key authentication helpers using access-control state.
# Related requirements: AC-01, AC-02, W28A-274-A deliverables 1, 2
# Related tests: UT1.2, UT1.3, ST1.2, IT1.1

"""Authentication helpers for db-mcp-server."""

from __future__ import annotations

from typing import Any

from src.core.access_control.service import AccessControlService


class APIKeyAuthoriser:
    """API-key verifier backed by the access-control service."""

    def __init__(self, access_control: AccessControlService) -> None:
        self._access_control = access_control

    async def verify_api_key(self, api_key: str) -> dict[str, Any] | None:
        """Validate an API key and return FastAPI-compatible auth state."""
        principal = self._access_control.verify_api_key(api_key)
        if principal is None:
            return None

        return {
            "user_id": principal.user_id,
            "roles": principal.roles,
            "permissions": principal.permissions,
            "tenant_id": principal.tenant_id,
            "username": principal.username,
            "api_key_id": principal.api_key_id,
            "profile_ids": principal.profile_ids,
            "scopes": principal.scopes,
            "principal": principal,
        }
