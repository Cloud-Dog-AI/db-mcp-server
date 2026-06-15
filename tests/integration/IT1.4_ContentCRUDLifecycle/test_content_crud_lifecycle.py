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
# Description: Integration test for end-to-end content CRUD through MCP tools.
# Related requirements: CO-01, CO-02, CN-01
# Related tests: IT1.4

from __future__ import annotations

from pathlib import Path

import pytest

from tests.helpers.core_tools_runtime import API_BASE_URL, MCP_BASE_URL, call_tool, create_profile, start_servers, stop_servers, unique_db_name, wait_for
from tests.helpers.server_runtime import active_env_file

pytestmark = [pytest.mark.integration, pytest.mark.db, pytest.mark.mcp, pytest.mark.timeout(300)]
@pytest.mark.IT
@pytest.mark.mcp
@pytest.mark.req("FR-009")


def test_content_crud_lifecycle_through_mcp() -> None:
    root = Path(__file__).resolve().parents[3]
    env_file = active_env_file(default_tier="IT")
    db_name = unique_db_name("dbmcp_it_crud")

    start_servers(root, env_file)
    try:
        wait_for(f"{MCP_BASE_URL}/health")
        profile_id = create_profile(
            base_url=API_BASE_URL,
            profile_name="it-crud-profile",
            allowed_permissions=["catalog.read", "schema.read", "data.read", "data.create", "data.update", "data.delete"],
            field_exclusions=["price"],
        )

        created = call_tool(
            "data.create",
            {
                "profile_id": profile_id,
                "namespace": db_name,
                "entity": "widgets",
                "document": {"_id": "W001", "name": "Widget A", "price": 10.5, "status": "draft"},
            },
        )
        assert "price" not in created["document"]

        read_before = call_tool(
            "data.read",
            {"profile_id": profile_id, "namespace": db_name, "entity": "widgets", "filter": {"_id": "W001"}, "limit": 10},
        )
        assert read_before["items"][0]["name"] == "Widget A"

        updated = call_tool(
            "data.update",
            {
                "profile_id": profile_id,
                "namespace": db_name,
                "entity": "widgets",
                "filter": {"field": "_id", "operator": "eq", "value": "W001"},
                "update": {"$set": {"status": "published"}},
            },
        )
        assert updated["modified_count"] == 1

        read_after = call_tool(
            "data.read",
            {
                "profile_id": profile_id,
                "namespace": db_name,
                "entity": "widgets",
                "filter": {"field": "status", "operator": "eq", "value": "published"},
                "limit": 10,
            },
        )
        assert read_after["items"][0]["status"] == "published"

        deleted = call_tool(
            "data.delete",
            {
                "profile_id": profile_id,
                "namespace": db_name,
                "entity": "widgets",
                "filter": {"field": "_id", "operator": "eq", "value": "W001"},
            },
        )
        assert deleted["deleted_count"] == 1

        exists = call_tool(
            "data.exists",
            {
                "profile_id": profile_id,
                "namespace": db_name,
                "entity": "widgets",
                "filter": {"field": "_id", "operator": "eq", "value": "W001"},
            },
        )
        assert exists["exists"] is False
    finally:
        stop_servers(root, env_file)
