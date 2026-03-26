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
# Description: Unit tests for the Elasticsearch adapter with a mocked client.
# Related requirements: CN-01
# Related tests: UT1.16

from __future__ import annotations

from copy import deepcopy

import pytest

from src.core.connectors.elasticsearch.adapter import ElasticsearchConnector

pytestmark = pytest.mark.unit


class FakeIndicesClient:
    """In-memory index store for unit testing."""

    def __init__(self) -> None:
        self.indices = {
            "widgets": {
                "mappings": {
                    "properties": {
                        "name": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                        "owner_id": {"type": "keyword"},
                        "status": {"type": "keyword"},
                        "value": {"type": "integer"},
                    }
                },
                "aliases": {"widgets_current": {}},
                "documents": {
                    "1": {"name": "alpha", "owner_id": "u1", "status": "active", "value": 1},
                    "2": {"name": "beta", "owner_id": "u2", "status": "inactive", "value": 2},
                },
            }
        }
        self.templates: dict[str, dict[str, object]] = {}

    def get(self, *, index: str = "*", **_kwargs):
        if index == "*":
            return {name: {} for name in self.indices}
        if index not in self.indices:
            raise KeyError(index)
        return {index: {}}

    def get_alias(self, *, index: str = "*", **_kwargs):
        if index == "*":
            return {
                name: {"aliases": deepcopy(payload["aliases"])}
                for name, payload in self.indices.items()
            }
        if index in self.indices:
            return {index: {"aliases": deepcopy(self.indices[index]["aliases"])}}
        alias_targets = {
            name: {"aliases": {index: {}}}
            for name, payload in self.indices.items()
            if index in payload["aliases"]
        }
        if alias_targets:
            return alias_targets
        raise KeyError(index)

    def get_mapping(self, *, index: str, **_kwargs):
        targets = [index] if index in self.indices else [
            name for name, payload in self.indices.items() if index in payload["aliases"]
        ]
        if not targets:
            raise KeyError(index)
        return {
            name: {"mappings": deepcopy(self.indices[name]["mappings"])}
            for name in targets
        }

    def create(self, *, index: str, body=None, **_kwargs):
        mappings = deepcopy((body or {}).get("mappings") or {})
        aliases = deepcopy((body or {}).get("aliases") or {})
        self.indices[index] = {"mappings": mappings, "aliases": aliases, "documents": {}}
        return {"acknowledged": True}

    def delete(self, *, index: str, **_kwargs):
        self.indices.pop(index, None)
        return {"acknowledged": True}

    def delete_alias(self, *, index: str, name: str, **_kwargs):
        self.indices[index]["aliases"].pop(name, None)
        return {"acknowledged": True}

    def put_index_template(self, *, name: str, index_patterns=None, template=None, **_kwargs):
        self.templates[name] = {
            "index_patterns": index_patterns or [],
            "template": deepcopy(template or {}),
        }
        return {"acknowledged": True}

    def get_index_template(self, *, name: str = "*", **_kwargs):
        return {
            "index_templates": [
                {"name": key, "index_template": deepcopy(value)}
                for key, value in sorted(self.templates.items())
            ]
        }

    def delete_index_template(self, *, name: str, **_kwargs):
        self.templates.pop(name, None)
        return {"acknowledged": True}


class FakeElasticsearch:
    """In-memory Elasticsearch client for unit testing.

    Mirrors the ``elasticsearch-py`` 9.x keyword-arg API surface.
    """

    def __init__(self, *args, **kwargs) -> None:
        _ = args, kwargs
        self.indices = FakeIndicesClient()

    def ping(self) -> bool:
        return True

    def info(self) -> dict[str, object]:
        return {"cluster_name": "test-cluster"}

    def search(
        self, *, index: str, query=None, source=None, sort=None, size: int = 10, **_kwargs
    ):
        target = "widgets" if index == "widgets_current" else index
        docs = self.indices.indices[target]["documents"]
        query = query or {"match_all": {}}
        hits = []
        for doc_id, src in docs.items():
            if not _matches(src, query):
                continue
            payload = {"_id": doc_id, "_index": target, "_source": deepcopy(src)}
            hits.append(payload)
        return {"hits": {"hits": hits[:size]}}

    def count(self, *, index: str, query=None, **_kwargs):
        hits = self.search(index=index, query=query, size=1000)
        return {"count": len(hits["hits"]["hits"])}

    def index(
        self, *, index: str, document=None, body=None, id: str | None = None, **_kwargs
    ):
        target = "widgets" if index == "widgets_current" else index
        payload = document or body or {}
        next_id = id or str(len(self.indices.indices[target]["documents"]) + 1)
        self.indices.indices[target]["documents"][next_id] = deepcopy(payload)
        return {"_id": next_id}

    def get(self, *, index: str, id: str, **_kwargs):
        target = "widgets" if index == "widgets_current" else index
        return {
            "_id": id,
            "_index": target,
            "_source": deepcopy(self.indices.indices[target]["documents"][id]),
        }

    def update_by_query(
        self, *, index: str, query=None, script=None, **_kwargs
    ):
        target = "widgets" if index == "widgets_current" else index
        query = query or {"match_all": {}}
        params = script.get("params", {})
        updated = 0
        total = 0
        for doc in self.indices.indices[target]["documents"].values():
            if not _matches(doc, query):
                continue
            total += 1
            for key, value in params.get("set_values", {}).items():
                doc[key] = value
            for key in params.get("unset_fields", []):
                doc.pop(key, None)
            updated += 1
        return {"total": total, "updated": updated}

    def delete_by_query(self, *, index: str, query=None, **_kwargs):
        target = "widgets" if index == "widgets_current" else index
        query = query or {"match_all": {}}
        remaining = {}
        deleted = 0
        for doc_id, doc in self.indices.indices[target]["documents"].items():
            if _matches(doc, query):
                deleted += 1
            else:
                remaining[doc_id] = doc
        self.indices.indices[target]["documents"] = remaining
        return {"deleted": deleted}

    def close(self) -> None:
        return None


