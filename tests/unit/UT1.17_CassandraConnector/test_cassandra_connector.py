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
# Description: Unit tests for the Cassandra adapter with mocked Cluster/Session.
# Related requirements: CN-01
# Tests: CN-05
# Related tests: UT1.17
# Recent changes:
#   W28A-274-G — Initial implementation

from __future__ import annotations

from collections import namedtuple
from copy import deepcopy
from typing import Any

import pytest

from src.core.connectors.cassandra.adapter import CassandraConnector

pytestmark = pytest.mark.unit


Row = namedtuple("Row", ["column_name", "type", "kind", "position"], defaults=[0])
KeyspaceRow = namedtuple("KeyspaceRow", ["keyspace_name", "replication"])
TableRow = namedtuple("TableRow", ["table_name"])
IndexRow = namedtuple("IndexRow", ["index_name", "kind", "options"])
LocalRow = namedtuple("LocalRow", ["cluster_name"])
CountRow = namedtuple("CountRow", ["count"])


class FakeResultSet:
    """Minimal ResultSet stand-in for unit tests."""

    def __init__(self, rows: list[Any]) -> None:
        self._rows = rows

    def __iter__(self):
        return iter(self._rows)

    def one(self):
        return self._rows[0] if self._rows else None


class FakeSession:
    """In-memory Cassandra session mock."""

    def __init__(self) -> None:
        self.default_timeout: float = 30.0
        self.keyspaces = {
            "test_ks": {
                "replication": {"class": "SimpleStrategy", "replication_factor": "1"},
                "tables": {
                    "widgets": {
                        "columns": [
                            Row("_id", "text", "partition_key", 0),
                            Row("name", "text", "regular", 0),
                            Row("owner_id", "text", "regular", 0),
                            Row("status", "text", "regular", 0),
                            Row("value", "int", "regular", 0),
                        ],
                        "indexes": [
                            IndexRow("idx_widgets_status", "COMPOSITES", {"target": "status"}),
                        ],
                        "rows": {
                            "1": {"_id": "1", "name": "alpha", "owner_id": "u1", "status": "active", "value": 1},
                            "2": {"_id": "2", "name": "beta", "owner_id": "u2", "status": "inactive", "value": 2},
                        },
                    }
                },
            }
        }

    def execute(self, query: str, params: list | tuple | None = None) -> FakeResultSet:
        q = query.strip()

        if q == "SELECT cluster_name FROM system.local":
            return FakeResultSet([LocalRow("test-cluster")])

        if q.startswith("SELECT keyspace_name, replication FROM system_schema.keyspaces"):
            return FakeResultSet([
                KeyspaceRow(ks, data["replication"])
                for ks, data in self.keyspaces.items()
            ])

        if q.startswith("SELECT keyspace_name FROM system_schema.keyspaces WHERE"):
            ks_name = params[0] if params else ""
            if ks_name in self.keyspaces:
                return FakeResultSet([KeyspaceRow(ks_name, None)])
            return FakeResultSet([])

        if q.startswith("SELECT table_name FROM system_schema.tables WHERE"):
            ks_name = params[0] if params else ""
            ks = self.keyspaces.get(ks_name, {})
            return FakeResultSet([TableRow(t) for t in sorted(ks.get("tables", {}))])

        if q.startswith("SELECT column_name, type, kind, position"):
            ks_name = params[0] if params else ""
            table_name = params[1] if params and len(params) > 1 else ""
            table = self.keyspaces.get(ks_name, {}).get("tables", {}).get(table_name, {})
            return FakeResultSet(list(table.get("columns", [])))

        if q.startswith("SELECT column_name FROM system_schema.columns") and "kind = 'partition_key'" in q:
            ks_name = params[0] if params else ""
            table_name = params[1] if params and len(params) > 1 else ""
            table = self.keyspaces.get(ks_name, {}).get("tables", {}).get(table_name, {})
            pk_cols = [c for c in table.get("columns", []) if c.kind == "partition_key"]
            PKRow = namedtuple("PKRow", ["column_name"])
            return FakeResultSet([PKRow(c.column_name) for c in pk_cols])

        if q.startswith("SELECT index_name, kind, options"):
            ks_name = params[0] if params else ""
            table_name = params[1] if params and len(params) > 1 else ""
            table = self.keyspaces.get(ks_name, {}).get("tables", {}).get(table_name, {})
            return FakeResultSet(list(table.get("indexes", [])))

        if "COUNT(*)" in q:
            ks_table = self._extract_ks_table(q)
            if ks_table:
                ks, table = ks_table
                rows = self.keyspaces.get(ks, {}).get("tables", {}).get(table, {}).get("rows", {})
                filtered = self._apply_where(rows, q, params)
                return FakeResultSet([CountRow(len(filtered))])
            return FakeResultSet([CountRow(0)])

        if q.startswith("SELECT") and "FROM" in q:
            ks_table = self._extract_ks_table(q)
            if ks_table:
                ks, table = ks_table
                rows = self.keyspaces.get(ks, {}).get("tables", {}).get(table, {}).get("rows", {})
                filtered = self._apply_where(rows, q, params)
                limit = self._extract_limit(q)
                result = [type("Row", (), {"_asdict": lambda s=deepcopy(v): s, **deepcopy(v)})() for v in list(filtered.values())[:limit]]
                return FakeResultSet(result)

        if q.startswith("INSERT INTO"):
            ks_table = self._extract_ks_table(q)
            if ks_table and params:
                ks, table = ks_table
                col_str = q[q.index("(") + 1:q.index(")")]
                columns = [c.strip() for c in col_str.split(",")]
                row_data = dict(zip(columns, params))
                row_id = str(row_data.get("_id", str(len(self.keyspaces[ks]["tables"][table]["rows"]) + 1)))
                self.keyspaces[ks]["tables"][table]["rows"][row_id] = row_data
            return FakeResultSet([])

        if q.startswith("UPDATE"):
            return FakeResultSet([])

        if q.startswith("DELETE FROM"):
            ks_table = self._extract_ks_table(q)
            if ks_table and params:
                ks, table = ks_table
                rows = self.keyspaces.get(ks, {}).get("tables", {}).get(table, {}).get("rows", {})
                to_remove = [k for k, v in rows.items() if self._row_matches_params(v, q, params)]
                for k in to_remove:
                    del rows[k]
            return FakeResultSet([])

        if q.startswith("CREATE TABLE") or q.startswith("DROP TABLE"):
            ks_table = self._extract_ks_table(q)
            if ks_table:
                ks, table = ks_table
                if q.startswith("CREATE"):
                    self.keyspaces.setdefault(ks, {"replication": {}, "tables": {}})
                    self.keyspaces[ks]["tables"][table] = {"columns": [], "indexes": [], "rows": {}}
                else:
                    self.keyspaces.get(ks, {}).get("tables", {}).pop(table, None)
            return FakeResultSet([])

        if q.startswith("CREATE INDEX"):
            return FakeResultSet([])

        if q.startswith("DROP INDEX"):
            return FakeResultSet([])

        return FakeResultSet([])

    def shutdown(self) -> None:
        pass

    @staticmethod
    def _extract_ks_table(query: str) -> tuple[str, str] | None:
        """Extract keyspace.table from CQL query."""
        for keyword in ("FROM", "INTO", "UPDATE", "TABLE", "ON"):
            if keyword in query.upper():
                parts = query.upper().split(keyword)
                if len(parts) > 1:
                    remainder = parts[1].strip().split()[0] if parts[1].strip() else ""
                    remainder_original = query.split(keyword.lower() if keyword.lower() in query else keyword)
                    if len(remainder_original) > 1:
                        token = remainder_original[1].strip().split()[0].rstrip("(;")
                        if "." in token:
                            ks, table = token.split(".", 1)
                            return ks, table
        return None

    @staticmethod
    def _extract_limit(query: str) -> int:
        upper = query.upper()
        if "LIMIT" in upper:
            parts = upper.split("LIMIT")
            if len(parts) > 1:
                num = parts[1].strip().split()[0]
                try:
                    return int(num)
                except ValueError:
                    pass
        return 1000

    @staticmethod
    def _apply_where(rows: dict, query: str, params: list | tuple | None) -> dict:
        if "WHERE" not in query.upper() or not params:
            return dict(rows)
        return {k: v for k, v in rows.items() if any(
            str(v.get(col, "")) == str(p) for col, p in zip(
                [c.strip().split("=")[0].strip() for c in query.upper().split("WHERE")[1].split("AND")]
                if "WHERE" in query.upper() else [],
                params
            )
        )}

    @staticmethod
    def _row_matches_params(row: dict, query: str, params: list | tuple) -> bool:
        if not params:
            return False
        upper = query.upper()
        if "WHERE" not in upper:
            return False
        where_part = query.split("WHERE")[1] if "WHERE" in query else query.split("where")[1] if "where" in query else ""
        conditions = where_part.split("AND") if where_part else []
        for cond, param in zip(conditions, params):
            col = cond.strip().split("=")[0].strip().split(".")[-1]
            if str(row.get(col, "")) != str(param):
                return False
        return True


