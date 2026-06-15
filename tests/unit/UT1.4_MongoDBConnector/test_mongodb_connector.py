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
# Description: Unit tests for the MongoDB adapter with a mocked MongoClient.
# Related requirements: CN-01
# Related tests: UT1.4

from __future__ import annotations

import pytest
from bson.binary import Binary

from src.core.connectors.mongodb.adapter import MongoDBConnector

pytestmark = pytest.mark.unit


class FakeIndex(dict):
    pass


class FakeCollection:
    def __init__(self, database=None, name: str = "widgets") -> None:
        self.database = database
        self.name = name
        self.documents = [
            {"_id": "1", "name": "alpha", "owner_id": "u1", "value": 1},
            {"_id": "2", "name": "beta", "owner_id": "u2", "value": 2},
        ]
        self.indexes = [
            FakeIndex({"name": "_id_", "key": {"_id": 1}, "unique": True}),
            FakeIndex({"name": "owner_id_1", "key": {"owner_id": 1}, "unique": False}),
        ]

    def find(self, filter=None, projection=None):
        items = [doc for doc in self.documents if all(doc.get(k) == v for k, v in (filter or {}).items())]
        class Cursor(list):
            def sort(self, items):
                field, direction = items[0]
                reverse = direction == -1
                return Cursor(sorted(self, key=lambda x: x.get(field), reverse=reverse))
            def limit(self, n):
                return Cursor(self[:n])
        rows = []
        for item in items:
            if projection:
                row = {k: v for k, v in item.items() if projection.get(k, 1)}
            else:
                row = dict(item)
            rows.append(row)
        return Cursor(rows)

    def insert_one(self, document):
        doc = dict(document)
        doc.setdefault("_id", str(len(self.documents) + 1))
        self.documents.append(doc)
        class Result:
            inserted_id = doc["_id"]
        return Result()

    def find_one(self, filter):
        for item in self.documents:
            if all(item.get(k) == v for k, v in filter.items()):
                return dict(item)
        return None

    def update_many(self, filter, update):
        matched = 0
        modified = 0
        for item in self.documents:
            if all(item.get(k) == v for k, v in filter.items()):
                matched += 1
                item.update(update.get("$set", {}))
                modified += 1
        class Result:
            matched_count = matched
            modified_count = modified
        return Result()

    def delete_many(self, filter):
        original = len(self.documents)
        self.documents = [item for item in self.documents if not all(item.get(k) == v for k, v in filter.items())]
        class Result:
            deleted_count = original - len(self.documents)
        return Result()

    def count_documents(self, filter):
        return len([doc for doc in self.documents if all(doc.get(k) == v for k, v in (filter or {}).items())])

    def aggregate(self, pipeline):
        size = pipeline[0]["$sample"]["size"]
        return [dict(item) for item in self.documents[:size]]

    def list_indexes(self):
        return list(self.indexes)

    def create_index(self, keys, unique=False, name=None):
        idx_name = name or "generated_idx"
        self.indexes.append(FakeIndex({"name": idx_name, "key": dict(keys), "unique": unique}))
        return idx_name

    def drop_index(self, name):
        self.indexes = [idx for idx in self.indexes if idx["name"] != name]

    def drop(self):
        if self.database is not None:
            self.database.collections.pop(self.name, None)


class FakeDatabase:
    def __init__(self) -> None:
        self.collections = {"widgets": FakeCollection(self, "widgets")}

    def list_collections(self):
        return [{"name": name, "type": "collection"} for name in self.collections]

    def command(self, payload):
        name = payload["filter"]["name"]
        batch = [{"name": name, "options": {}, "info": {}}] if name in self.collections else []
        return {"cursor": {"firstBatch": batch}}

    def __getitem__(self, item):
        return self.collections[item]

    def create_collection(self, name, **_options):
        self.collections[name] = FakeCollection(self, name)
        return self.collections[name]


class FakeAdmin:
    def command(self, _payload):
        return {"ok": 1}


