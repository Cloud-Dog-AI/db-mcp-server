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
# Description: Integration test for relationship inference and curated lifecycle.
# Related requirements: RL-01, RL-02, RL-03, CN-01
# Related tests: IT1.5

from __future__ import annotations

from pathlib import Path

import pytest

from tests.helpers.core_tools_runtime import API_BASE_URL, MCP_BASE_URL, call_tool, create_profile, seed_via_mcp, start_servers, stop_servers, unique_db_name, wait_for
from tests.helpers.server_runtime import active_env_file

pytestmark = [pytest.mark.integration, pytest.mark.db, pytest.mark.mcp, pytest.mark.timeout(300)]
@pytest.mark.IT
@pytest.mark.mcp
@pytest.mark.req("FR-009")


def test_relationship_infer_create_update_delete_flow() -> None:
    root = Path(__file__).resolve().parents[3]
    env_file = active_env_file(default_tier="IT")
    db_name = unique_db_name("dbmcp_it_relationship")

    start_servers(root, env_file)
    try:
        wait_for(f"{MCP_BASE_URL}/health")
        profile_id = create_profile(
            base_url=API_BASE_URL,
            profile_name="it-relationship-profile",
            allowed_permissions=["catalog.read", "schema.read", "data.read", "data.create", "relationship.read", "relationship.change"],
        )
        seed_via_mcp(profile_id, db_name)

        inferred = call_tool(
            "relationship.infer",
            {"profile_id": profile_id, "namespace": db_name, "entity": "orders"},
        )
        assert any(item["field"] == "customer_id" and item["target_entity"] == "customer" for item in inferred["items"])

        curated = call_tool(
            "relationship.create",
            {
                "profile_id": profile_id,
                "namespace": db_name,
                "entity": "orders",
                "field": "customer_id",
                "target_namespace": db_name,
                "target_entity": "customers",
                "relationship_type": "many_to_one",
                "description": "Orders belong to customers",
            },
        )
        assert curated["provenance"] == "curated"

        listed = call_tool(
            "relationship.list",
            {"profile_id": profile_id, "namespace": db_name, "entity": "orders"},
        )
        assert any(item["relationship_id"] == curated["relationship_id"] for item in listed["items"])

        updated = call_tool(
            "relationship.update",
            {"relationship_id": curated["relationship_id"], "description": "Orders map to customer master"},
        )
        assert updated["description"] == "Orders map to customer master"

        deleted = call_tool("relationship.delete", {"relationship_id": curated["relationship_id"]})
        assert deleted["deleted"] is True
    finally:
        stop_servers(root, env_file)
