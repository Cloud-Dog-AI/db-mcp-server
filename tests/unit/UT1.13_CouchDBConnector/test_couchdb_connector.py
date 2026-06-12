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
# Description: Unit tests for the CouchDB adapter with a mocked HTTP session.
# Related requirements: CN-01
# Tests: CN-02
# Related tests: UT1.13

from __future__ import annotations

from copy import deepcopy
import json as jsonlib
from urllib.parse import parse_qs, unquote, urlparse

import pytest

from src.core.connectors.couchdb.adapter import CouchDBConnector

pytestmark = pytest.mark.unit


class FakeResponse:
    def __init__(self, *, status_code: int, payload) -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = jsonlib.dumps(payload)

    def json(self):
        return deepcopy(self._payload)

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            import requests

            error = requests.HTTPError(f"HTTP {self.status_code}")
            error.response = self
            raise error


class FakeSession:
    def __init__(self) -> None:
        self.auth = None
        self.headers = {}
        self.databases = {
            "testdb": {
                "docs": {
                    "_design/common": {
                        "_id": "_design/common",
                        "_rev": "1-design",
                        "views": {
                            "by_status": {
                                "map": "function(doc){ if(doc.status){ emit(doc.status, null); } }",
                            }
                        },
                    },
                    "1": {
                        "_id": "1",
                        "_rev": "1-a",
                        "doc_type": "widgets",
                        "name": "alpha",
                        "owner_id": "u1",
                        "status": "active",
                        "value": 1,
                    },
                    "2": {
                        "_id": "2",
                        "_rev": "1-b",
                        "doc_type": "widgets",
                        "name": "beta",
                        "owner_id": "u2",
                        "status": "inactive",
                        "value": 2,
                    },
                },
                "indexes": [
                    {
                        "ddoc": None,
                        "name": "_all_docs",
                        "type": "special",
                        "def": {"fields": [{"_id": "asc"}]},
                    }
                ],
            }
        }

    def request(self, method: str, url: str, timeout: int = 30, params=None, json=None, **_kwargs):
        _ = timeout
        parsed = urlparse(url)
        path_parts = [unquote(part) for part in parsed.path.split("/") if part]
        query = parse_qs(parsed.query)
        if params:
            for key, value in params.items():
                query[key] = [str(value)]

        if path_parts == ["_up"] and method == "GET":
            return FakeResponse(status_code=200, payload={"status": "ok"})
        if path_parts == ["_all_dbs"] and method == "GET":
            return FakeResponse(status_code=200, payload=["_users", "testdb"])

        if not path_parts:
            return FakeResponse(status_code=200, payload={"couchdb": "Welcome"})

        database = self.databases[path_parts[0]]
        docs = database["docs"]

        if len(path_parts) == 2 and path_parts[1] == "_all_docs" and method == "GET":
            include_docs = query.get("include_docs", ["false"])[0] == "true"
            startkey = jsonlib.loads(query["startkey"][0]) if "startkey" in query else None
            endkey = jsonlib.loads(query["endkey"][0]) if "endkey" in query else None
            rows = []
            for doc_id in sorted(docs.keys()):
                if startkey is not None and doc_id < startkey:
                    continue
                if endkey is not None and doc_id > endkey:
                    continue
                row = {"id": doc_id, "key": doc_id, "value": {"rev": docs[doc_id].get("_rev", "1")}}
                if include_docs:
                    row["doc"] = deepcopy(docs[doc_id])
                rows.append(row)
            return FakeResponse(status_code=200, payload={"rows": rows})

        if len(path_parts) == 2 and path_parts[1] == "_index" and method == "GET":
            return FakeResponse(status_code=200, payload={"indexes": deepcopy(database["indexes"])})
        if len(path_parts) == 2 and path_parts[1] == "_index" and method == "POST":
            payload = {
                "ddoc": f"_design/{json['name']}",
                "name": json["name"],
                "type": json.get("type", "json"),
                "def": deepcopy(json["index"]),
            }
            database["indexes"].append(payload)
            return FakeResponse(status_code=200, payload={"id": payload["ddoc"], "name": payload["name"], "result": "created"})
        if len(path_parts) == 5 and path_parts[1] == "_index" and method == "DELETE":
            _ddoc = unquote(path_parts[2])
            _type = path_parts[3]
            name = unquote(path_parts[4])
            database["indexes"] = [item for item in database["indexes"] if item.get("name") != name]
            return FakeResponse(status_code=200, payload={"ok": True})

        if len(path_parts) == 5 and path_parts[1] == "_design" and path_parts[3] == "_view" and method == "GET":
            view_name = path_parts[4]
            rows = []
            for item in docs.values():
                if item.get("_id", "").startswith("_design/"):
                    continue
                rows.append({"id": item["_id"], "key": item.get("status"), "doc": deepcopy(item)})
            return FakeResponse(status_code=200, payload={"total_rows": len(rows), "rows": rows, "view": view_name})

        if len(path_parts) == 1 and method == "POST":
            next_id = str(max(int(doc_id) for doc_id in docs if not doc_id.startswith("_design/")) + 1)
            created = deepcopy(json)
            created.setdefault("_id", next_id)
            created.setdefault("_rev", f"1-{created['_id']}")
            docs[created["_id"]] = created
            return FakeResponse(status_code=201, payload={"ok": True, "id": created["_id"]})

        if len(path_parts) == 2 and method == "GET":
            return FakeResponse(status_code=200, payload=deepcopy(docs[path_parts[1]]))
        if len(path_parts) == 2 and method == "PUT":
            doc_id = path_parts[1]
            updated = deepcopy(json)
            current_rev = docs.get(doc_id, {}).get("_rev", "0")
            rev_number = int(str(current_rev).split("-", 1)[0]) + 1
            updated.setdefault("_id", doc_id)
            updated["_rev"] = f"{rev_number}-{doc_id}"
            docs[doc_id] = updated
            return FakeResponse(status_code=201, payload={"ok": True, "id": doc_id, "rev": updated["_rev"]})
        if len(path_parts) == 2 and method == "DELETE":
            docs.pop(path_parts[1], None)
            return FakeResponse(status_code=200, payload={"ok": True})

        raise AssertionError(f"Unhandled request: {method} {url} params={params} json={json}")

    def close(self) -> None:
        return None


