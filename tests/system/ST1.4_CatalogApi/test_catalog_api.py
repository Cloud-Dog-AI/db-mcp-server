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
# Description: System test for catalogue MCP tools against real MongoDB.
# Related requirements: CD-01, CD-02, CD-03, CN-01
# Related tests: ST1.4

from __future__ import annotations

import os
from pathlib import Path

import pytest

from tests.fixtures.seed_data import seed_mongodb
from tests.helpers.core_tools_runtime import API_BASE_URL, MCP_BASE_URL, call_tool, create_profile, start_servers, stop_servers, unique_db_name, wait_for
from tests.helpers.mongo_runtime import cleanup_database, ensure_real_mongodb

pytestmark = [pytest.mark.system, pytest.mark.db, pytest.mark.mcp, pytest.mark.timeout(240)]


def test_catalogue_tools_against_real_mongodb() -> None:
    root = Path(__file__).resolve().parents[3]
    env_file = Path(os.environ.get("DB_MCP_SERVER_ENV_FILE", str(root / "tests" / "env-ST")))
    uri = ensure_real_mongodb()
    db_name = unique_db_name("dbmcp_st_catalog")
    seed_mongodb(uri=uri, db_name=db_name)

    start_servers(root, env_file)
    try:
        wait_for(f"{MCP_BASE_URL}/health")
        profile_id = create_profile(
            base_url=API_BASE_URL,
            profile_name="st-catalog-profile",
            allowed_permissions=["catalog.read", "schema.read", "data.read"],
        )
        namespaces = call_tool("catalog.list_namespaces", {"profile_id": profile_id})
        assert any(item["name"] == db_name for item in namespaces["items"])

        entities = call_tool("catalog.list_entities", {"profile_id": profile_id, "namespace": db_name})
        assert {item["name"] for item in entities["items"]} >= {"customers", "orders", "products", "suppliers", "invoices"}

        entity = call_tool("catalog.get_entity", {"profile_id": profile_id, "namespace": db_name, "entity": "orders"})
        assert entity["document_count"] == 50
        assert entity["field_count"] >= 6

        search = call_tool("catalog.search", {"profile_id": profile_id, "query": "customer"})
        assert any(item["entity"] == "orders" for item in search["items"])
        assert any(item["entity"] == "customers" for item in search["items"])
    finally:
        stop_servers(root, env_file)
        cleanup_database(db_name)
