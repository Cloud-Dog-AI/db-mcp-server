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
# Description: W28A-871 saved-query API integration coverage.
# Related requirements: W28A-871 DM-DB-01, CW-DA5
# Related tests: W871-API-SQ-01

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.servers.api.app import create_api_app

pytestmark = [pytest.mark.integration]


def _env_file(tmp_path: Path) -> Path:
    env_file = tmp_path / "env-saved-queries"
    env_file.write_text(
        "\n".join(
            [
                "TEST_ENV_TIER=IT",
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
@pytest.mark.IT
@pytest.mark.mcp
@pytest.mark.probe  # rtt-2026-06-12 INST3: KEEP-AS-PROBE pending operator REQ-binding


def test_saved_queries_crud_conflict_and_delete(tmp_path: Path) -> None:
    client = _client(tmp_path)
    headers = {"X-API-Key": "test-api-key"}

    created = client.post(
        "/v1/admin/saved-queries",
        headers=headers,
        json={
            "page_key": "data-browser",
            "name": "Active users",
            "description": "Users with active status",
            "payload": {
                "filters": [{"field": "status", "operator": "eq", "value": "active"}],
                "limit": 50,
            },
            "shared": True,
        },
    )
    assert created.status_code == 200, created.text
    created_payload = created.json()["data"]
    assert created_payload["id"] > 0
    assert created_payload["user_id"] == "bootstrap-admin"
    assert created_payload["page_key"] == "data-browser"
    assert created_payload["payload"]["limit"] == 50
    query_id = created_payload["id"]

    duplicate = client.post(
        "/v1/admin/saved-queries",
        headers=headers,
        json={
            "page_key": "data-browser",
            "name": "Active users",
            "payload": {"filters": []},
        },
    )
    assert duplicate.status_code == 409, duplicate.text
    assert duplicate.json()["error"]["code"] == "CONFLICT"

    listed = client.get("/v1/admin/saved-queries?page_key=data-browser", headers=headers)
    assert listed.status_code == 200, listed.text
    assert [item["name"] for item in listed.json()["data"]] == ["Active users"]

    fetched = client.get(f"/v1/admin/saved-queries/{query_id}", headers=headers)
    assert fetched.status_code == 200, fetched.text
    assert fetched.json()["data"]["name"] == "Active users"

    updated = client.patch(
        f"/v1/admin/saved-queries/{query_id}",
        headers=headers,
        json={
            "name": "Recent active users",
            "payload": {
                "filters": [{"field": "created_at", "operator": "gte", "value": "2026-01-01"}],
                "limit": 25,
            },
            "shared": False,
        },
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["data"]["name"] == "Recent active users"
    assert updated.json()["data"]["payload"]["limit"] == 25
    assert updated.json()["data"]["shared"] is False

    deleted = client.delete(f"/v1/admin/saved-queries/{query_id}", headers=headers)
    assert deleted.status_code == 200, deleted.text
    assert deleted.json()["data"] == {"deleted": True, "id": query_id}

    missing = client.get(f"/v1/admin/saved-queries/{query_id}", headers=headers)
    assert missing.status_code == 404, missing.text
