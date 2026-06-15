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

import base64
import os
from pathlib import Path

import pytest

from tests.fixtures.seed_data import seed_mongodb
from tests.helpers.core_tools_runtime import API_BASE_URL, MCP_BASE_URL, call_tool, create_profile, start_servers, stop_servers, unique_db_name, wait_for
from tests.helpers.mongo_runtime import cleanup_database, ensure_real_mongodb
from src.core.connectors.mongodb.adapter import MongoDBConnector

pytestmark = [pytest.mark.system, pytest.mark.db, pytest.mark.mcp, pytest.mark.timeout(240)]
@pytest.mark.ST
@pytest.mark.mcp
@pytest.mark.req("FR-006")


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
@pytest.mark.ST
@pytest.mark.mcp
@pytest.mark.req("FR-006")


def test_content_tools_support_all_documented_filter_operators() -> None:
    """Structured filter operators should behave correctly against real MongoDB."""
    root = Path(__file__).resolve().parents[3]
    env_file = Path(os.environ.get("DB_MCP_SERVER_ENV_FILE", str(root / "tests" / "env-ST")))
    uri = ensure_real_mongodb()
    db_name = unique_db_name("dbmcp_st_filters")
    connector = MongoDBConnector(uri=uri)

    connector.create(
        db_name,
        "records",
        {
            "_id": "R1",
            "name": "Alpha Widget",
            "status": "active",
            "quantity": 5,
            "category": "hardware",
            "nullable": None,
            "description": "small alpha widget",
            "tags": ["blue", "round"],
        },
    )
    connector.create(
        db_name,
        "records",
        {
            "_id": "R2",
            "name": "Beta Widget",
            "status": "inactive",
            "quantity": 15,
            "category": "software",
            "nullable": "present",
            "description": "beta release package",
            "optional": "set",
        },
    )
    connector.create(
        db_name,
        "records",
        {
            "_id": "R3",
            "name": "Gamma Tool",
            "status": "active",
            "quantity": 25,
            "category": "hardware",
            "nullable": "ready",
            "description": "gamma support tool",
            "optional": "set",
        },
    )
    connector.close()

    start_servers(root, env_file)
    try:
        wait_for(f"{MCP_BASE_URL}/health")
        profile_id = create_profile(
            base_url=API_BASE_URL,
            profile_name="st-filter-operators-profile",
            allowed_permissions=["catalog.read", "schema.read", "data.read", "data.update", "data.delete"],
        )

        cases = [
            ("eq", {"field": "status", "operator": "eq", "value": "active"}, {"R1", "R3"}),
            ("neq", {"field": "status", "operator": "neq", "value": "active"}, {"R2"}),
            ("gt", {"field": "quantity", "operator": "gt", "value": 15}, {"R3"}),
            ("gte", {"field": "quantity", "operator": "gte", "value": 15}, {"R2", "R3"}),
            ("lt", {"field": "quantity", "operator": "lt", "value": 15}, {"R1"}),
            ("lte", {"field": "quantity", "operator": "lte", "value": 15}, {"R1", "R2"}),
            ("in", {"field": "category", "operator": "in", "value": ["hardware"]}, {"R1", "R3"}),
            ("not_in", {"field": "category", "operator": "not_in", "value": ["hardware"]}, {"R2"}),
            ("contains", {"field": "name", "operator": "contains", "value": "Widget"}, {"R1", "R2"}),
            ("starts_with", {"field": "name", "operator": "starts_with", "value": "Alpha"}, {"R1"}),
            ("ends_with", {"field": "name", "operator": "ends_with", "value": "Tool"}, {"R3"}),
            ("exists", {"field": "optional", "operator": "exists", "value": True}, {"R2", "R3"}),
            ("not_exists", {"field": "optional", "operator": "not_exists"}, {"R1"}),
            ("regex", {"field": "description", "operator": "regex", "value": "^beta.*package$"}, {"R2"}),
            ("is_null", {"field": "nullable", "operator": "is_null"}, {"R1"}),
            ("is_not_null", {"field": "nullable", "operator": "is_not_null"}, {"R2", "R3"}),
        ]

        for operator_name, filter_payload, expected_ids in cases:
            result = call_tool(
                "data.read",
                {
                    "profile_id": profile_id,
                    "namespace": db_name,
                    "entity": "records",
                    "filter": filter_payload,
                    "sort": [{"field": "_id", "direction": "asc"}],
                    "limit": 10,
                },
            )
            observed_ids = {item["_id"] for item in result["items"]}
            assert observed_ids == expected_ids, (operator_name, observed_ids, expected_ids)

        and_result = call_tool(
            "data.read",
            {
                "profile_id": profile_id,
                "namespace": db_name,
                "entity": "records",
                "filter": {
                    "op": "and",
                    "conditions": [
                        {"field": "status", "operator": "eq", "value": "active"},
                        {"field": "category", "operator": "eq", "value": "hardware"},
                    ],
                },
            },
        )
        assert {item["_id"] for item in and_result["items"]} == {"R1", "R3"}

        or_result = call_tool(
            "data.read",
            {
                "profile_id": profile_id,
                "namespace": db_name,
                "entity": "records",
                "filter": {
                    "op": "or",
                    "conditions": [
                        {"field": "quantity", "operator": "lt", "value": 10},
                        {"field": "name", "operator": "starts_with", "value": "Gamma"},
                    ],
                },
            },
        )
        assert {item["_id"] for item in or_result["items"]} == {"R1", "R3"}
    finally:
        stop_servers(root, env_file)
        cleanup_database(db_name)
