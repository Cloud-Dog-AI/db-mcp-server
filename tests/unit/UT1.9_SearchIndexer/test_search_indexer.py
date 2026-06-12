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
# Description: UT coverage for discovery indexer normalisation and document creation.
# Related requirements: W28A-274-I deliverables 1, 2
# Tests: CD-04, SI-01, SI-02, SI-03, SI-04
# Related tests: UT1.9

from __future__ import annotations

from types import SimpleNamespace

from src.core.search import DiscoveryIndexer, build_fts5_query, normalise_search_terms
import pytest


class _FakeConnector:
    def list_namespaces(self):
        return [{"name": "sales", "type": "database"}]

    def list_entities(self, namespace: str):
        assert namespace == "sales"
        return [{"name": "customers", "type": "collection"}]

    def describe_entity(self, namespace: str, entity: str):
        return {"namespace": namespace, "entity": entity, "document_count": 2, "indexes": []}

    def describe_fields(self, namespace: str, entity: str):
        return {
            "fields": [
                {"name": "_id", "types": ["str"]},
                {"name": "email", "types": ["str"]},
                {"name": "name", "types": ["str"]},
            ]
        }

    def extract_relationships(self, namespace: str, entity: str):
        return [{"field": "account_manager_id", "target_entity_hint": "users", "relationship_type": "reference_candidate"}]

    def read(self, namespace: str, entity: str, limit: int | None = None):
        assert limit == 3
        return [
            {"_id": "C001", "name": "Acme", "email": "acme@example.com", "status": "active"},
            {"_id": "C002", "name": "Beta", "email": "beta@example.com", "status": "inactive"},
        ]

    def close(self):
        return None


class _FakeConnectors:
    def __init__(self):
        self.profile = {
            "profile_id": "profile-1",
            "name": "Search Test",
            "source_type": "mongodb",
            "description": "Test profile",
            "field_masks": {},
            "field_exclusions": ["status"],
            "index_policy": {
                "enabled": True,
                "include_content": True,
                "content_fields": ["email", "name"],
                "max_documents_per_entity": 3,
                "max_excerpt_chars": 180,
            },
        }

    def for_profile(self, profile_id: str):
        assert profile_id == "profile-1"
        return SimpleNamespace(profile=self.profile, connector=_FakeConnector())

    @staticmethod
    def filter_namespaces(profile, namespaces):
        return namespaces

    @staticmethod
    def filter_entities(profile, namespace, entities):
        return entities

    @staticmethod
    def ensure_entity_allowed(profile, namespace, entity):
        return None


class _FakeAccessControl:
    @staticmethod
    def get_profile(profile_id: str):
        return {
            "profile_id": profile_id,
            "name": "Search Test",
            "source_type": "mongodb",
            "description": "Test profile",
            "index_policy": {
                "enabled": True,
                "include_content": True,
                "content_fields": ["email", "name"],
                "max_documents_per_entity": 3,
                "max_excerpt_chars": 180,
            },
        }


def _build_runtime():
    return SimpleNamespace(
        config={
            "search.max_documents_per_entity": 3,
            "search.max_excerpt_chars": 180,
        },
        access_control=_FakeAccessControl(),
        connectors=_FakeConnectors(),
    )
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.probe  # rtt-2026-06-12 INST3: KEEP-AS-PROBE pending operator REQ-binding


def test_v1_9_1_query_normalisation_and_fts_building() -> None:
    assert normalise_search_terms("Customer email fields") == ["customer", "email", "fields"]
    assert build_fts5_query("Customer email fields") == "customer* AND email* AND fields*"
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.probe  # rtt-2026-06-12 INST3: KEEP-AS-PROBE pending operator REQ-binding


def test_v1_9_2_sync_profile_builds_metadata_relationship_and_content_documents() -> None:
    runtime = _build_runtime()
    indexer = DiscoveryIndexer(runtime)

    result = indexer.sync_profile("profile-1", job_id="job-1")

    documents = result["documents"]
    profile_status = result["profile_status"]
    entity_statuses = result["entity_statuses"]

    assert any(item.doc_kind == "field" and item.title == "customers.email" for item in documents)
    assert any(item.doc_kind == "relationship_hint" and item.related_entity == "users" for item in documents)
    assert any(item.doc_kind == "content_excerpt" and "acme@example.com" in item.excerpt for item in documents)
    assert all("status" not in item.excerpt for item in documents if item.doc_kind == "content_excerpt")
    assert profile_status.document_count == len(documents)
    assert profile_status.field_count == 3
    assert profile_status.content_count == 2
    assert len(entity_statuses) == 1
    assert entity_statuses[0].entity == "customers"
