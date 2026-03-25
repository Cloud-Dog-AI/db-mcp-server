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
# Description: Core catalogue MCP tools shared across connector types.
# Related requirements: CD-01, CD-02, CD-03, CN-01
# Related tests: UT1.6, ST1.4, IT1.3

"""Catalogue MCP tool registry."""

from __future__ import annotations

from typing import Any

from cloud_dog_api_kit import ToolContract


def build_catalog_tool_registry(runtime) -> dict[str, ToolContract]:
    """Build catalogue MCP tools using the connector dispatch layer."""
    connectors = runtime.connectors

    async def list_namespaces(payload: dict[str, Any], request) -> dict[str, Any]:
        profile_id = str(payload.get("profile_id", ""))

        def callback(session):
            items = session.connector.list_namespaces()
            return connectors.filter_namespaces(session.profile, items)

        return {
            "items": connectors.execute(
                request,
                profile_id=profile_id,
                permission="catalog.read",
                audit_action="catalog.list_namespaces",
                audit_target_id=profile_id,
                callback=callback,
            )
        }

    async def list_entities(payload: dict[str, Any], request) -> dict[str, Any]:
        profile_id = str(payload.get("profile_id", ""))
        namespace = str(payload.get("namespace", ""))

        def callback(session):
            connectors.ensure_namespace_allowed(session.profile, namespace)
            items = session.connector.list_entities(namespace)
            return connectors.filter_entities(session.profile, namespace, items)

        return {
            "items": connectors.execute(
                request,
                profile_id=profile_id,
                permission="catalog.read",
                audit_action="catalog.list_entities",
                audit_target_id=f"{profile_id}:{namespace}",
                callback=callback,
            )
        }

    async def get_entity(payload: dict[str, Any], request) -> dict[str, Any]:
        profile_id = str(payload.get("profile_id", ""))
        namespace = str(payload.get("namespace", ""))
        entity = str(payload.get("entity", ""))

        def callback(session):
            connectors.ensure_entity_allowed(session.profile, namespace, entity)
            detail = session.connector.describe_entity(namespace, entity)
            fields = session.connector.describe_fields(namespace, entity)
            return {
                **detail,
                "field_count": len(fields.get("fields", [])),
                "fields": fields.get("fields", []),
            }

        return connectors.execute(
            request,
            profile_id=profile_id,
            permission="catalog.read",
            audit_action="catalog.get_entity",
            audit_target_id=f"{profile_id}:{namespace}.{entity}",
            callback=callback,
        )

    async def search(payload: dict[str, Any], request) -> dict[str, Any]:
        profile_id = str(payload.get("profile_id", ""))
        query = str(payload.get("query", "")).strip().lower()

        def callback(session):
            results: list[dict[str, Any]] = []
            namespaces = connectors.filter_namespaces(session.profile, session.connector.list_namespaces())
            for namespace_item in namespaces:
                namespace = str(namespace_item.get("name", ""))
                entities = connectors.filter_entities(session.profile, namespace, session.connector.list_entities(namespace))
                for entity_item in entities:
                    entity = str(entity_item.get("name", ""))
                    fields = session.connector.describe_fields(namespace, entity).get("fields", [])
                    haystacks = [namespace.lower(), entity.lower(), str(entity_item.get("type", "")).lower()]
                    field_hits = [field for field in fields if query in str(field.get("name", "")).lower()]
                    if query and query not in " ".join(haystacks) and not field_hits:
                        continue
                    results.append(
                        {
                            "namespace": namespace,
                            "entity": entity,
                            "entity_type": entity_item.get("type", "collection"),
                            "matched_fields": field_hits,
                        }
                    )
            return results

        return {
            "items": connectors.execute(
                request,
                profile_id=profile_id,
                permission="catalog.read",
                audit_action="catalog.search",
                audit_target_id=profile_id,
                callback=callback,
            )
        }

    return {
        "catalog.list_namespaces": ToolContract(name="catalog.list_namespaces", handler=list_namespaces, description="List namespaces visible to a profile"),
        "catalog.list_entities": ToolContract(name="catalog.list_entities", handler=list_entities, description="List entities visible within a namespace"),
        "catalog.get_entity": ToolContract(name="catalog.get_entity", handler=get_entity, description="Describe an entity in detail"),
        "catalog.search": ToolContract(name="catalog.search", handler=search, description="Search entity and field names within a profile"),
    }
