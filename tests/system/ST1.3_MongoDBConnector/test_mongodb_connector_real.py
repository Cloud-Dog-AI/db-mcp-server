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
# Description: System test for the MongoDB adapter against a real local MongoDB 6 runtime.
# Related requirements: CN-01
# Related tests: ST1.3

from __future__ import annotations

import time

import pytest
from pymongo import MongoClient

from src.core.connectors.mongodb.adapter import MongoDBConnector
from tests.helpers.mongo_runtime import cleanup_database, ensure_real_mongodb

pytestmark = [pytest.mark.system, pytest.mark.timeout(180)]


def test_mongodb_adapter_against_real_local_mongo() -> None:
    """MongoDB adapter methods should work against a real local MongoDB runtime."""
    uri = ensure_real_mongodb()
    db_name = f"dbmcp_st_{int(time.time())}"
    client = MongoClient(uri, serverSelectionTimeoutMS=3000)
    try:
        client[db_name]["widgets"].insert_many(
            [
                {"name": "alpha", "owner_id": "u1", "value": 1},
                {"name": "beta", "owner_id": "u2", "value": 2},
            ]
        )
        connector = MongoDBConnector(uri=uri)
        namespaces = connector.list_namespaces()
        assert any(item["name"] == db_name for item in namespaces)
        entities = connector.list_entities(db_name)
        assert any(item["name"] == "widgets" for item in entities)
        fields = connector.describe_fields(db_name, "widgets")
        assert any(item["name"] == "owner_id" for item in fields["fields"])
        indexes = connector.list_indexes(db_name, "widgets")
        assert any(item["name"] == "_id_" for item in indexes)
        created = connector.create(db_name, "widgets", {"name": "gamma", "owner_id": "u3", "value": 3})
        assert created["document"]["name"] == "gamma"
        rows = connector.read(db_name, "widgets", {"owner_id": "u3"}, limit=5)
        assert len(rows) == 1
        updated = connector.update(db_name, "widgets", {"owner_id": "u3"}, {"$set": {"value": 9}})
        assert updated["modified_count"] == 1
        assert connector.count(db_name, "widgets", {"owner_id": "u3"}) == 1
        relationships = connector.extract_relationships(db_name, "widgets")
        assert any(item["field"] == "owner_id" for item in relationships)
        deleted = connector.delete(db_name, "widgets", {"owner_id": "u3"})
        assert deleted["deleted_count"] == 1
    finally:
        client.close()
        cleanup_database(db_name)
