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
# Description: System test for the PostgreSQL adapter against a real PostgreSQL runtime.
# Related requirements: CN-01

from __future__ import annotations

import time
from pathlib import Path

import pytest

from src.common.config_loader import load_runtime_config
from src.core.connectors.service import ConnectorManager

pytestmark = [pytest.mark.system, pytest.mark.timeout(240)]

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class DummyRuntime:
    def __init__(self, config) -> None:
        self.config = config


def _connector():
    config = load_runtime_config(
        [
            str(PROJECT_ROOT / "tests/env-ST"),
            str(PROJECT_ROOT / "tests/env-postgresql"),
        ]
    )
    manager = ConnectorManager(DummyRuntime(config))
    return manager._build_postgresql_connector({"source_connection": "default"})


def test_postgresql_connector_against_real_runtime() -> None:
    connector = _connector()
    namespace = "public"
    entity = f"w28a554_pg_widgets_{int(time.time())}"
    index_name = f"{entity}_owner_idx"
    try:
        namespaces = connector.list_namespaces()
        assert any(item["name"] == namespace for item in namespaces)

        connector.schema_change_apply(
            {
                "operation": "create_entity",
                "namespace": namespace,
                "entity": entity,
                "columns": {"id": "integer", "name": "text", "owner_id": "text", "value": "integer"},
                "primary_key": "id",
            }
        )
        try:
            fields = connector.describe_fields(namespace, entity)
            assert any(item["name"] == "owner_id" for item in fields["fields"])

            created = connector.create(namespace, entity, {"id": 1, "name": "alpha", "owner_id": "u1", "value": 10})
            assert created["document"]["owner_id"] == "u1"

            rows = connector.read(namespace, entity, {"id": 1}, limit=5)
            assert len(rows) == 1
            assert rows[0]["name"] == "alpha"

            updated = connector.update(namespace, entity, {"id": 1}, {"$set": {"value": 11}})
            assert updated["modified_count"] == 1
            assert connector.count(namespace, entity, {"id": 1}) == 1

            plan = connector.schema_change_plan(
                {
                    "operation": "create_index",
                    "namespace": namespace,
                    "entity": entity,
                    "column": "owner_id",
                    "name": index_name,
                }
            )
            applied = connector.schema_change_apply(plan)
            assert applied["index_name"] == index_name
            assert any(item["name"] == index_name for item in connector.list_indexes(namespace, entity))

            deleted = connector.delete(namespace, entity, {"id": 1})
            assert deleted["deleted_count"] == 1
            assert connector.count(namespace, entity, {"id": 1}) == 0
        finally:
            connector.schema_change_apply(
                {
                    "operation": "drop_entity",
                    "namespace": namespace,
                    "entity": entity,
                }
            )
    finally:
        connector.close()
