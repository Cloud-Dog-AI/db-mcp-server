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
# Description: W28A-871 profile scope and schema approval API coverage.
# Related requirements: W28A-871 DM-P-10, DM-S-05, CW-DA4
# Related tests: UT1.21

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from src.core.connectors.service import ConnectorManager
from src.core.schema.models import SchemaChangeOperation, SchemaChangePlan, SchemaChangeRecord
from src.servers.api.app import create_api_app

pytestmark = [pytest.mark.unit]


def _env_file(tmp_path: Path) -> Path:
    env_file = tmp_path / "env-profile-scope-schema"
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


@dataclass(slots=True)
class _FakeSession:
    profile: dict[str, Any]
    connector: Any


class _FakeConnector:
    def __init__(self, manager: "_FakeConnectorManager") -> None:
        self._manager = manager

    def list_namespaces(self) -> list[dict[str, Any]]:
        self._manager.calls.append("list_namespaces")
        return [
            {"name": "public", "type": "schema"},
            {"name": "internal", "type": "schema"},
        ]

    def list_entities(self, namespace: str) -> list[dict[str, Any]]:
        self._manager.calls.append(f"list_entities:{namespace}")
        return {
            "public": [{"name": "users", "type": "table"}],
            "internal": [{"name": "secrets", "type": "table"}],
        }[namespace]

    def close(self) -> None:
        self._manager.calls.append("close")


class _FakeConnectorManager:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def for_profile_payload(self, profile: dict[str, Any]) -> _FakeSession:
        self.calls.append("for_profile_payload")
        return _FakeSession(profile=profile, connector=_FakeConnector(self))

    @staticmethod
    def filter_namespaces(
        profile: dict[str, Any],
        namespaces: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        allowed = [str(item) for item in profile.get("namespaces", []) if str(item).strip()]
        if not allowed:
            return namespaces
        return [item for item in namespaces if str(item.get("name")) in allowed]

    @staticmethod
    def filter_entities(
        profile: dict[str, Any],
        namespace: str,
        entities: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        allowed = [str(item) for item in profile.get("entities", []) if str(item).strip()]
        if not allowed:
            return entities
        return [
            item
            for item in entities
            if str(item.get("name")) in allowed or f"{namespace}.{item.get('name')}" in allowed
        ]


def _client(tmp_path: Path) -> TestClient:
    return TestClient(create_api_app([str(_env_file(tmp_path))]))
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-004")


def test_profile_scope_route_dry_runs_filtered_profile_without_persisting(tmp_path: Path) -> None:
    client = _client(tmp_path)
    runtime = client.app.state.runtime
    fake_connectors = _FakeConnectorManager()
    runtime.connectors = fake_connectors
    runtime.access_control.bind_connector_manager(fake_connectors)
    headers = {"X-API-Key": "test-api-key"}

    profile_response = client.post(
        "/v1/profiles",
        headers=headers,
        json={
            "name": "scope-profile",
            "source_type": "postgresql",
            "source_connection": "postgresql://example.invalid:5432/w28a871",
            "allowed_permissions": ["profile.manage"],
        },
    )
    assert profile_response.status_code == 200, profile_response.text
    profile_id = profile_response.json()["data"]["profile_id"]

    scoped = client.post(
        f"/v1/admin/profiles/{profile_id}/test-scope",
        headers=headers,
        json={"profile": {"namespaces": ["public"], "entities": ["public.users"]}},
    )
    assert scoped.status_code == 200, scoped.text
    data = scoped.json()["data"]
    assert data["ok"] is True
    assert data["namespace_count"] == 1
    assert data["entity_count"] == 1
    assert data["namespaces"] == [{"name": "public", "type": "schema"}]
    assert [item["name"] for item in data["entities_by_namespace"]["public"]] == ["users"]
    assert "close" in fake_connectors.calls

    persisted = client.get(f"/v1/profiles/{profile_id}", headers=headers)
    assert persisted.status_code == 200, persisted.text
    assert persisted.json()["data"]["namespaces"] == []
    assert persisted.json()["data"]["entities"] == []
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-004")


def test_schema_change_approve_route_marks_plan_approved(tmp_path: Path) -> None:
    client = _client(tmp_path)
    runtime = client.app.state.runtime
    headers = {"X-API-Key": "test-api-key"}

    profile_response = client.post(
        "/v1/profiles",
        headers=headers,
        json={
            "name": "schema-profile",
            "source_type": "postgresql",
            "source_connection": "postgresql://example.invalid:5432/w28a871",
            "allowed_permissions": ["schema.change.approve"],
        },
    )
    assert profile_response.status_code == 200, profile_response.text
    profile_id = profile_response.json()["data"]["profile_id"]

    record = SchemaChangeRecord(
        plan=SchemaChangePlan(
            profile_id=profile_id,
            source_type="postgresql",
            operations=[
                SchemaChangeOperation(
                    op_type="create_index",
                    namespace="public",
                    entity="users",
                    parameters={"name": "users_email_idx", "column": "email"},
                )
            ],
            dry_run_result={"summary": {"operation_count": 1}},
            requires_approval=True,
        ),
        status="planned",
        planned_by="bootstrap-admin",
    )
    runtime.schema_changes._repository.upsert(record)

    approved = client.post(
        f"/v1/schema-changes/{record.plan_id}/approve",
        headers=headers,
        json={"target_name": "users"},
    )
    assert approved.status_code == 200, approved.text
    data = approved.json()["data"]
    assert data["plan_id"] == record.plan_id
    assert data["approved"] is True
    assert data["status"] == "approved"
    assert data["approved_by"] == "bootstrap-admin"
    assert data["audit_trail"][-1]["action"] == "schema.change.approve"
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-004")


def test_connector_manager_resolves_named_source_connection() -> None:
    class _AccessControl:
        def get_source_connection(self, name: str) -> dict[str, Any]:
            assert name == "pg_primary"
            return {"uri_template": "postgresql://example.invalid:5432/w28a871"}

    manager = ConnectorManager(type("Runtime", (), {"access_control": _AccessControl()})())
    assert (
        manager._resolve_source_connection({"source_connection": "pg_primary"})
        == "postgresql://example.invalid:5432/w28a871"
    )