@pytest.fixture(autouse=True)
def fake_session(monkeypatch):
    monkeypatch.setattr("src.core.connectors.couchdb.adapter.requests.Session", FakeSession)
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.probe  # rtt-2026-06-12 INST3: KEEP-AS-PROBE pending operator REQ-binding


def test_adapter_capabilities_and_catalogue_calls() -> None:
    connector = CouchDBConnector(uri="http://admin:cloud-dog-test@example")
    assert connector.capability_report()["supports"]["structured_read"] is True
    assert connector.validate_profile()["ok"] is True
    assert connector.list_namespaces() == [{"name": "testdb", "type": "database"}]
    entities = connector.list_entities("testdb")
    assert {item["name"] for item in entities} >= {"_documents", "widgets", "common/by_status"}
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.probe  # rtt-2026-06-12 INST3: KEEP-AS-PROBE pending operator REQ-binding


def test_adapter_data_and_schema_operations() -> None:
    connector = CouchDBConnector(uri="http://admin:cloud-dog-test@example")
    assert connector.describe_entity("testdb", "widgets")["document_count"] == 2
    assert connector.describe_fields("testdb", "widgets")["sample_count"] == 2
    assert connector.count("testdb", "widgets", {"owner_id": "u1"}) == 1
    inserted = connector.create("testdb", "widgets", {"name": "gamma", "owner_id": "u3"})
    assert inserted["document"]["doc_type"] == "widgets"
    updated = connector.update("testdb", "widgets", {"owner_id": "u3"}, {"$set": {"value": 9}})
    assert updated["matched_count"] == 1
    deleted = connector.delete("testdb", "widgets", {"owner_id": "u3"})
    assert deleted["deleted_count"] == 1
    plan = connector.schema_change_plan(
        {
            "operation": "create_index",
            "namespace": "testdb",
            "entity": "widgets",
            "keys": [{"field": "name", "direction": "asc"}],
        }
    )
    assert plan["after_state"]["indexes"][-1]["name"] == "name_asc"
    applied = connector.schema_change_apply(plan)
    assert applied["applied"] is True
    create_entity = connector.schema_change_plan(
        {"operation": "create_entity", "namespace": "testdb", "entity": "archive"}
    )
    assert create_entity["after_state"]["entity_exists"] is True
    connector.schema_change_apply(create_entity)
    assert any(item["name"] == "archive" for item in connector.list_entities("testdb"))
    drop_entity = connector.schema_change_plan(
        {"operation": "drop_entity", "namespace": "testdb", "entity": "archive"}
    )
    dropped = connector.schema_change_apply(drop_entity)
    assert dropped["entity_dropped"] is True
    assert connector.extract_relationships("testdb", "widgets")[0]["relationship_type"] == "reference_candidate"
