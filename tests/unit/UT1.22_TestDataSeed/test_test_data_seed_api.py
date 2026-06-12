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
# Description: W28A-871 gated test-data seed API coverage.
# Related requirements: W28A-871 CW-TD2
# Related tests: UT1.22

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.servers.api.app import create_api_app

pytestmark = [pytest.mark.unit]


def _env_file(tmp_path: Path) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    env_file = tmp_path / "env-test-data-seed"
    env_file.write_text(
        "\n".join(
            [
                "TEST_ENV_TIER=UT",
                "CLOUD_DOG__API_SERVER__PORT=8086",
                "CLOUD_DOG__WEB_SERVER__PORT=8087",
                "CLOUD_DOG__MCP_SERVER__PORT=8088",
                "CLOUD_DOG__A2A_SERVER__PORT=8089",
                "CLOUD_DOG__AUTH__API_KEY=test-api-key",
                f"CLOUD_DOG__METADATA_STORE__URI=sqlite:///{tmp_path / 'metadata.db'}",
                f"CLOUD_DOG__AUDIT_STORE__URI=sqlite:///{tmp_path / 'audit.db'}",
                f"CLOUD_DOG__JOBS__SQL_DATABASE_URL=sqlite:///{tmp_path / 'jobs.db'}",
                f"CLOUD_DOG__SEARCH__DISCOVERY_INDEX_PATH={tmp_path / 'discovery-index.db'}",
            ]
        ),
        encoding="utf-8",
    )
    return env_file


def _client(tmp_path: Path) -> TestClient:
    return TestClient(create_api_app([str(_env_file(tmp_path))]))


def test_test_data_seed_is_forbidden_outside_allowed_runtime_profiles(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RUNTIME_PROFILE", "prod")
    client = _client(tmp_path / "blocked")
    response = client.post(
        "/v1/admin/test-data/seed",
        headers={"X-API-Key": "test-api-key"},
        json={
            "dataset_id": "w28a871_sqlite",
            "connection_name": "uat-sqlite",
        },
    )
    assert response.status_code == 403, response.text
    assert "RUNTIME_PROFILE=preprod" in response.json()["error"]["message"]


def test_test_data_seed_runs_sqlite_fixture_when_runtime_profile_is_allowed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RUNTIME_PROFILE", "local-docker")
    client = _client(tmp_path / "allowed")
    target_db = tmp_path / "allowed" / "w28a871.sqlite"
    create_response = client.post(
        "/v1/admin/source-connections",
        headers={"X-API-Key": "test-api-key"},
        json={
            "name": "uat-sqlite",
            "source_type": "sqlite",
            "uri_template": f"sqlite:///{target_db}",
            "description": "W28A-871 local seed target",
            "status": "not_tested",
        },
    )
    assert create_response.status_code == 200, create_response.text

    response = client.post(
        "/v1/admin/test-data/seed",
        headers={"X-API-Key": "test-api-key"},
        json={
            "dataset_id": "w28a871_sqlite",
            "connection_name": "uat-sqlite",
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["ok"] is True
    assert data["runtime_profile"] == "local-docker"
    assert data["dataset_id"] == "w28a871_sqlite"
    assert data["connection_name"] == "uat-sqlite"
    assert data["counts"] == {"users": 5, "orders": 7}
    with sqlite3.connect(target_db) as connection:
        assert connection.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 5
        assert connection.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 7


def test_test_data_seed_rejects_unknown_dataset(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RUNTIME_PROFILE", "preprod")
    client = _client(tmp_path / "unknown")

    response = client.post(
        "/v1/admin/test-data/seed",
        headers={"X-API-Key": "test-api-key"},
        json={
            "dataset_id": "w28a871_unknown",
            "connection_name": "uat-sqlite",
        },
    )
    assert response.status_code == 422, response.text
    assert "Unknown dataset_id" in response.json()["error"]["message"]


def test_test_data_seed_rejects_unknown_connection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RUNTIME_PROFILE", "preprod")
    client = _client(tmp_path / "missing-connection")

    response = client.post(
        "/v1/admin/test-data/seed",
        headers={"X-API-Key": "test-api-key"},
        json={
            "dataset_id": "w28a871_sqlite",
            "connection_name": "missing-sqlite",
        },
    )
    assert response.status_code == 404, response.text
    assert "Source connection not found" in response.json()["error"]["message"]
