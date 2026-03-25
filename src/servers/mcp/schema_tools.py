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
# Description: Core schema MCP tools shared across connector types.
# Related requirements: SC-01, SC-02, CN-01
# Related tests: ST1.6, IT1.3

"""Schema MCP tool registry."""

from __future__ import annotations

from typing import Any

from cloud_dog_api_kit import ToolContract


def build_schema_tool_registry(runtime) -> dict[str, ToolContract]:
    """Build schema MCP tools using the connector dispatch layer."""
    connectors = runtime.connectors
    schema_changes = runtime.schema_changes

    async def describe_entity(payload: dict[str, Any], request) -> dict[str, Any]:
        profile_id = str(payload.get("profile_id", ""))
        namespace = str(payload.get("namespace", ""))
        entity = str(payload.get("entity", ""))

        def callback(session):
            connectors.ensure_entity_allowed(session.profile, namespace, entity)
            entity_detail = session.connector.describe_entity(namespace, entity)
            field_detail = session.connector.describe_fields(namespace, entity)
            return {**entity_detail, "fields": field_detail.get("fields", [])}

        return connectors.execute(
            request,
            profile_id=profile_id,
            permission="schema.read",
            audit_action="schema.describe_entity",
            audit_target_id=f"{profile_id}:{namespace}.{entity}",
            callback=callback,
        )

    async def describe_fields(payload: dict[str, Any], request) -> dict[str, Any]:
        profile_id = str(payload.get("profile_id", ""))
        namespace = str(payload.get("namespace", ""))
        entity = str(payload.get("entity", ""))

        def callback(session):
            connectors.ensure_entity_allowed(session.profile, namespace, entity)
            return session.connector.describe_fields(namespace, entity)

        return connectors.execute(
            request,
            profile_id=profile_id,
            permission="schema.read",
            audit_action="schema.describe_fields",
            audit_target_id=f"{profile_id}:{namespace}.{entity}",
            callback=callback,
        )

    async def list_indexes(payload: dict[str, Any], request) -> dict[str, Any]:
        profile_id = str(payload.get("profile_id", ""))
        namespace = str(payload.get("namespace", ""))
        entity = str(payload.get("entity", ""))

        def callback(session):
            connectors.ensure_entity_allowed(session.profile, namespace, entity)
            return session.connector.list_indexes(namespace, entity)

        return {
            "items": connectors.execute(
                request,
                profile_id=profile_id,
                permission="schema.read",
                audit_action="schema.list_indexes",
                audit_target_id=f"{profile_id}:{namespace}.{entity}",
                callback=callback,
            )
        }

    async def sample_shapes(payload: dict[str, Any], request) -> dict[str, Any]:
        profile_id = str(payload.get("profile_id", ""))
        namespace = str(payload.get("namespace", ""))
        entity = str(payload.get("entity", ""))
        count = int(payload.get("count", 5) or 5)

        def callback(session):
            connectors.ensure_entity_allowed(session.profile, namespace, entity)
            return session.connector.sample_shapes(namespace, entity, n=count)

        return {
            "items": connectors.execute(
                request,
                profile_id=profile_id,
                permission="schema.read",
                audit_action="schema.sample_shapes",
                audit_target_id=f"{profile_id}:{namespace}.{entity}",
                callback=callback,
            )
        }

    async def change_plan(payload: dict[str, Any], request) -> dict[str, Any]:
        profile_id = str(payload.get("profile_id", ""))
        return schema_changes.plan_change(request, profile_id=profile_id, payload=payload)

    async def change_apply(payload: dict[str, Any], request) -> dict[str, Any]:
        profile_id = str(payload.get("profile_id", ""))
        return schema_changes.apply_change(request, profile_id=profile_id, payload=payload)

    async def change_history(payload: dict[str, Any], request) -> dict[str, Any]:
        profile_id = str(payload.get("profile_id", "")).strip() or None
        limit = int(payload.get("limit", 20) or 20)
        status = str(payload.get("status", "")).strip() or None
        return schema_changes.history(request, profile_id=profile_id, limit=limit, status=status)

    return {
        "schema.describe_entity": ToolContract(name="schema.describe_entity", handler=describe_entity, description="Describe an entity schema"),
        "schema.describe_fields": ToolContract(name="schema.describe_fields", handler=describe_fields, description="Describe per-field schema detail"),
        "schema.list_indexes": ToolContract(name="schema.list_indexes", handler=list_indexes, description="List entity indexes"),
        "schema.sample_shapes": ToolContract(name="schema.sample_shapes", handler=sample_shapes, description="Sample entity document shapes"),
        "schema.change.plan": ToolContract(name="schema.change.plan", handler=change_plan, description="Plan a dry-run schema change"),
        "schema.change.apply": ToolContract(name="schema.change.apply", handler=change_apply, description="Apply a planned schema change"),
        "schema.change.history": ToolContract(name="schema.change.history", handler=change_history, description="List recent schema changes with audit trail"),
    }
