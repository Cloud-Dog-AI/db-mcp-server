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
# Description: Integration test for full discovery and audit flow via API and MCP.
# Related requirements: CD-01, CD-02, CD-03, AC-02, CN-01
# Related tests: IT1.3

from __future__ import annotations

from pathlib import Path

import pytest

from tests.helpers.core_tools_runtime import API_BASE_URL, MCP_BASE_URL, call_tool, create_profile, seed_via_mcp, start_servers, stop_servers, unique_db_name, wait_for
from tests.helpers.server_runtime import active_env_file

pytestmark = [pytest.mark.integration, pytest.mark.db, pytest.mark.mcp, pytest.mark.timeout(300)]
@pytest.mark.IT
@pytest.mark.mcp
@pytest.mark.req("FR-005")


def test_full_discovery_flow_via_api_and_mcp() -> None:
    root = Path(__file__).resolve().parents[3]
    env_file = active_env_file(default_tier="IT")
    db_name = unique_db_name("dbmcp_it_discovery")

    start_servers(root, env_file)
    try:
        wait_for(f"{MCP_BASE_URL}/health")
        profile_id = create_profile(
            base_url=API_BASE_URL,
            profile_name="it-discovery-profile",
            allowed_permissions=["catalog.read", "schema.read", "data.read", "data.create", "audit.read"],
        )
        seed_via_mcp(profile_id, db_name)

        namespaces = call_tool("catalog.list_namespaces", {"profile_id": profile_id})
        assert any(item["name"] == db_name for item in namespaces["items"])

        entities = call_tool("catalog.list_entities", {"profile_id": profile_id, "namespace": db_name})
        assert any(item["name"] == "orders" for item in entities["items"])

        entity = call_tool("catalog.get_entity", {"profile_id": profile_id, "namespace": db_name, "entity": "orders"})
        assert entity["document_count"] == 50

        read = call_tool(
            "data.read",
            {
                "profile_id": profile_id,
                "namespace": db_name,
                "entity": "orders",
                "filter": {"field": "status", "operator": "eq", "value": "shipped"},
                "limit": 5,
            },
        )
        assert read["items"]

        search = call_tool("catalog.search", {"profile_id": profile_id, "query": "supplier"})
        assert any(item["entity"] == "products" for item in search["items"])

        audit = call_tool("audit.list_events", {"limit": 20, "event_type": "tool.call"})
        assert any(item.get("details", {}).get("tool") == "catalog.search" for item in audit["items"])
    finally:
        stop_servers(root, env_file)
