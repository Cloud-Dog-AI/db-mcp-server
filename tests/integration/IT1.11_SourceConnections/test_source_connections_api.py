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
# Description: W28A-871 source-connections API integration coverage.
# Related requirements: W28A-871 DM-P-07, CW-DA1, CW-DA6
# Related tests: W871-SC-01..10

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.servers.api.app import create_api_app

pytestmark = [pytest.mark.integration]


def _env_file(tmp_path: Path) -> Path:
    env_file = tmp_path / "env-source-connections"
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
@pytest.mark.req("FR-009")


def test_source_connections_crud_and_referenced_delete_conflict(tmp_path: Path) -> None:
    """Source-connection CRUD should block deletion until referencing profiles are unbound."""
    client = _client(tmp_path)
    headers = {"X-API-Key": "test-api-key"}

    created = client.post(
        "/v1/admin/source-connections",
        headers=headers,
        json={
            "name": "pg_primary",
            "source_type": "postgres",
            "uri_template": "postgresql://example.invalid:5432/w28a871",
            "credentials_ref": "vault.dev.databases.providers.postgres",
            "description": "Primary Postgres source",
        },
    )
    assert created.status_code == 200, created.text
    created_payload = created.json()["data"]
    assert created_payload["name"] == "pg_primary"
    assert created_payload["source_type"] == "postgres"
    assert created_payload["status"] == "not_tested"
    assert created_payload["last_tested_at"] is None

    listed = client.get("/v1/admin/source-connections", headers=headers)
    assert listed.status_code == 200, listed.text
    assert [item["name"] for item in listed.json()["data"]] == ["pg_primary"]

    updated = client.patch(
        "/v1/admin/source-connections/pg_primary",
        headers=headers,
        json={
            "uri_template": "postgresql://example.invalid:5432/w28a871_updated",
            "credentials_ref": "vault.dev.databases.providers.postgres",
            "description": "Updated primary Postgres source",
        },
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["data"]["description"] == "Updated primary Postgres source"
    assert updated.json()["data"]["source_type"] == "postgres"

    profile = client.post(
        "/v1/profiles",
        headers=headers,
        json={
            "name": "pg-primary-profile",
            "source_type": "postgresql",
            "source_connection": "pg_primary",
            "allowed_permissions": ["admin.read", "admin.write", "profile.manage"],
        },
    )
    assert profile.status_code == 200, profile.text
    profile_id = profile.json()["data"]["profile_id"]

    blocked_delete = client.delete("/v1/admin/source-connections/pg_primary", headers=headers)
    assert blocked_delete.status_code == 409, blocked_delete.text
    blocked_payload = blocked_delete.json()
    assert "unbind 1 profile first" in blocked_payload["error"]["message"]

    deleted_profile = client.delete(f"/v1/profiles/{profile_id}", headers=headers)
    assert deleted_profile.status_code == 200, deleted_profile.text

    deleted = client.delete("/v1/admin/source-connections/pg_primary", headers=headers)
    assert deleted.status_code == 200, deleted.text
    assert deleted.json()["data"] == {"deleted": True, "name": "pg_primary"}

    missing = client.get("/v1/admin/source-connections/pg_primary", headers=headers)
    assert missing.status_code == 404, missing.text
