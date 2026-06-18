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
# Description: API routes for db-mcp-server access-control management.
# Related requirements: AC-01, AC-02, AC-03, CFG-01
# Related tests: ST1.2, IT1.1

"""Access-control API routes for db-mcp-server."""

from __future__ import annotations

from fastapi import APIRouter, Request

from cloud_dog_api_kit import success_envelope

from src.core.access_control.schemas import (
    ApiKeyCreateRequest,
    GroupUpsertRequest,
    MaskPreviewRequest,
    ProfileUpsertRequest,
    ProfileScopeTestRequest,
    RevokeApiKeyRequest,
    RoleCreateRequest,
    RoleUpdateRequest,
    UserUpsertRequest,
)


def create_access_control_router(runtime, base_path: str) -> APIRouter:
    """Create the access-control CRUD router."""
    access = runtime.access_control
    router = APIRouter(prefix=base_path, tags=["access-control"])

    @router.get("/profiles")
    async def list_profiles(request: Request) -> dict:
        access.require_request_permission(
            request,
            permission="profile.manage",
            audit_resource_type="profile",
            audit_resource_id="list",
        )
        return success_envelope(access.list_profiles())

    @router.post("/profiles")
    async def create_profile(payload: ProfileUpsertRequest, request: Request) -> dict:
        principal = access.require_request_permission(
            request,
            permission="profile.manage",
            audit_resource_type="profile",
            audit_resource_id="create",
        )
        return success_envelope(
            access.create_profile(
                payload.model_dump(),
                actor_user_id=principal.user_id,
                actor_roles=principal.roles,
            )
        )

    @router.get("/profiles/{profile_id}")
    async def get_profile(profile_id: str, request: Request) -> dict:
        access.require_request_permission(
            request,
            permission="profile.manage",
            audit_resource_type="profile",
            audit_resource_id=profile_id,
        )
        return success_envelope(access.get_profile(profile_id))

    @router.put("/profiles/{profile_id}")
    async def update_profile(profile_id: str, payload: ProfileUpsertRequest, request: Request) -> dict:
        principal = access.require_request_permission(
            request,
            permission="profile.manage",
            audit_resource_type="profile",
            audit_resource_id=profile_id,
        )
        return success_envelope(
            access.update_profile(
                profile_id,
                payload.model_dump(),
                actor_user_id=principal.user_id,
                actor_roles=principal.roles,
            )
        )

    @router.delete("/profiles/{profile_id}")
    async def delete_profile(profile_id: str, request: Request) -> dict:
        principal = access.require_request_permission(
            request,
            permission="profile.manage",
            audit_resource_type="profile",
            audit_resource_id=profile_id,
        )
        access.delete_profile(profile_id, actor_user_id=principal.user_id, actor_roles=principal.roles)
        return success_envelope({"deleted": True, "profile_id": profile_id})

    @router.post("/admin/profiles/{profile_id}/test-scope")
    async def test_profile_scope(
        profile_id: str,
        payload: ProfileScopeTestRequest,
        request: Request,
    ) -> dict:
        return success_envelope(
            access.test_profile_scope(
                request,
                profile_id=profile_id,
                payload=payload.model_dump(),
            )
        )

    @router.post("/profiles/{profile_id}/mask-preview")
    async def mask_preview(profile_id: str, payload: MaskPreviewRequest, request: Request) -> dict:
        access.require_request_permission(
            request,
            permission="data.read",
            profile_id=profile_id,
            audit_resource_type="profile",
            audit_resource_id=profile_id,
        )
        return success_envelope(access.apply_profile_mask(profile_id, payload.record))

    @router.get("/profiles/{profile_id}/authorise/{permission}")
    async def profile_authorise(profile_id: str, permission: str, request: Request) -> dict:
        principal = access.require_request_permission(
            request,
            permission=permission,
            profile_id=profile_id,
            audit_resource_type="profile",
            audit_resource_id=profile_id,
        )
        return success_envelope(access.profile_access_summary(principal, profile_id, permission))

    @router.get("/users")
    async def list_users(request: Request) -> dict:
        access.require_request_permission(
            request,
            permission="profile.manage",
            audit_resource_type="user",
            audit_resource_id="list",
        )
        return success_envelope(access.list_users())

    @router.post("/users")
    async def create_user(payload: UserUpsertRequest, request: Request) -> dict:
        principal = access.require_request_permission(
            request,
            permission="profile.manage",
            audit_resource_type="user",
            audit_resource_id="create",
        )
        return success_envelope(
            access.create_user(
                payload.model_dump(),
                actor_user_id=principal.user_id,
                actor_roles=principal.roles,
            )
        )

    @router.get("/users/{user_id}")
    async def get_user(user_id: str, request: Request) -> dict:
        access.require_request_permission(
            request,
            permission="profile.manage",
            audit_resource_type="user",
            audit_resource_id=user_id,
        )
        return success_envelope(access.get_user(user_id))

    @router.put("/users/{user_id}")
    async def update_user(user_id: str, payload: UserUpsertRequest, request: Request) -> dict:
        principal = access.require_request_permission(
            request,
            permission="profile.manage",
            audit_resource_type="user",
            audit_resource_id=user_id,
        )
        return success_envelope(
            access.update_user(
                user_id,
                payload.model_dump(),
                actor_user_id=principal.user_id,
                actor_roles=principal.roles,
            )
        )

    @router.delete("/users/{user_id}")
    async def delete_user(user_id: str, request: Request) -> dict:
        principal = access.require_request_permission(
            request,
            permission="profile.manage",
            audit_resource_type="user",
            audit_resource_id=user_id,
        )
        access.delete_user(user_id, actor_user_id=principal.user_id, actor_roles=principal.roles)
        return success_envelope({"deleted": True, "user_id": user_id})

    @router.get("/groups")
    async def list_groups(request: Request) -> dict:
        access.require_request_permission(
            request,
            permission="profile.manage",
            audit_resource_type="group",
            audit_resource_id="list",
        )
        return success_envelope(access.list_groups())

    @router.post("/groups")
    async def create_group(payload: GroupUpsertRequest, request: Request) -> dict:
        principal = access.require_request_permission(
            request,
            permission="profile.manage",
            audit_resource_type="group",
            audit_resource_id="create",
        )
        return success_envelope(
            access.create_group(
                payload.model_dump(),
                actor_user_id=principal.user_id,
                actor_roles=principal.roles,
            )
        )

    @router.get("/groups/{group_id}")
    async def get_group(group_id: str, request: Request) -> dict:
        access.require_request_permission(
            request,
            permission="profile.manage",
            audit_resource_type="group",
            audit_resource_id=group_id,
        )
        return success_envelope(access.get_group(group_id))

    @router.put("/groups/{group_id}")
    async def update_group(group_id: str, payload: GroupUpsertRequest, request: Request) -> dict:
        principal = access.require_request_permission(
            request,
            permission="profile.manage",
            audit_resource_type="group",
            audit_resource_id=group_id,
        )
        return success_envelope(
            access.update_group(
                group_id,
                payload.model_dump(),
                actor_user_id=principal.user_id,
                actor_roles=principal.roles,
            )
        )

    @router.delete("/groups/{group_id}")
    async def delete_group(group_id: str, request: Request) -> dict:
        principal = access.require_request_permission(
            request,
            permission="profile.manage",
            audit_resource_type="group",
            audit_resource_id=group_id,
        )
        access.delete_group(group_id, actor_user_id=principal.user_id, actor_roles=principal.roles)
        return success_envelope({"deleted": True, "group_id": group_id})

    @router.get("/roles")
    async def list_roles(request: Request) -> dict:
        access.require_request_permission(
            request,
            permission="profile.manage",
            audit_resource_type="role",
            audit_resource_id="list",
        )
        return success_envelope(access.list_roles())

    @router.post("/roles")
    async def create_role(payload: RoleCreateRequest, request: Request) -> dict:
        principal = access.require_request_permission(
            request,
            permission="profile.manage",
            audit_resource_type="role",
            audit_resource_id="create",
        )
        return success_envelope(
            access.create_role(
                payload.model_dump(),
                actor_user_id=principal.user_id,
                actor_roles=principal.roles,
            )
        )

    @router.get("/roles/{role_id}")
    async def get_role(role_id: str, request: Request) -> dict:
        access.require_request_permission(
            request,
            permission="profile.manage",
            audit_resource_type="role",
            audit_resource_id=role_id,
        )
        return success_envelope(access.get_role(role_id))

    @router.put("/roles/{role_id}")
    async def update_role(role_id: str, payload: RoleUpdateRequest, request: Request) -> dict:
        principal = access.require_request_permission(
            request,
            permission="profile.manage",
            audit_resource_type="role",
            audit_resource_id=role_id,
        )
        return success_envelope(
            access.update_role(
                role_id,
                payload.model_dump(exclude_unset=True),
                actor_user_id=principal.user_id,
                actor_roles=principal.roles,
            )
        )

    @router.patch("/roles/{role_id}")
    async def patch_role(role_id: str, payload: RoleUpdateRequest, request: Request) -> dict:
        principal = access.require_request_permission(
            request,
            permission="profile.manage",
            audit_resource_type="role",
            audit_resource_id=role_id,
        )
        return success_envelope(
            access.update_role(
                role_id,
                payload.model_dump(exclude_unset=True),
                actor_user_id=principal.user_id,
                actor_roles=principal.roles,
            )
        )

    @router.delete("/roles/{role_id}")
    async def delete_role(role_id: str, request: Request) -> dict:
        principal = access.require_request_permission(
            request,
            permission="profile.manage",
            audit_resource_type="role",
            audit_resource_id=role_id,
        )
        access.delete_role(role_id, actor_user_id=principal.user_id, actor_roles=principal.roles)
        return success_envelope({"deleted": True, "role_id": role_id})

    @router.get("/api-keys")
    async def list_api_keys(request: Request, owner_user_id: str | None = None) -> dict:
        access.require_request_permission(
            request,
            permission="profile.manage",
            audit_resource_type="api_key",
            audit_resource_id="list",
        )
        return success_envelope(access.list_api_keys(owner_user_id))

    @router.post("/api-keys")
    async def create_api_key(payload: ApiKeyCreateRequest, request: Request) -> dict:
        principal = access.require_request_permission(
            request,
            permission="profile.manage",
            audit_resource_type="api_key",
            audit_resource_id="create",
        )
        return success_envelope(
            access.create_api_key(
                payload.model_dump(),
                actor_user_id=principal.user_id,
                actor_roles=principal.roles,
            )
        )

    @router.post("/api-keys/{api_key_id}/revoke")
    async def revoke_api_key(api_key_id: str, payload: RevokeApiKeyRequest, request: Request) -> dict:
        principal = access.require_request_permission(
            request,
            permission="profile.manage",
            audit_resource_type="api_key",
            audit_resource_id=api_key_id,
        )
        access.revoke_api_key(
            api_key_id,
            actor_user_id=principal.user_id,
            actor_roles=principal.roles,
            reason=payload.reason,
        )
        return success_envelope({"revoked": True, "api_key_id": api_key_id})

    @router.post("/api-keys/{api_key_id}/rotate")
    async def rotate_api_key(api_key_id: str, payload: RevokeApiKeyRequest, request: Request) -> dict:
        principal = access.require_request_permission(
            request,
            permission="profile.manage",
            audit_resource_type="api_key",
            audit_resource_id=api_key_id,
        )
        return success_envelope(
            access.rotate_api_key(
                api_key_id,
                actor_user_id=principal.user_id,
                actor_roles=principal.roles,
                reason=payload.reason,
            )
        )

    return router
