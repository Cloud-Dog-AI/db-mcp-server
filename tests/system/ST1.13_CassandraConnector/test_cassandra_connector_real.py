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
# Description: System test for the Cassandra adapter against a real Cassandra runtime.
# Related requirements: CN-01
# Related tests: ST1.13
# Recent changes:
#   W28A-274-G — Initial implementation

from __future__ import annotations

import os

import pytest

from src.core.connectors.cassandra.adapter import CassandraConnector
from tests.helpers.cassandra_runtime import ensure_real_cassandra

pytestmark = [pytest.mark.system, pytest.mark.timeout(240)]

CASSANDRA_HOST = os.getenv("DB_MCP_TEST_CASSANDRA_HOST", "127.0.0.1")
CASSANDRA_PORT = int(os.getenv("DB_MCP_TEST_CASSANDRA_PORT", "9042"))
KEYSPACE = os.getenv("DB_MCP_TEST_CASSANDRA_KEYSPACE", "dbmcp_ecommerce")


def _ensure_cassandra() -> CassandraConnector:
    """Connect to Cassandra or fail (not skip) if unavailable."""
    try:
        host, port, _ = ensure_real_cassandra()
        connector = CassandraConnector(
            host=host, port=port, timeout_seconds=15
        )
        connector.validate_profile()
        return connector
    except Exception as exc:
        pytest.fail(f"Cassandra not available at {CASSANDRA_HOST}:{CASSANDRA_PORT}: {exc}")
@pytest.mark.ST
@pytest.mark.mcp
@pytest.mark.probe  # rtt-2026-06-12 INST3: KEEP-AS-PROBE pending operator REQ-binding


def test_cassandra_adapter_against_real_runtime() -> None:
    """Cassandra adapter methods should work against a real runtime with seeded data."""
    connector = _ensure_cassandra()
    try:
        # Namespace listing
        namespaces = connector.list_namespaces()
        assert any(item["name"] == KEYSPACE for item in namespaces), (
            f"Keyspace {KEYSPACE} not found. Run cassandra_seed.py first."
        )

        # Entity listing
        entities = connector.list_entities(KEYSPACE)
        table_names = {item["name"] for item in entities}
        assert "customers" in table_names, f"Expected 'customers' table in {table_names}"

        # Describe fields — strongly typed from system_schema
        fields = connector.describe_fields(KEYSPACE, "customers")
        field_names = {item["name"] for item in fields["fields"]}
        assert "id" in field_names
        assert "name" in field_names
        assert fields["source"] == "system_schema"
        # Verify partition key is captured
        pk_fields = [f for f in fields["fields"] if f["kind"] == "partition_key"]
        assert len(pk_fields) > 0, "Should have at least one partition key field"

        # Count
        total = connector.count(KEYSPACE, "customers")
        assert total > 0, "Seeded data should have at least one customer"

        # Sample shapes
        samples = connector.sample_shapes(KEYSPACE, "customers", n=3)
        assert len(samples) > 0
        assert "name" in samples[0]

        # Read with partition key filter
        first_id = samples[0].get("id")
        if first_id:
            rows = connector.read(KEYSPACE, "customers", {"id": first_id}, limit=1)
            assert len(rows) == 1
            assert rows[0]["id"] == first_id

        # CRUD on a test table
        connector.schema_change_apply({
            "operation": "create_entity",
            "namespace": KEYSPACE,
            "entity": "st_test_crud",
            "columns": {"id": "text", "name": "text", "value": "int"},
            "primary_key": "id",
        })
        try:
            connector.create(KEYSPACE, "st_test_crud", {"id": "t1", "name": "test", "value": 42})
            read_back = connector.read(KEYSPACE, "st_test_crud", {"id": "t1"}, limit=1)
            assert len(read_back) == 1
            assert read_back[0]["name"] == "test"
            assert read_back[0]["value"] == 42

            connector.update(
                KEYSPACE, "st_test_crud",
                {"id": "t1"},
                {"$set": {"value": 99}},
            )
            updated = connector.read(KEYSPACE, "st_test_crud", {"id": "t1"}, limit=1)
            assert updated[0]["value"] == 99

            connector.delete(KEYSPACE, "st_test_crud", {"id": "t1"})
            after_delete = connector.count(KEYSPACE, "st_test_crud", {"id": "t1"})
            assert after_delete == 0

            # Relationship inference
            relationships = connector.extract_relationships(KEYSPACE, "orders")
            assert any(item["field"] == "customer_id" for item in relationships)

            # Schema change — create/drop index
            plan = connector.schema_change_plan({
                "operation": "create_index",
                "namespace": KEYSPACE,
                "entity": "st_test_crud",
                "column": "name",
            })
            assert plan["dry_run"] is True
            applied = connector.schema_change_apply(plan)
            assert applied["applied"] is True
        finally:
            connector.schema_change_apply({
                "operation": "drop_entity",
                "namespace": KEYSPACE,
                "entity": "st_test_crud",
            })
    finally:
        connector.close()
