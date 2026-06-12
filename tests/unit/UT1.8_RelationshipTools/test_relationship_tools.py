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
# Description: Unit tests for relationship MCP tools.
# Related requirements: RL-01, RL-02, RL-03
# Related tests: UT1.8

from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.servers.mcp.relationship_tools import build_relationship_tool_registry

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


class _FakeRelationships:
    def list(self, request, *, profile_id, namespace, entity):
        return [{"relationship_id": "r1", "field": "customer_id", "target_entity": "customers"}]

    def get(self, request, *, relationship_id):
        return {"relationship_id": relationship_id, "field": "customer_id"}

    def infer(self, request, *, profile_id, namespace, entity):
        return [{"relationship_id": "r2", "field": "supplier_id", "target_entity": "suppliers"}]

    def create(self, request, payload):
        return {"relationship_id": "r3", **payload}

    def update(self, request, relationship_id, payload):
        return {"relationship_id": relationship_id, **payload}

    def delete(self, request, relationship_id):
        return {"deleted": True, "relationship_id": relationship_id}
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.probe  # rtt-2026-06-12 INST3: KEEP-AS-PROBE pending operator REQ-binding


async def test_relationship_tools_cover_crud_and_inference() -> None:
    runtime = SimpleNamespace(relationships=_FakeRelationships())
    tools = build_relationship_tool_registry(runtime)

    listed = await tools["relationship.list"].handler({"profile_id": "p1", "namespace": "alpha", "entity": "orders"}, SimpleNamespace())
    assert listed["items"][0]["field"] == "customer_id"

    inferred = await tools["relationship.infer"].handler({"profile_id": "p1", "namespace": "alpha", "entity": "products"}, SimpleNamespace())
    assert inferred["items"][0]["target_entity"] == "suppliers"

    created = await tools["relationship.create"].handler({"profile_id": "p1", "namespace": "alpha", "entity": "orders", "field": "customer_id", "target_entity": "customers"}, SimpleNamespace())
    assert created["relationship_id"] == "r3"

    deleted = await tools["relationship.delete"].handler({"relationship_id": "r3"}, SimpleNamespace())
    assert deleted == {"deleted": True, "relationship_id": "r3"}