def _matches(document: dict[str, object], query: dict[str, object]) -> bool:
    """Minimal query DSL matcher for test purposes."""
    if not query or query == {"match_all": {}}:
        return True
    if "term" in query:
        field, value = next(iter(query["term"].items()))
        return document.get(field) == value
    if "terms" in query:
        field, values = next(iter(query["terms"].items()))
        return document.get(field) in values
    if "range" in query:
        field, rules = next(iter(query["range"].items()))
        value = document.get(field)
        return all(
            (key != "gt" or value > expected)
            and (key != "gte" or value >= expected)
            and (key != "lt" or value < expected)
            and (key != "lte" or value <= expected)
            for key, expected in rules.items()
        )
    if "exists" in query:
        return query["exists"]["field"] in document
    if "wildcard" in query:
        field, rule = next(iter(query["wildcard"].items()))
        needle = str(rule["value"]).strip("*")
        value = str(document.get(field, ""))
        return needle in value
    if "bool" in query:
        payload = query["bool"]
        must = payload.get("must", [])
        should = payload.get("should", [])
        must_not = payload.get("must_not", [])
        if must and not all(_matches(document, item) for item in must):
            return False
        if should and not any(_matches(document, item) for item in should):
            return False
        if must_not and any(_matches(document, item) for item in must_not):
            return False
        return True
    return False


@pytest.fixture(autouse=True)
def fake_elasticsearch(monkeypatch):
    """Replace the Elasticsearch client constructor with the in-memory fake."""
    monkeypatch.setattr(
        "src.core.connectors.elasticsearch.adapter.Elasticsearch",
        FakeElasticsearch,
    )


def test_adapter_capabilities_and_catalogue_calls() -> None:
    """Test capability report, validation, namespace listing, and entity listing."""
    connector = ElasticsearchConnector(uri="http://localhost:9200")
    assert connector.capability_report()["source_type"] == "elasticsearch"
    assert connector.capability_report()["supports"]["mapping_schema"] is True
    assert connector.validate_profile()["cluster_name"] == "test-cluster"
    assert connector.list_namespaces() == [{"name": "test-cluster", "type": "cluster"}]
    entities = connector.list_entities("test-cluster")
    assert {item["name"] for item in entities} >= {"widgets", "widgets_current"}


def test_adapter_data_and_schema_operations() -> None:
    """Test CRUD, schema change plans, and relationship inference."""
    connector = ElasticsearchConnector(uri="http://localhost:9200")
    detail = connector.describe_entity("test-cluster", "widgets")
    assert detail["document_count"] == 2
    fields = connector.describe_fields("test-cluster", "widgets")
    assert any(item["name"] == "owner_id" for item in fields["fields"])
    inserted = connector.create(
        "test-cluster", "widgets_current",
        {"name": "gamma", "owner_id": "u3", "value": 3},
    )
    assert inserted["document"]["_id"]
    updated = connector.update(
        "test-cluster", "widgets",
        {"term": {"owner_id": "u3"}},
        {"$set": {"value": 9}},
    )
    assert updated["modified_count"] == 1
    assert connector.count("test-cluster", "widgets", {"term": {"owner_id": "u3"}}) == 1
    plan = connector.schema_change_plan(
        {
            "operation": "create_index",
            "namespace": "test-cluster",
            "entity": "widgets",
            "keys": [{"field": "owner_id", "direction": "asc"}],
        }
    )
    assert plan["after_state"]["indexes"][-1]["name"] == "dbmcp_widgets_owner_id_asc"
    applied = connector.schema_change_apply(plan)
    assert applied["index_name"] == "dbmcp_widgets_owner_id_asc"
    indexes = connector.list_indexes("test-cluster", "widgets")
    assert any(item["name"] == "dbmcp_widgets_owner_id_asc" for item in indexes)
    create_entity = connector.schema_change_plan(
        {"operation": "create_entity", "namespace": "test-cluster", "entity": "archive"}
    )
    connector.schema_change_apply(create_entity)
    assert any(item["name"] == "archive" for item in connector.list_entities("test-cluster"))
    drop_entity = connector.schema_change_plan(
        {"operation": "drop_entity", "namespace": "test-cluster", "entity": "archive"}
    )
    dropped = connector.schema_change_apply(drop_entity)
    assert dropped["entity_dropped"] is True
    deleted = connector.delete("test-cluster", "widgets", {"term": {"owner_id": "u3"}})
    assert deleted["deleted_count"] == 1
    relationships = connector.extract_relationships("test-cluster", "widgets")
    assert relationships[0]["relationship_type"] == "reference_candidate"
