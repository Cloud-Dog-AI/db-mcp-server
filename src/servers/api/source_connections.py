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
# Description: Source-connection registry API routes.
# Related requirements: W28A-871 DM-P-07, CW-DA1, CW-DA6
# Related tests: IT1.11

"""Source-connection registry API routes for db-mcp-server."""

from __future__ import annotations

from fastapi import APIRouter, Request

from cloud_dog_api_kit import success_envelope

from src.core.access_control.schemas import (
    SourceConnectionCreateRequest,
    SourceConnectionDraftTestRequest,
    SourceConnectionUpdateRequest,
)


def create_source_connections_router(runtime, base_path: str) -> APIRouter:
    """Create source-connection CRUD and test routes."""
    access = runtime.access_control
    router = APIRouter(prefix=base_path, tags=["source-connections"])

    @router.get("/admin/source-connections")
    async def list_source_connections(request: Request) -> dict:
        access.require_request_permission(
            request,
            permission="admin.read",
            audit_resource_type="source_connection",
            audit_resource_id="list",
        )
        return success_envelope(access.list_source_connections())

    @router.post("/admin/source-connections")
    async def create_source_connection(payload: SourceConnectionCreateRequest, request: Request) -> dict:
        principal = access.require_request_permission(
            request,
            permission="admin.write",
            audit_resource_type="source_connection",
            audit_resource_id="create",
        )
        return success_envelope(
            access.create_source_connection(
                payload.model_dump(),
                actor_user_id=principal.user_id,
                actor_roles=principal.roles,
            )
        )

    @router.get("/admin/source-connections/{name}")
    async def get_source_connection(name: str, request: Request) -> dict:
        access.require_request_permission(
            request,
            permission="admin.read",
            audit_resource_type="source_connection",
            audit_resource_id=name,
        )
        return success_envelope(access.get_source_connection(name))

    @router.patch("/admin/source-connections/{name}")
    async def update_source_connection(
        name: str,
        payload: SourceConnectionUpdateRequest,
        request: Request,
    ) -> dict:
        principal = access.require_request_permission(
            request,
            permission="admin.write",
            audit_resource_type="source_connection",
            audit_resource_id=name,
        )
        return success_envelope(
            access.update_source_connection(
                name,
                payload.model_dump(),
                actor_user_id=principal.user_id,
                actor_roles=principal.roles,
            )
        )

    @router.delete("/admin/source-connections/{name}")
    async def delete_source_connection(name: str, request: Request) -> dict:
        principal = access.require_request_permission(
            request,
            permission="admin.write",
            audit_resource_type="source_connection",
            audit_resource_id=name,
        )
        access.delete_source_connection(
            name,
            actor_user_id=principal.user_id,
            actor_roles=principal.roles,
        )
        return success_envelope({"deleted": True, "name": name})

    @router.post("/admin/source-connections/{name}/test")
    async def test_source_connection(name: str, request: Request) -> dict:
        principal = access.require_request_permission(
            request,
            permission="admin.read",
            audit_resource_type="source_connection",
            audit_resource_id=name,
        )
        return success_envelope(
            access.test_source_connection(
                name,
                actor_user_id=principal.user_id,
                actor_roles=principal.roles,
            )
        )

    @router.post("/admin/source-connections/test")
    async def test_source_connection_draft(
        payload: SourceConnectionDraftTestRequest,
        request: Request,
    ) -> dict:
        access.require_request_permission(
            request,
            permission="admin.write",
            audit_resource_type="source_connection",
            audit_resource_id="draft",
        )
        return success_envelope(access.test_source_connection_draft(payload.model_dump()))

    return router