class FakeMongoClient:
    list_database_names_calls = 0

    def __init__(self, *_args, **_kwargs):
        self.databases = {"testdb": FakeDatabase()}
        self.admin = FakeAdmin()

    def list_database_names(self):
        type(self).list_database_names_calls += 1
        return ["admin", "testdb"]

    def __getitem__(self, item):
        return self.databases[item]

    def close(self):
        return None


@pytest.fixture(autouse=True)
def fake_mongo(monkeypatch):
    monkeypatch.setattr("src.core.connectors.mongodb.adapter.MongoClient", FakeMongoClient)
    FakeMongoClient.list_database_names_calls = 0
    MongoDBConnector._namespace_cache.clear()
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-003")


def test_adapter_capabilities_and_catalogue_calls() -> None:
    connector = MongoDBConnector(uri="mongodb://example")
    assert connector.capability_report()["supports"]["structured_read"] is True
    assert connector.validate_profile()["ok"] is True
    assert connector.list_namespaces() == [{"name": "testdb", "type": "database"}]
    assert connector.list_entities("testdb") == [{"name": "widgets", "type": "collection"}]
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-003")


def test_adapter_caches_namespace_listing_per_uri() -> None:
    connector = MongoDBConnector(uri="mongodb://example")

    assert connector.list_namespaces() == [{"name": "testdb", "type": "database"}]
    assert connector.list_namespaces() == [{"name": "testdb", "type": "database"}]
    assert FakeMongoClient.list_database_names_calls == 1
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-003")


def test_adapter_data_and_schema_operations() -> None:
    connector = MongoDBConnector(uri="mongodb://example")
    assert connector.describe_entity("testdb", "widgets")["document_count"] == 2
    assert connector.describe_fields("testdb", "widgets")["sample_count"] == 2
    assert connector.count("testdb", "widgets", {"owner_id": "u1"}) == 1
    inserted = connector.create("testdb", "widgets", {"name": "gamma", "owner_id": "u3"})
    assert inserted["document"]["name"] == "gamma"
    updated = connector.update("testdb", "widgets", {"owner_id": "u3"}, {"$set": {"value": 9}})
    assert updated["matched_count"] == 1
    deleted = connector.delete("testdb", "widgets", {"owner_id": "u3"})
    assert deleted["deleted_count"] == 1
    plan = connector.schema_change_plan({"operation": "create_index", "namespace": "testdb", "entity": "widgets", "keys": [{"field": "name", "direction": "asc"}]})
    assert plan["before_state"]["indexes"]
    assert plan["after_state"]["indexes"][-1]["name"] == "name_asc"
    applied = connector.schema_change_apply(plan)
    assert applied["applied"] is True
    assert connector.extract_relationships("testdb", "widgets")[0]["relationship_type"] == "reference_candidate"
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-003")


def test_adapter_plans_and_applies_entity_lifecycle() -> None:
    connector = MongoDBConnector(uri="mongodb://example")
    create_plan = connector.schema_change_plan(
        {"operation": "create_entity", "namespace": "testdb", "entity": "archive"}
    )
    assert create_plan["before_state"]["entity_exists"] is False
    created = connector.schema_change_apply(create_plan)
    assert created["entity_created"] is True

    drop_plan = connector.schema_change_plan(
        {"operation": "drop_entity", "namespace": "testdb", "entity": "archive"}
    )
    assert drop_plan["before_state"]["entity_exists"] is True
    dropped = connector.schema_change_apply(drop_plan)
    assert dropped["entity_dropped"] is True
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-003")


def test_adapter_normalises_binary_fields_and_preserves_binary_schema_type() -> None:
    connector = MongoDBConnector(uri="mongodb://example")
    inserted = connector.create("testdb", "widgets", {"_id": "bin", "payload": Binary(b"\x00\x01\x02")})
    assert inserted["document"]["payload"] == "000102"

    fields = connector.describe_fields("testdb", "widgets")
    payload_field = next(item for item in fields["fields"] if item["name"] == "payload")
    assert payload_field["types"] == ["binary"]
