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
# Description: Schema-change API routes.
# Related requirements: W28A-871 DM-S-05
# Related tests: UT1.21

"""Schema-change approval API routes."""

from __future__ import annotations

from fastapi import APIRouter, Request

from cloud_dog_api_kit import success_envelope

from src.core.access_control.schemas import SchemaChangeApproveRequest


def create_schema_changes_router(runtime, base_path: str) -> APIRouter:
    """Create schema-change routes."""
    schema_changes = runtime.schema_changes
    router = APIRouter(prefix=base_path, tags=["schema-changes"])

    @router.post("/schema-changes/{plan_id}/approve")
    async def approve_schema_change(
        plan_id: str,
        payload: SchemaChangeApproveRequest,
        request: Request,
    ) -> dict:
        return success_envelope(
            schema_changes.approve_plan(
                request,
                plan_id=plan_id,
                payload=payload.model_dump(),
            )
        )

    return router
