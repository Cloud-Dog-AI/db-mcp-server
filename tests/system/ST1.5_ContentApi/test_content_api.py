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
# Description: System test for content MCP tools with structured filters against real MongoDB.
# Related requirements: CO-01, CO-02, CN-01
# Related tests: ST1.5

from __future__ import annotations

import os
from pathlib import Path

import pytest

from tests.fixtures.seed_data import seed_mongodb
from tests.helpers.core_tools_runtime import API_BASE_URL, MCP_BASE_URL, call_tool, create_profile, start_servers, stop_servers, unique_db_name, wait_for
from tests.helpers.mongo_runtime import cleanup_database, ensure_real_mongodb

pytestmark = [pytest.mark.system, pytest.mark.db, pytest.mark.mcp, pytest.mark.timeout(240)]


def test_content_tools_apply_structured_filters_and_masks() -> None:
    root = Path(__file__).resolve().parents[3]
    env_file = Path(os.environ.get("DB_MCP_SERVER_ENV_FILE", str(root / "tests" / "env-ST")))
    uri = ensure_real_mongodb()
    db_name = unique_db_name("dbmcp_st_content")
    seed_mongodb(uri=uri, db_name=db_name)

    start_servers(root, env_file)
    try:
        wait_for(f"{MCP_BASE_URL}/health")
        profile_id = create_profile(
            base_url=API_BASE_URL,
            profile_name="st-content-profile",
            allowed_permissions=["catalog.read", "schema.read", "data.read", "data.create", "data.update", "data.delete"],
            field_masks={"country": "MASKED"},
        )
        filtered = call_tool(
            "data.read",
            {
                "profile_id": profile_id,
                "namespace": db_name,
                "entity": "customers",
                "filter": {
                    "op": "and",
                    "conditions": [
                        {"field": "country", "operator": "eq", "value": "UK"},
                        {"field": "status", "operator": "eq", "value": "active"},
                    ],
                },
                "sort": [{"field": "_id", "direction": "asc"}],
                "limit": 5,
            },
        )
        assert filtered["items"]
        assert all(item["country"] == "MASKED" for item in filtered["items"])

        created = call_tool(
            "data.create",
            {
                "profile_id": profile_id,
                "namespace": db_name,
                "entity": "customers",
                "document": {"_id": "C999", "name": "Masked Customer", "country": "UK", "status": "active"},
            },
        )
        assert created["document"]["country"] == "MASKED"

        updated = call_tool(
            "data.update",
            {
                "profile_id": profile_id,
                "namespace": db_name,
                "entity": "customers",
                "filter": {"field": "_id", "operator": "eq", "value": "C999"},
                "update": {"$set": {"status": "inactive"}},
            },
        )
        assert updated["modified_count"] == 1

        exists = call_tool(
            "data.exists",
            {
                "profile_id": profile_id,
                "namespace": db_name,
                "entity": "customers",
                "filter": {"field": "status", "operator": "eq", "value": "inactive"},
            },
        )
        assert exists["exists"] is True

        deleted = call_tool(
            "data.delete",
            {
                "profile_id": profile_id,
                "namespace": db_name,
                "entity": "customers",
                "filter": {"field": "_id", "operator": "eq", "value": "C999"},
            },
        )
        assert deleted["deleted_count"] == 1
    finally:
        stop_servers(root, env_file)
        cleanup_database(db_name)
