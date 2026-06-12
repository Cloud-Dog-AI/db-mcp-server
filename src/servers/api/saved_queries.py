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
# Description: Saved query-builder state API routes.
# Related requirements: W28A-871 DM-DB-01, CW-DA5
# Related tests: IT1.12

"""Saved-query API routes for data-admin pages."""

from __future__ import annotations

from fastapi import APIRouter, Request

from cloud_dog_api_kit import success_envelope

from src.core.access_control.schemas import SavedQueryCreateRequest, SavedQueryUpdateRequest


def create_saved_queries_router(runtime, base_path: str) -> APIRouter:
    """Create saved-query CRUD routes."""
    access = runtime.access_control
    router = APIRouter(prefix=base_path, tags=["saved-queries"])

    @router.post("/admin/saved-queries")
    async def create_saved_query(payload: SavedQueryCreateRequest, request: Request) -> dict:
        return success_envelope(access.create_saved_query(request, payload.model_dump()))

    @router.get("/admin/saved-queries")
    async def list_saved_queries(page_key: str, request: Request) -> dict:
        return success_envelope(access.list_saved_queries(request, page_key=page_key))

    @router.get("/admin/saved-queries/{query_id}")
    async def get_saved_query(query_id: int, request: Request) -> dict:
        return success_envelope(access.get_saved_query(request, query_id=query_id))

    @router.patch("/admin/saved-queries/{query_id}")
    async def update_saved_query(
        query_id: int,
        payload: SavedQueryUpdateRequest,
        request: Request,
    ) -> dict:
        return success_envelope(
            access.update_saved_query(
                request,
                query_id=query_id,
                payload=payload.model_dump(),
            )
        )

    @router.delete("/admin/saved-queries/{query_id}")
    async def delete_saved_query(query_id: int, request: Request) -> dict:
        access.delete_saved_query(request, query_id=query_id)
        return success_envelope({"deleted": True, "id": query_id})

    return router