@pytest.mark.ST
@pytest.mark.mcp
@pytest.mark.req("FR-006")


def test_content_tools_round_trip_binary_fields() -> None:
    """Binary fields should round-trip through live Mongo content and schema paths."""
    root = Path(__file__).resolve().parents[3]
    env_file = Path(os.environ.get("DB_MCP_SERVER_ENV_FILE", str(root / "tests" / "env-ST")))
    uri = ensure_real_mongodb()
    db_name = unique_db_name("dbmcp_st_binary")

    small_blob = (b"small-binary-" * 4096)[:50 * 1024]
    large_blob = (b"large-binary-" * 50000)[:500 * 1024]

    start_servers(root, env_file)
    try:
        wait_for(f"{MCP_BASE_URL}/health")
        profile_id = create_profile(
            base_url=API_BASE_URL,
            profile_name="st-binary-profile",
            allowed_permissions=["catalog.read", "schema.read", "data.read", "data.create", "data.update", "data.delete"],
        )

        created = call_tool(
            "data.create",
            {
                "profile_id": profile_id,
                "namespace": db_name,
                "entity": "assets",
                "document": {
                    "_id": "blob-small",
                    "payload": {
                        "__type__": "binary",
                        "encoding": "hex",
                        "data": small_blob.hex(),
                    },
                },
            },
        )
        assert created["document"]["payload"] == small_blob.hex()

        fields = call_tool(
            "schema.describe_fields",
            {"profile_id": profile_id, "namespace": db_name, "entity": "assets"},
        )
        payload_field = next(item for item in fields["fields"] if item["name"] == "payload")
        assert payload_field["types"] == ["binary"]

        updated = call_tool(
            "data.update",
            {
                "profile_id": profile_id,
                "namespace": db_name,
                "entity": "assets",
                "filter": {"field": "_id", "operator": "eq", "value": "blob-small"},
                "update": {
                    "$set": {
                        "payload": {
                            "__type__": "binary",
                            "encoding": "base64",
                            "data": base64.b64encode(large_blob).decode("ascii"),
                        }
                    }
                },
            },
        )
        assert updated["modified_count"] == 1

        read_back = call_tool(
            "data.read",
            {
                "profile_id": profile_id,
                "namespace": db_name,
                "entity": "assets",
                "filter": {"field": "_id", "operator": "eq", "value": "blob-small"},
            },
        )
        assert read_back["items"][0]["payload"] == large_blob.hex()
        assert len(read_back["items"][0]["payload"]) == len(large_blob) * 2

        deleted = call_tool(
            "data.delete",
            {
                "profile_id": profile_id,
                "namespace": db_name,
                "entity": "assets",
                "filter": {"field": "_id", "operator": "eq", "value": "blob-small"},
            },
        )
        assert deleted["deleted_count"] == 1

        exists = call_tool(
            "data.exists",
            {
                "profile_id": profile_id,
                "namespace": db_name,
                "entity": "assets",
                "filter": {"field": "_id", "operator": "eq", "value": "blob-small"},
            },
        )
        assert exists["exists"] is False
    finally:
        stop_servers(root, env_file)
        cleanup_database(db_name)
