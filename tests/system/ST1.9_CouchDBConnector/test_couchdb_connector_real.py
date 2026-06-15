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
# Description: System test for the CouchDB adapter against a real local CouchDB 3 runtime.
# Related requirements: CN-01
# Related tests: ST1.9

from __future__ import annotations

import time
from urllib.parse import urlparse, urlunparse

import pytest
import requests

from src.core.connectors.couchdb.adapter import CouchDBConnector
from tests.helpers.couchdb_runtime import cleanup_database, ensure_real_couchdb

pytestmark = [pytest.mark.system, pytest.mark.timeout(180)]


def _session(uri: str) -> requests.Session:
    session = requests.Session()
    parsed = urlparse(uri)
    if parsed.username:
        session.auth = (parsed.username, parsed.password or "")
    session.headers.update({"Content-Type": "application/json"})
    return session


def _public_url(uri: str) -> str:
    parsed = urlparse(uri)
    netloc = parsed.hostname or ""
    if parsed.port:
        netloc = f"{netloc}:{parsed.port}"
    return urlunparse((parsed.scheme, netloc, parsed.path, "", "", "")).rstrip("/")
@pytest.mark.ST
@pytest.mark.mcp
@pytest.mark.req("FR-006")


def test_couchdb_adapter_against_real_local_couchdb() -> None:
    """CouchDB adapter methods should work against a real local CouchDB runtime."""
    uri = ensure_real_couchdb()
    base_url = _public_url(uri)
    db_name = f"dbmcp_st_{int(time.time())}"
    session = _session(uri)
    try:
        response = session.put(f"{base_url}/{db_name}", timeout=10)
        response.raise_for_status()
        design_doc = {
            "_id": "_design/common",
            "views": {
                "by_status": {
                    "map": "function(doc){ if(doc.status){ emit(doc.status, null); } }",
                }
            },
        }
        bulk = {
            "docs": [
                design_doc,
                {"_id": "1", "doc_type": "widgets", "name": "alpha", "owner_id": "u1", "status": "active", "value": 1},
                {"_id": "2", "doc_type": "widgets", "name": "beta", "owner_id": "u2", "status": "inactive", "value": 2},
            ]
        }
        response = session.post(f"{base_url}/{db_name}/_bulk_docs", json=bulk, timeout=10)
        response.raise_for_status()

        connector = CouchDBConnector(uri=uri)
        namespaces = connector.list_namespaces()
        assert any(item["name"] == db_name for item in namespaces)
        entities = connector.list_entities(db_name)
        assert any(item["name"] == "widgets" for item in entities)
        assert any(item["name"] == "common/by_status" for item in entities)
        fields = connector.describe_fields(db_name, "widgets")
        assert any(item["name"] == "owner_id" for item in fields["fields"])
        created = connector.create(db_name, "widgets", {"name": "gamma", "owner_id": "u3", "value": 3})
        assert created["document"]["doc_type"] == "widgets"
        rows = connector.read(db_name, "widgets", {"owner_id": "u3"}, limit=5)
        assert len(rows) == 1
        updated = connector.update(db_name, "widgets", {"owner_id": "u3"}, {"$set": {"value": 9}})
        assert updated["modified_count"] == 1
        assert connector.count(db_name, "widgets", {"owner_id": "u3"}) == 1
        relationships = connector.extract_relationships(db_name, "widgets")
        assert any(item["field"] == "owner_id" for item in relationships)
        plan = connector.schema_change_plan(
            {
                "operation": "create_index",
                "namespace": db_name,
                "entity": "widgets",
                "keys": [{"field": "name", "direction": "asc"}],
            }
        )
        applied = connector.schema_change_apply(plan)
        assert applied["index_name"] == "name_asc"
        indexes = connector.list_indexes(db_name, "widgets")
        assert any(item["name"] == "name_asc" for item in indexes)
        deleted = connector.delete(db_name, "widgets", {"owner_id": "u3"})
        assert deleted["deleted_count"] == 1
    finally:
        session.close()
        cleanup_database(db_name)
