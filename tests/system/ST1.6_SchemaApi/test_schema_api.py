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
# Description: System test for schema MCP tools against real MongoDB.
# Related requirements: SC-01, SC-02, W28A-274-L deliverables 2, 4, 5
# Related tests: ST1.6

from __future__ import annotations

import os
from pathlib import Path

import pytest

from tests.fixtures.seed_data import seed_mongodb
from tests.helpers.core_tools_runtime import API_BASE_URL, MCP_BASE_URL, call_tool, create_profile, start_servers, stop_servers, unique_db_name, wait_for
from tests.helpers.mongo_runtime import cleanup_database, ensure_real_mongodb

pytestmark = [pytest.mark.system, pytest.mark.db, pytest.mark.mcp, pytest.mark.timeout(240)]
@pytest.mark.ST
@pytest.mark.mcp
@pytest.mark.req("FR-006")


def test_schema_tools_plan_apply_history_and_refresh() -> None:
    root = Path(__file__).resolve().parents[3]
    env_file = Path(os.environ.get("DB_MCP_SERVER_ENV_FILE", str(root / "tests" / "env-ST")))
    uri = ensure_real_mongodb()
    db_name = unique_db_name("dbmcp_st_schema")
    seed_mongodb(uri=uri, db_name=db_name)

    start_servers(root, env_file)
    try:
        wait_for(f"{MCP_BASE_URL}/health")
        profile_id = create_profile(
            base_url=API_BASE_URL,
            profile_name="st-schema-profile",
            allowed_permissions=[
                "schema.read",
                "schema.change",
                "catalog.read",
                "data.read",
                "index.manage",
            ],
            namespaces=[db_name],
            index_policy={
                "enabled": True,
                "include_content": True,
                "content_fields": ["status", "email", "product"],
                "max_documents_per_entity": 10,
                "max_excerpt_chars": 240,
            },
        )

        initial_sync = call_tool("index.sync_profile", {"profile_id": profile_id})
        assert initial_sync["job_status"] == "succeeded"
        initial_status = call_tool("index.status", {"profile_id": profile_id})
        initial_orders = next(item for item in initial_status["items"][0]["entities"] if item["entity"] == "orders")

        describe = call_tool("schema.describe_entity", {"profile_id": profile_id, "namespace": db_name, "entity": "orders"})
        assert any(field["name"] == "customer_id" for field in describe["fields"])

        plan = call_tool(
            "schema.change.plan",
            {
                "profile_id": profile_id,
                "operation": {
                    "operation": "create_index",
                    "namespace": db_name,
                    "entity": "orders",
                    "name": "orders_status_idx",
                    "keys": [{"field": "status", "direction": "asc"}],
                },
            },
        )
        assert plan["operation"] == "create_index"
        assert plan["dry_run"] is True
        assert plan["requires_approval"] is True
        assert plan["dry_run_result"]["operations"][0]["after_state"]["indexes"][-1]["name"] == "orders_status_idx"

        applied = call_tool("schema.change.apply", {"profile_id": profile_id, "plan": plan, "approved": True})
        assert applied["applied"] is True
        assert applied["index_refresh_triggered"] is True
        indexes = call_tool("schema.list_indexes", {"profile_id": profile_id, "namespace": db_name, "entity": "orders"})
        assert any(item["name"] == "orders_status_idx" for item in indexes["items"])

        history = call_tool("schema.change.history", {"profile_id": profile_id, "limit": 5})
        assert history["items"][0]["plan_id"] == plan["plan_id"]
        assert history["items"][0]["status"] == "applied"
        assert history["items"][0]["audit_event_id"].endswith(":apply-state")
        assert any(item["action"] == "schema.change.apply" for item in history["items"][0]["audit_trail"])

        refreshed_status = call_tool("index.status", {"profile_id": profile_id})
        refreshed_orders = next(item for item in refreshed_status["items"][0]["entities"] if item["entity"] == "orders")
        assert refreshed_orders["last_synced_at"] >= initial_orders["last_synced_at"]

        samples = call_tool("schema.sample_shapes", {"profile_id": profile_id, "namespace": db_name, "entity": "orders", "count": 3})
        assert len(samples["items"]) == 3
    finally:
        stop_servers(root, env_file)
        cleanup_database(db_name)
