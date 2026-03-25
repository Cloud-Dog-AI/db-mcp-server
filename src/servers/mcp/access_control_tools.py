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
# Description: MCP management tools for db-mcp-server access control.
# Related requirements: AC-01, AC-02, CFG-01
# Related tests: IT1.1

"""MCP management tools for db-mcp-server access control."""

from __future__ import annotations

from typing import Any

from fastapi import Request

from cloud_dog_api_kit import ToolContract
from cloud_dog_api_kit.errors import UnauthorisedError


def _require_admin(request: Request) -> None:
    roles = set(getattr(request.state, "roles", []) or [])
    if "admin" not in roles:
        raise UnauthorisedError(message="Admin access required")


def build_access_control_tool_registry(runtime) -> dict[str, ToolContract]:
    """Build MCP tools for access-control CRUD parity."""
    access = runtime.access_control

    async def profiles_list(_payload: dict[str, Any], request: Request) -> dict[str, Any]:
        _require_admin(request)
        return {"items": access.list_profiles()}

    async def profiles_create(payload: dict[str, Any], request: Request) -> dict[str, Any]:
        _require_admin(request)
        principal = access.principal_from_request(request)
        return access.create_profile(payload, actor_user_id=principal.user_id, actor_roles=principal.roles)

    async def profiles_get(payload: dict[str, Any], request: Request) -> dict[str, Any]:
        _require_admin(request)
        return access.get_profile(str(payload.get("profile_id", "")))

    async def profiles_update(payload: dict[str, Any], request: Request) -> dict[str, Any]:
        _require_admin(request)
        principal = access.principal_from_request(request)
        profile_id = str(payload.get("profile_id", ""))
        update_payload = dict(payload)
        update_payload.pop("profile_id", None)
        return access.update_profile(profile_id, update_payload, actor_user_id=principal.user_id, actor_roles=principal.roles)

    async def profiles_delete(payload: dict[str, Any], request: Request) -> dict[str, Any]:
        _require_admin(request)
        principal = access.principal_from_request(request)
        profile_id = str(payload.get("profile_id", ""))
        access.delete_profile(profile_id, actor_user_id=principal.user_id, actor_roles=principal.roles)
        return {"deleted": True, "profile_id": profile_id}

    async def users_list(_payload: dict[str, Any], request: Request) -> dict[str, Any]:
        _require_admin(request)
        return {"items": access.list_users()}

    async def users_create(payload: dict[str, Any], request: Request) -> dict[str, Any]:
        _require_admin(request)
        principal = access.principal_from_request(request)
        return access.create_user(payload, actor_user_id=principal.user_id, actor_roles=principal.roles)

    async def groups_list(_payload: dict[str, Any], request: Request) -> dict[str, Any]:
        _require_admin(request)
        return {"items": access.list_groups()}

    async def groups_create(payload: dict[str, Any], request: Request) -> dict[str, Any]:
        _require_admin(request)
        principal = access.principal_from_request(request)
        return access.create_group(payload, actor_user_id=principal.user_id, actor_roles=principal.roles)

    async def api_keys_list(payload: dict[str, Any], request: Request) -> dict[str, Any]:
        _require_admin(request)
        return {"items": access.list_api_keys(payload.get("owner_user_id"))}

    async def api_keys_create(payload: dict[str, Any], request: Request) -> dict[str, Any]:
        _require_admin(request)
        principal = access.principal_from_request(request)
        return access.create_api_key(payload, actor_user_id=principal.user_id, actor_roles=principal.roles)

    async def api_keys_revoke(payload: dict[str, Any], request: Request) -> dict[str, Any]:
        _require_admin(request)
        principal = access.principal_from_request(request)
        api_key_id = str(payload.get("api_key_id", ""))
        access.revoke_api_key(api_key_id, actor_user_id=principal.user_id, actor_roles=principal.roles, reason=str(payload.get("reason", "revoked")))
        return {"revoked": True, "api_key_id": api_key_id}

    return {
        "profiles.list": ToolContract(name="profiles.list", handler=profiles_list, description="List access profiles"),
        "profiles.create": ToolContract(name="profiles.create", handler=profiles_create, description="Create an access profile"),
        "profiles.get": ToolContract(name="profiles.get", handler=profiles_get, description="Get a profile by id"),
        "profiles.update": ToolContract(name="profiles.update", handler=profiles_update, description="Update a profile"),
        "profiles.delete": ToolContract(name="profiles.delete", handler=profiles_delete, description="Delete a profile"),
        "users.list": ToolContract(name="users.list", handler=users_list, description="List users"),
        "users.create": ToolContract(name="users.create", handler=users_create, description="Create a user"),
        "groups.list": ToolContract(name="groups.list", handler=groups_list, description="List groups"),
        "groups.create": ToolContract(name="groups.create", handler=groups_create, description="Create a group"),
        "api_keys.list": ToolContract(name="api_keys.list", handler=api_keys_list, description="List API keys"),
        "api_keys.create": ToolContract(name="api_keys.create", handler=api_keys_create, description="Create an API key"),
        "api_keys.revoke": ToolContract(name="api_keys.revoke", handler=api_keys_revoke, description="Revoke an API key"),
    }
