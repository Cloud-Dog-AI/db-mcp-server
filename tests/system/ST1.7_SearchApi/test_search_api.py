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
# Description: ST coverage for discovery search and indexing against real MongoDB.
# Related requirements: W28A-274-I deliverables 1, 2, 3, 4
# Related tests: ST1.7

from __future__ import annotations

import os
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
import pytest
@pytest.mark.ST
@pytest.mark.mcp
@pytest.mark.req("FR-010")


def test_v1_7_search_metadata_finds_customer_email_field() -> None:
    root = Path(__file__).resolve().parents[3]
    env_file = Path(os.environ.get("DB_MCP_SERVER_ENV_FILE", str(root / "tests" / "env-ST")))
    start_servers(root, env_file)
    try:
        wait_for(f"{API_BASE_URL}/health")
        namespace = unique_db_name("search_st")
        profile_id = create_profile(
            base_url=API_BASE_URL,
            profile_name="search-st-profile",
            allowed_permissions=[
                "catalog.read",
                "schema.read",
                "relationship.read",
                "data.read",
                "data.create",
                "content.search",
                "index.manage",
            ],
            description="Search ST profile",
            namespaces=[namespace],
            index_policy={
                "enabled": True,
                "include_content": True,
                "content_fields": ["email", "name", "product"],
                "max_documents_per_entity": 10,
            },
        )
        seed_via_mcp(profile_id, namespace)

        sync_result = call_tool("index.sync_profile", {"profile_id": profile_id})
        assert sync_result["job_status"] == "succeeded"
        assert sync_result["profile_status"]["field_count"] >= 1

        search_result = call_tool(
            "search.metadata",
            {"profile_id": profile_id, "query": "customer email", "limit": 10},
        )
        assert search_result["items"], search_result
        match = next(
            item
            for item in search_result["items"]
            if item["doc_kind"] == "field" and item["title"] == "customers.email"
        )
        explain_result = call_tool(
            "search.explain_match",
            {
                "profile_id": profile_id,
                "query": "customer email",
                "document_id": match["document_id"],
            },
        )
        assert any(item["field"] == "title" for item in explain_result["matched_components"])

        status_result = call_tool("index.status", {"profile_id": profile_id})
        assert status_result["items"][0]["profile_id"] == profile_id
        assert status_result["items"][0]["freshness_state"] == "fresh"
    finally:
        stop_servers(root, env_file)
