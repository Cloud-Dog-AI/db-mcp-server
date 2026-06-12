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
# Description: Integration test for schema change plan/approve/apply workflow with audit and index refresh.
# Related requirements: SC-01, SC-02, W28A-274-L deliverables 2, 4, 5
# Related tests: IT1.7

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.fixtures.seed_data import seed_mongodb
from tests.helpers.core_tools_runtime import API_BASE_URL, call_tool, create_profile, start_servers, stop_servers, unique_db_name, wait_for
from tests.helpers.mongo_runtime import cleanup_database, ensure_real_mongodb
from tests.helpers.server_runtime import active_env_file

pytestmark = [pytest.mark.integration, pytest.mark.timeout(240)]
@pytest.mark.IT
@pytest.mark.mcp
@pytest.mark.probe  # rtt-2026-06-12 INST3: KEEP-AS-PROBE pending operator REQ-binding


def test_v1_7_schema_change_plan_approve_apply_audit_and_refresh() -> None:
    root = Path(__file__).resolve().parents[3]
    env_file = active_env_file(default_tier="IT")
    audit_log = root / "logs" / "audit.log.jsonl"
    audit_log.unlink(missing_ok=True)

    uri = ensure_real_mongodb()
    namespace = unique_db_name("schema_it")
    seed_mongodb(uri=uri, db_name=namespace)

    start_servers(root, env_file)
    try:
        wait_for(f"{API_BASE_URL}/health")
        profile_id = create_profile(
            base_url=API_BASE_URL,
            profile_name="schema-it-profile",
            allowed_permissions=[
                "catalog.read",
                "schema.read",
                "schema.change",
                "data.read",
                "index.manage",
            ],
            namespaces=[namespace],
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

        plan = call_tool(
            "schema.change.plan",
            {
                "profile_id": profile_id,
                "operation": {
                    "operation": "create_index",
                    "namespace": namespace,
                    "entity": "orders",
                    "name": "orders_status_idx",
                    "keys": [{"field": "status", "direction": "asc"}],
                },
            },
        )
        assert plan["plan_id"].startswith("schg_")
        assert plan["audit_trail"][0]["audit_event_id"].endswith(":plan")

        applied = call_tool("schema.change.apply", {"profile_id": profile_id, "plan": plan, "approved": True})
        assert applied["success"] is True
        assert applied["operations_applied"] == 1
        assert applied["audit_event_id"].endswith(":apply-state")
        assert applied["index_refresh_triggered"] is True

        indexes = call_tool("schema.list_indexes", {"profile_id": profile_id, "namespace": namespace, "entity": "orders"})
        assert any(item["name"] == "orders_status_idx" for item in indexes["items"])

        history = call_tool("schema.change.history", {"profile_id": profile_id, "limit": 5})
        entry = history["items"][0]
        assert entry["plan_id"] == plan["plan_id"]
        assert entry["status"] == "applied"
        assert entry["result"]["audit_event_id"] == applied["audit_event_id"]
        assert any(item["audit_event_id"].endswith(":apply-state") for item in entry["audit_trail"])

        refreshed_status = call_tool("index.status", {"profile_id": profile_id})
        refreshed_orders = next(item for item in refreshed_status["items"][0]["entities"] if item["entity"] == "orders")
        assert refreshed_orders["last_synced_at"] >= initial_orders["last_synced_at"]

        audit_lines = [json.loads(line) for line in audit_log.read_text(encoding="utf-8").splitlines() if line.strip()]
        matching = [item for item in audit_lines if item.get("correlation_id") == applied["audit_event_id"]]
        assert matching, applied["audit_event_id"]
        privileged = matching[0]
        assert privileged["event_type"] == "admin.schema.change"
        assert privileged["details"]["approval_status"] == "approved"
        assert privileged["details"]["new_value"][0]["indexes"]
    finally:
        stop_servers(root, env_file)
        cleanup_database(namespace)
