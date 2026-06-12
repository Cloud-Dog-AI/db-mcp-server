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
# Description: Discovery cache API routes.
# Related requirements: W28A-871 DM-P-09, DM-CAT-04, DM-S-01, CW-DA2, CW-DA3
# Related tests: UT1.20

"""Discovery API routes for profile-driven data-admin selectors."""

from __future__ import annotations

from fastapi import APIRouter, Request

from cloud_dog_api_kit import success_envelope

from src.core.access_control.schemas import (
    DiscoveryEntitiesRequest,
    DiscoveryFieldsRequest,
    DiscoveryNamespacesRequest,
)


def create_discovery_router(runtime, base_path: str) -> APIRouter:
    """Create discovery cache routes."""
    discovery = runtime.discovery
    router = APIRouter(prefix=base_path, tags=["discovery"])

    @router.post("/admin/discovery/namespaces")
    async def discover_namespaces(payload: DiscoveryNamespacesRequest, request: Request) -> dict:
        return success_envelope(
            discovery.namespaces(
                request,
                profile_id=payload.profile_id,
                connection_name=payload.connection_name,
                refresh=payload.refresh,
                ttl_seconds=payload.ttl_seconds,
            )
        )

    @router.post("/admin/discovery/entities")
    async def discover_entities(payload: DiscoveryEntitiesRequest, request: Request) -> dict:
        return success_envelope(
            discovery.entities(
                request,
                profile_id=payload.profile_id,
                namespace=payload.namespace,
                refresh=payload.refresh,
                ttl_seconds=payload.ttl_seconds,
            )
        )

    @router.post("/admin/discovery/fields")
    async def discover_fields(payload: DiscoveryFieldsRequest, request: Request) -> dict:
        return success_envelope(
            discovery.fields(
                request,
                profile_id=payload.profile_id,
                namespace=payload.namespace,
                entity=payload.entity,
                refresh=payload.refresh,
                ttl_seconds=payload.ttl_seconds,
            )
        )

    return router
