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
# Description: Unit tests for connector-agnostic catalogue MCP tools.
# Related requirements: CD-01, CD-02, CD-03, CN-01
# Related tests: UT1.6

from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.servers.mcp.catalog_tools import build_catalog_tool_registry

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


class _FakeConnector:
    def list_namespaces(self):
        return [{"name": "alpha", "type": "database"}, {"name": "beta", "type": "database"}]

    def list_entities(self, namespace):
        return [{"name": "customers", "type": "collection"}, {"name": "orders", "type": "collection"}]

    def describe_entity(self, namespace, entity):
        return {"namespace": namespace, "entity": entity, "document_count": 2, "indexes": [{"name": "_id_"}]}

    def describe_fields(self, namespace, entity):
        return {"fields": [{"name": "customer_id", "types": ["str"]}, {"name": "status", "types": ["str"]}]}


class _FakeConnectors:
    def execute(self, _request, *, callback, **_kwargs):
        session = SimpleNamespace(profile={"namespaces": ["alpha"], "entities": ["alpha.customers", "alpha.orders"]}, connector=_FakeConnector())
        return callback(session)

    def filter_namespaces(self, _profile, namespaces):
        return [item for item in namespaces if item["name"] == "alpha"]

    def filter_entities(self, _profile, _namespace, entities):
        return entities

    def ensure_namespace_allowed(self, _profile, _namespace):
        return None

    def ensure_entity_allowed(self, _profile, _namespace, _entity):
        return None


async def test_catalog_tools_list_and_search() -> None:
    runtime = SimpleNamespace(connectors=_FakeConnectors())
    tools = build_catalog_tool_registry(runtime)

    namespaces = await tools["catalog.list_namespaces"].handler({"profile_id": "p1"}, SimpleNamespace())
    assert namespaces["items"] == [{"name": "alpha", "type": "database"}]

    entity = await tools["catalog.get_entity"].handler({"profile_id": "p1", "namespace": "alpha", "entity": "customers"}, SimpleNamespace())
    assert entity["field_count"] == 2

    search = await tools["catalog.search"].handler({"profile_id": "p1", "query": "customer"}, SimpleNamespace())
    assert search["items"][0]["entity"] == "customers"
    assert search["items"][0]["matched_fields"][0]["name"] == "customer_id"