class FakeCluster:
    """Fake Cluster that returns a FakeSession."""

    def __init__(self, *args, **kwargs) -> None:
        _ = args, kwargs

    def connect(self) -> FakeSession:
        return FakeSession()

    def shutdown(self) -> None:
        pass


@pytest.fixture(autouse=True)
def fake_cassandra(monkeypatch):
    """Replace the Cassandra Cluster with the in-memory fake."""
    monkeypatch.setattr(
        "src.core.connectors.cassandra.adapter.Cluster",
        FakeCluster,
    )
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.probe  # rtt-2026-06-12 INST3: KEEP-AS-PROBE pending operator REQ-binding


def test_adapter_capabilities_and_catalogue_calls() -> None:
    """Test capability report, validation, namespace listing, and entity listing."""
    connector = CassandraConnector(host="127.0.0.1")
    assert connector.capability_report()["source_type"] == "cassandra"
    assert connector.capability_report()["supports"]["content_search"] is False
    assert connector.validate_profile()["cluster_name"] == "test-cluster"
    namespaces = connector.list_namespaces()
    assert any(item["name"] == "test_ks" for item in namespaces)
    entities = connector.list_entities("test_ks")
    assert any(item["name"] == "widgets" for item in entities)
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.probe  # rtt-2026-06-12 INST3: KEEP-AS-PROBE pending operator REQ-binding


