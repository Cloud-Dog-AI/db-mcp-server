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
# Description: Unit tests for structured content MCP tools and filter translation.
# Related requirements: CO-01, CO-02, CN-01
# Related tests: UT1.7

from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.core.filters import MongoDBFilterTranslator
from src.servers.mcp.content_tools import build_content_tool_registry

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


class _FakeConnector:
    def __init__(self) -> None:
        self.last_filter = None

    def read(self, namespace, entity, filter=None, projection=None, sort=None, limit=None):
        self.last_filter = filter
        return [
            {"name": "Widget A", "secret": "top"},
            {"name": "Widget B", "secret": "top"},
        ]

    def create(self, namespace, entity, document):
        return {"inserted_id": document.get("_id", "x"), "document": dict(document)}

    def update(self, namespace, entity, filter, update):
        self.last_filter = filter
        return {"matched_count": 1, "modified_count": 1}

    def delete(self, namespace, entity, filter):
        self.last_filter = filter
        return {"deleted_count": 1}

    def count(self, namespace, entity, filter=None):
        self.last_filter = filter
        return 1


class _FakeConnectors:
    def __init__(self) -> None:
        self.connector = _FakeConnector()

    def execute(self, _request, *, callback, **_kwargs):
        session = SimpleNamespace(profile={}, connector=self.connector, translator=MongoDBFilterTranslator())
        return callback(session)

    def ensure_entity_allowed(self, _profile, _namespace, _entity):
        return None

    def mask_record(self, _profile_id, record):
        record = dict(record)
        record["secret"] = "***"
        return record

    def mask_records(self, profile_id, records):
        return [self.mask_record(profile_id, item) for item in records]


async def test_content_tools_translate_filters_and_mask_results() -> None:
    runtime = SimpleNamespace(connectors=_FakeConnectors())
    tools = build_content_tool_registry(runtime)

    read = await tools["data.read"].handler(
        {
            "profile_id": "p1",
            "namespace": "alpha",
            "entity": "widgets",
            "filter": {"field": "quantity", "operator": "gte", "value": 10},
            "limit": 1,
        },
        SimpleNamespace(),
    )
    assert read["items"][0]["secret"] == "***"
    assert runtime.connectors.connector.last_filter == {"quantity": {"$gte": 10}}

    created = await tools["data.create"].handler(
        {
            "profile_id": "p1",
            "namespace": "alpha",
            "entity": "widgets",
            "documents": [{"_id": "A1", "name": "Widget A", "secret": "top"}],
        },
        SimpleNamespace(),
    )
    assert created["documents"][0]["secret"] == "***"

    exists = await tools["data.exists"].handler(
        {"profile_id": "p1", "namespace": "alpha", "entity": "widgets", "filter": {"status": "active"}},
        SimpleNamespace(),
    )
    assert exists == {"exists": True, "count": 1}
