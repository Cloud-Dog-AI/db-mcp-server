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
# Description: Unit tests for PostgreSQL/MariaDB connector dispatch and URI resolution.
# Related requirements: CN-01, CFG-01

from __future__ import annotations

import pytest

from src.core.connectors.service import ConnectorManager

pytestmark = pytest.mark.unit


class DummyConfig:
    def __init__(self, values: dict[str, object]) -> None:
        self._values = values

    def get(self, path: str, default: object = None) -> object:
        return self._values.get(path, default)


class DummyAccessControl:
    def __init__(self, profile: dict[str, object]) -> None:
        self._profile = profile

    def get_profile(self, _profile_id: str) -> dict[str, object]:
        return dict(self._profile)

    def get_profile_internal(self, _profile_id: str) -> dict[str, object]:
        return dict(self._profile)


class DummyRuntime:
    def __init__(self, config: DummyConfig, profile: dict[str, object]) -> None:
        self.config = config
        self.access_control = DummyAccessControl(profile)
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-018")


def test_connector_manager_supports_postgresql_source_type(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.core.connectors.postgresql.adapter.PostgreSQLConnector.validate_profile",
        lambda self: {"ok": True},
    )
    runtime = DummyRuntime(
        DummyConfig({"connectors.postgresql.default_uri": "postgresql://db-user:db-pass@db2.db.example.com:5432/dbmcp_test"}),
        {"source_type": "postgresql", "source_connection": "default"},
    )
    manager = ConnectorManager(runtime)

    session = manager.for_profile("profile-1")

    assert session.profile["source_type"] == "postgresql"
    assert session.connector.uri.startswith("postgresql+psycopg://db-user:db-pass@db2.db.example.com:5432/")
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-018")


def test_connector_manager_supports_mariadb_source_type(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.core.connectors.mariadb.adapter.MariaDBConnector.validate_profile",
        lambda self: {"ok": True},
    )
    runtime = DummyRuntime(
        DummyConfig({"connectors.mariadb.default_uri": "mariadb://db-user:db-pass@db1.db.example.com:3306/dbmcp_test"}),
        {"source_type": "mariadb", "source_connection": "default"},
    )
    manager = ConnectorManager(runtime)

    session = manager.for_profile("profile-1")

    assert session.profile["source_type"] == "mariadb"
    assert session.connector.uri.startswith("mysql+pymysql://db-user:db-pass@db1.db.example.com:3306/")