def test_adapter_data_and_schema_operations() -> None:
    """Test CRUD, schema changes, and relationship inference."""
    connector = CassandraConnector(host="127.0.0.1")
    detail = connector.describe_entity("test_ks", "widgets")
    assert detail["document_count"] == 2
    fields = connector.describe_fields("test_ks", "widgets")
    assert any(item["name"] == "owner_id" for item in fields["fields"])
    assert any(item["kind"] == "partition_key" for item in fields["fields"])
    inserted = connector.create(
        "test_ks", "widgets",
        {"_id": "3", "name": "gamma", "owner_id": "u3", "value": 3},
    )
    assert inserted["inserted_id"] == "3"
    assert connector.count("test_ks", "widgets") == 3
    relationships = connector.extract_relationships("test_ks", "widgets")
    assert any(item["field"] == "owner_id" for item in relationships)
    indexes = connector.list_indexes("test_ks", "widgets")
    assert any(item["name"] == "idx_widgets_status" for item in indexes)
    plan = connector.schema_change_plan(
        {
            "operation": "create_entity",
            "namespace": "test_ks",
            "entity": "archive",
            "columns": {"id": "text", "data": "text"},
            "primary_key": "id",
        }
    )
    assert plan["dry_run"] is True
    applied = connector.schema_change_apply(plan)
    assert applied["entity_created"] is True
    drop = connector.schema_change_plan(
        {"operation": "drop_entity", "namespace": "test_ks", "entity": "archive"}
    )
    dropped = connector.schema_change_apply(drop)
    assert dropped["entity_dropped"] is True
