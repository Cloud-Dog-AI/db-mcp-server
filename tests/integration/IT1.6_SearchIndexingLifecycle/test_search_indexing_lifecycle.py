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
# Description: IT coverage for discovery indexing pipeline and search lifecycle.
# Related requirements: W28A-274-I deliverables 1, 2, 3, 4
# Related tests: IT1.6

from __future__ import annotations

from pathlib import Path

from tests.helpers.core_tools_runtime import (
    API_BASE_URL,
    call_tool,
    create_profile,
    seed_via_mcp,
    start_servers,
    stop_servers,
    unique_db_name,
    wait_for,
)
from tests.helpers.server_runtime import active_env_file
import pytest
@pytest.mark.IT
@pytest.mark.mcp
@pytest.mark.req("FR-009")


def test_v1_6_full_search_indexing_pipeline() -> None:
    root = Path(__file__).resolve().parents[3]
    env_file = active_env_file(default_tier="IT")
    start_servers(root, env_file)
    try:
        wait_for(f"{API_BASE_URL}/health")
        namespace = unique_db_name("search_it")
        profile_id = create_profile(
            base_url=API_BASE_URL,
            profile_name="search-it-profile",
            allowed_permissions=[
                "catalog.read",
                "schema.read",
                "relationship.read",
                "data.read",
                "data.create",
                "content.search",
                "index.manage",
            ],
            description="Search IT profile",
            namespaces=[namespace],
            index_policy={
                "enabled": True,
                "include_content": True,
                "content_fields": ["email", "name", "product"],
                "max_documents_per_entity": 10,
                "max_excerpt_chars": 240,
            },
        )
        seed_via_mcp(profile_id, namespace)

        full_sync = call_tool("index.sync_profile", {"profile_id": profile_id})
        assert full_sync["job_status"] == "succeeded"
        assert full_sync["profile_status"]["document_count"] > 0

        metadata = call_tool("search.metadata", {"profile_id": profile_id, "query": "customer email"})
        assert any(item["title"] == "customers.email" for item in metadata["items"])

        content = call_tool("search.content", {"profile_id": profile_id, "query": "customer01@example.com"})
        assert any(item["doc_kind"] == "content_excerpt" for item in content["items"])

        related = call_tool(
            "search.related",
            {"profile_id": profile_id, "namespace": namespace, "entity": "orders", "limit": 5},
        )
        related_entities = {(item["namespace"], item["entity"]) for item in related["items"]}
        assert (namespace, "customers") in related_entities or (namespace, "products") in related_entities

        entity_sync = call_tool(
            "index.sync_entity",
            {"profile_id": profile_id, "namespace": namespace, "entity": "customers"},
        )
        assert entity_sync["job_status"] == "succeeded"
        assert entity_sync["entity_status"]["entity"] == "customers"

        rebuilt = call_tool("index.rebuild", {"profile_ids": [profile_id]})
        assert rebuilt["job_status"] == "succeeded"
        assert rebuilt["profiles"][0]["profile_id"] == profile_id

        status = call_tool("index.status", {"profile_id": profile_id})
        assert status["items"][0]["document_count"] > 0
        assert status["items"][0]["entities"]
    finally:
        stop_servers(root, env_file)
