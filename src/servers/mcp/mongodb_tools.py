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
# Description: MongoDB MCP tools for catalog, schema, and data operations.
# Related requirements: CN-01, CD-02, SC-01, CO-01, CO-02
# Related tests: IT1.2

"""MongoDB MCP tools for db-mcp-server."""

from __future__ import annotations

from typing import Any

from cloud_dog_api_kit import ToolContract

from src.core.connectors.mongodb import MongoDBConnectorService


def build_mongodb_tool_registry(runtime) -> dict[str, ToolContract]:
    """Return MongoDB-specific MCP tool contracts."""
    service = MongoDBConnectorService(runtime)

    async def catalog_list_namespaces(payload: dict[str, Any], request) -> dict[str, Any]:
        profile_id = str(payload.get('profile_id', ''))
        return {
            'items': service.execute(
                request,
                profile_id=profile_id,
                permission='catalog.read',
                audit_action='catalog.list_namespaces',
                audit_target_id=profile_id,
                callback=lambda connector, _profile: connector.list_namespaces(),
            )
        }

    async def catalog_list_entities(payload: dict[str, Any], request) -> dict[str, Any]:
        profile_id = str(payload.get('profile_id', ''))
        namespace = str(payload.get('namespace', ''))
        return {
            'items': service.execute(
                request,
                profile_id=profile_id,
                permission='catalog.read',
                audit_action='catalog.list_entities',
                audit_target_id=f'{profile_id}:{namespace}',
                callback=lambda connector, _profile: connector.list_entities(namespace),
            )
        }

    async def catalog_get_entity(payload: dict[str, Any], request) -> dict[str, Any]:
        profile_id = str(payload.get('profile_id', ''))
        namespace = str(payload.get('namespace', ''))
        entity = str(payload.get('entity', ''))
        return service.execute(
            request,
            profile_id=profile_id,
            permission='catalog.read',
            audit_action='catalog.get_entity',
            audit_target_id=f'{profile_id}:{namespace}.{entity}',
            callback=lambda connector, _profile: connector.describe_entity(namespace, entity),
        )

    async def schema_describe_entity(payload: dict[str, Any], request) -> dict[str, Any]:
        return await catalog_get_entity(payload, request)

    async def schema_describe_fields(payload: dict[str, Any], request) -> dict[str, Any]:
        profile_id = str(payload.get('profile_id', ''))
        namespace = str(payload.get('namespace', ''))
        entity = str(payload.get('entity', ''))
        return service.execute(
            request,
            profile_id=profile_id,
            permission='schema.read',
            audit_action='schema.describe_fields',
            audit_target_id=f'{profile_id}:{namespace}.{entity}',
            callback=lambda connector, _profile: connector.describe_fields(namespace, entity),
        )

    async def schema_list_indexes(payload: dict[str, Any], request) -> dict[str, Any]:
        profile_id = str(payload.get('profile_id', ''))
        namespace = str(payload.get('namespace', ''))
        entity = str(payload.get('entity', ''))
        return {
            'items': service.execute(
                request,
                profile_id=profile_id,
                permission='schema.read',
                audit_action='schema.list_indexes',
                audit_target_id=f'{profile_id}:{namespace}.{entity}',
                callback=lambda connector, _profile: connector.list_indexes(namespace, entity),
            )
        }

    async def data_read(payload: dict[str, Any], request) -> dict[str, Any]:
        profile_id = str(payload.get('profile_id', ''))
        namespace = str(payload.get('namespace', ''))
        entity = str(payload.get('entity', ''))
        result = service.execute(
            request,
            profile_id=profile_id,
            permission='data.read',
            audit_action='data.read',
            audit_target_id=f'{profile_id}:{namespace}.{entity}',
            callback=lambda connector, _profile: connector.read(
                namespace,
                entity,
                filter=payload.get('filter'),
                projection=payload.get('projection'),
                sort=payload.get('sort'),
                limit=payload.get('limit'),
            ),
        )
        return {'items': result}

    async def data_create(payload: dict[str, Any], request) -> dict[str, Any]:
        profile_id = str(payload.get('profile_id', ''))
        namespace = str(payload.get('namespace', ''))
        entity = str(payload.get('entity', ''))
        return service.execute(
            request,
            profile_id=profile_id,
            permission='data.create',
            audit_action='data.create',
            audit_target_id=f'{profile_id}:{namespace}.{entity}',
            callback=lambda connector, _profile: connector.create(namespace, entity, payload.get('document') or {}),
        )

    async def data_update(payload: dict[str, Any], request) -> dict[str, Any]:
        profile_id = str(payload.get('profile_id', ''))
        namespace = str(payload.get('namespace', ''))
        entity = str(payload.get('entity', ''))
        return service.execute(
            request,
            profile_id=profile_id,
            permission='data.update',
            audit_action='data.update',
            audit_target_id=f'{profile_id}:{namespace}.{entity}',
            callback=lambda connector, _profile: connector.update(
                namespace,
                entity,
                payload.get('filter') or {},
                payload.get('update') or {},
            ),
        )

    async def data_delete(payload: dict[str, Any], request) -> dict[str, Any]:
        profile_id = str(payload.get('profile_id', ''))
        namespace = str(payload.get('namespace', ''))
        entity = str(payload.get('entity', ''))
        return service.execute(
            request,
            profile_id=profile_id,
            permission='data.delete',
            audit_action='data.delete',
            audit_target_id=f'{profile_id}:{namespace}.{entity}',
            callback=lambda connector, _profile: connector.delete(namespace, entity, payload.get('filter') or {}),
        )

    async def data_count(payload: dict[str, Any], request) -> dict[str, Any]:
        profile_id = str(payload.get('profile_id', ''))
        namespace = str(payload.get('namespace', ''))
        entity = str(payload.get('entity', ''))
        result = service.execute(
            request,
            profile_id=profile_id,
            permission='data.read',
            audit_action='data.count',
            audit_target_id=f'{profile_id}:{namespace}.{entity}',
            callback=lambda connector, _profile: connector.count(namespace, entity, payload.get('filter')),
        )
        return {'count': result}

    return {
        'catalog.list_namespaces': ToolContract(name='catalog.list_namespaces', handler=catalog_list_namespaces, description='List MongoDB databases for a profile'),
        'catalog.list_entities': ToolContract(name='catalog.list_entities', handler=catalog_list_entities, description='List MongoDB collections in a database'),
        'catalog.get_entity': ToolContract(name='catalog.get_entity', handler=catalog_get_entity, description='Describe a MongoDB collection'),
        'schema.describe_entity': ToolContract(name='schema.describe_entity', handler=schema_describe_entity, description='Describe MongoDB collection metadata'),
        'schema.describe_fields': ToolContract(name='schema.describe_fields', handler=schema_describe_fields, description='Infer MongoDB field shapes'),
        'schema.list_indexes': ToolContract(name='schema.list_indexes', handler=schema_list_indexes, description='List MongoDB indexes'),
        'data.read': ToolContract(name='data.read', handler=data_read, description='Read MongoDB documents with structured filters'),
        'data.create': ToolContract(name='data.create', handler=data_create, description='Insert MongoDB documents'),
        'data.update': ToolContract(name='data.update', handler=data_update, description='Update MongoDB documents'),
        'data.delete': ToolContract(name='data.delete', handler=data_delete, description='Delete MongoDB documents'),
        'data.count': ToolContract(name='data.count', handler=data_count, description='Count MongoDB documents'),
    }
