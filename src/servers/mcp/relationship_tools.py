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
# Description: Relationship MCP tools backed by metadata persistence.
# Related requirements: RL-01, RL-02, RL-03
# Related tests: UT1.8, IT1.5

"""Relationship MCP tool registry."""

from __future__ import annotations

from typing import Any

from cloud_dog_api_kit import ToolContract


def build_relationship_tool_registry(runtime) -> dict[str, ToolContract]:
    """Build relationship MCP tools."""
    relationships = runtime.relationships

    async def relationship_list(payload: dict[str, Any], request) -> dict[str, Any]:
        return {
            "items": relationships.list(
                request,
                profile_id=str(payload.get("profile_id", "")),
                namespace=str(payload.get("namespace", "")),
                entity=str(payload.get("entity", "")),
            )
        }

    async def relationship_get(payload: dict[str, Any], request) -> dict[str, Any]:
        return relationships.get(request, relationship_id=str(payload.get("relationship_id", "")))

    async def relationship_infer(payload: dict[str, Any], request) -> dict[str, Any]:
        return {
            "items": relationships.infer(
                request,
                profile_id=str(payload.get("profile_id", "")),
                namespace=str(payload.get("namespace", "")),
                entity=str(payload.get("entity", "")),
            )
        }

    async def relationship_create(payload: dict[str, Any], request) -> dict[str, Any]:
        return relationships.create(request, payload)

    async def relationship_update(payload: dict[str, Any], request) -> dict[str, Any]:
        relationship_id = str(payload.get("relationship_id", ""))
        update_payload = dict(payload)
        update_payload.pop("relationship_id", None)
        return relationships.update(request, relationship_id, update_payload)

    async def relationship_delete(payload: dict[str, Any], request) -> dict[str, Any]:
        return relationships.delete(request, relationship_id=str(payload.get("relationship_id", "")))

    return {
        "relationship.list": ToolContract(name="relationship.list", handler=relationship_list, description="List persisted relationships for an entity"),
        "relationship.get": ToolContract(name="relationship.get", handler=relationship_get, description="Get a single relationship by id"),
        "relationship.infer": ToolContract(name="relationship.infer", handler=relationship_infer, description="Infer relationship candidates from source data"),
        "relationship.create": ToolContract(name="relationship.create", handler=relationship_create, description="Create a curated relationship"),
        "relationship.update": ToolContract(name="relationship.update", handler=relationship_update, description="Update relationship metadata"),
        "relationship.delete": ToolContract(name="relationship.delete", handler=relationship_delete, description="Delete a relationship"),
    }
