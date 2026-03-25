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
# Description: Core content MCP tools shared across connector types.
# Related requirements: CO-01, CO-02, NF-01, CN-01
# Related tests: UT1.7, ST1.5, IT1.3, IT1.4

"""Content MCP tool registry."""

from __future__ import annotations

from typing import Any

from cloud_dog_api_kit import ToolContract

from src.core.filters import parse_filter


def build_content_tool_registry(runtime) -> dict[str, ToolContract]:
    """Build content MCP tools using structured filters and connector dispatch."""
    connectors = runtime.connectors

    async def data_read(payload: dict[str, Any], request) -> dict[str, Any]:
        profile_id = str(payload.get("profile_id", ""))
        namespace = str(payload.get("namespace", ""))
        entity = str(payload.get("entity", ""))
        limit = int(payload.get("limit", 50) or 50)
        offset = int(payload.get("offset", 0) or 0)

        def callback(session):
            connectors.ensure_entity_allowed(session.profile, namespace, entity)
            filter_query = session.translator.translate(parse_filter(payload.get("filter")))
            fetch_limit = limit + offset if limit > 0 else None
            rows = session.connector.read(
                namespace,
                entity,
                filter=filter_query,
                projection=payload.get("projection"),
                sort=payload.get("sort"),
                limit=fetch_limit,
            )
            page = rows[offset: offset + limit if limit > 0 else None]
            return {
                "items": connectors.mask_records(profile_id, page),
                "offset": offset,
                "limit": limit,
            }

        return connectors.execute(
            request,
            profile_id=profile_id,
            permission="data.read",
            audit_action="data.read",
            audit_target_id=f"{profile_id}:{namespace}.{entity}",
            callback=callback,
        )

    async def data_create(payload: dict[str, Any], request) -> dict[str, Any]:
        profile_id = str(payload.get("profile_id", ""))
        namespace = str(payload.get("namespace", ""))
        entity = str(payload.get("entity", ""))

        def callback(session):
            connectors.ensure_entity_allowed(session.profile, namespace, entity)
            bulk_mode = "documents" in payload
            documents = payload.get("documents")
            if documents is None:
                documents = [payload.get("document") or {}]
            created = [session.connector.create(namespace, entity, item) for item in list(documents)]
            if len(created) == 1 and not bulk_mode:
                single = created[0]
                single["document"] = connectors.mask_record(profile_id, single.get("document", {}))
                return single
            return {
                "inserted_count": len(created),
                "documents": connectors.mask_records(profile_id, [item.get("document", {}) for item in created]),
            }

        return connectors.execute(
            request,
            profile_id=profile_id,
            permission="data.create",
            audit_action="data.create",
            audit_target_id=f"{profile_id}:{namespace}.{entity}",
            callback=callback,
        )

    async def data_update(payload: dict[str, Any], request) -> dict[str, Any]:
        profile_id = str(payload.get("profile_id", ""))
        namespace = str(payload.get("namespace", ""))
        entity = str(payload.get("entity", ""))

        def callback(session):
            connectors.ensure_entity_allowed(session.profile, namespace, entity)
            filter_query = session.translator.translate(parse_filter(payload.get("filter")))
            return session.connector.update(namespace, entity, filter_query, payload.get("update") or {})

        return connectors.execute(
            request,
            profile_id=profile_id,
            permission="data.update",
            audit_action="data.update",
            audit_target_id=f"{profile_id}:{namespace}.{entity}",
            callback=callback,
        )

    async def data_delete(payload: dict[str, Any], request) -> dict[str, Any]:
        profile_id = str(payload.get("profile_id", ""))
        namespace = str(payload.get("namespace", ""))
        entity = str(payload.get("entity", ""))

        def callback(session):
            connectors.ensure_entity_allowed(session.profile, namespace, entity)
            filter_query = session.translator.translate(parse_filter(payload.get("filter")))
            return session.connector.delete(namespace, entity, filter_query)

        return connectors.execute(
            request,
            profile_id=profile_id,
            permission="data.delete",
            audit_action="data.delete",
            audit_target_id=f"{profile_id}:{namespace}.{entity}",
            callback=callback,
        )

    async def data_count(payload: dict[str, Any], request) -> dict[str, Any]:
        profile_id = str(payload.get("profile_id", ""))
        namespace = str(payload.get("namespace", ""))
        entity = str(payload.get("entity", ""))

        def callback(session):
            connectors.ensure_entity_allowed(session.profile, namespace, entity)
            filter_query = session.translator.translate(parse_filter(payload.get("filter")))
            return {"count": session.connector.count(namespace, entity, filter_query)}

        return connectors.execute(
            request,
            profile_id=profile_id,
            permission="data.read",
            audit_action="data.count",
            audit_target_id=f"{profile_id}:{namespace}.{entity}",
            callback=callback,
        )

    async def data_exists(payload: dict[str, Any], request) -> dict[str, Any]:
        profile_id = str(payload.get("profile_id", ""))
        namespace = str(payload.get("namespace", ""))
        entity = str(payload.get("entity", ""))

        def callback(session):
            connectors.ensure_entity_allowed(session.profile, namespace, entity)
            filter_query = session.translator.translate(parse_filter(payload.get("filter")))
            count = session.connector.count(namespace, entity, filter_query)
            return {"exists": count > 0, "count": count}

        return connectors.execute(
            request,
            profile_id=profile_id,
            permission="data.read",
            audit_action="data.exists",
            audit_target_id=f"{profile_id}:{namespace}.{entity}",
            callback=callback,
        )

    return {
        "data.read": ToolContract(name="data.read", handler=data_read, description="Read content using the structured filter model"),
        "data.create": ToolContract(name="data.create", handler=data_create, description="Insert one or more content records"),
        "data.update": ToolContract(name="data.update", handler=data_update, description="Update content records matching a structured filter"),
        "data.delete": ToolContract(name="data.delete", handler=data_delete, description="Delete content records matching a structured filter"),
        "data.count": ToolContract(name="data.count", handler=data_count, description="Count content records matching a structured filter"),
        "data.exists": ToolContract(name="data.exists", handler=data_exists, description="Check whether any content matches a structured filter"),
    }
