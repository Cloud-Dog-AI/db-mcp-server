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
# Description: Gated test-data seed API route.
# Related requirements: W28A-871 CW-TD2
# Related tests: UT1.22

"""Test-data seed API routes."""

from __future__ import annotations

from fastapi import APIRouter, Request

from cloud_dog_api_kit import success_envelope

from src.core.access_control.schemas import TestDataSeedRequest


def create_test_data_router(runtime, base_path: str) -> APIRouter:
    """Create test-data routes."""
    router = APIRouter(prefix=base_path, tags=["test-data"])

    @router.post("/admin/test-data/seed")
    async def seed_test_data(payload: TestDataSeedRequest, request: Request) -> dict:
        return success_envelope(
            runtime.test_data.seed(
                request,
                dataset_id=payload.dataset_id,
                connection_name=payload.connection_name,
            )
        )

    return router
