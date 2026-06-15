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
# Description: W28A-871 discovery API/cache contract coverage.
# Related requirements: W28A-871 DM-P-09, DM-CAT-04, DM-S-01, CW-DA2, CW-DA3
# Related tests: UT1.20

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from src.servers.api.app import create_api_app

pytestmark = [pytest.mark.unit]


def _env_file(tmp_path: Path) -> Path:
    env_file = tmp_path / "env-discovery-api"
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
        self._manager.calls["namespaces"] += 1
        return list(self._manager.namespaces)

    def list_entities(self, namespace: str) -> list[dict[str, Any]]:
        self._manager.calls[f"entities:{namespace}"] += 1
        return list(self._manager.entities_by_namespace[namespace])

    def describe_fields(self, namespace: str, entity: str) -> dict[str, Any]:
        self._manager.calls[f"fields:{namespace}:{entity}"] += 1
        return {"fields": list(self._manager.fields_by_entity[(namespace, entity)])}

    def close(self) -> None:
        self._manager.calls["close"] += 1


class _FakeConnectorManager:
    def __init__(self, runtime: Any) -> None:
        self._runtime = runtime
        self.calls: Counter[str] = Counter()
        self.namespaces = [{"name": "public", "type": "schema"}]
        self.entities_by_namespace = {
            "public": [
                {"name": "users", "type": "table"},
                {"name": "orders", "type": "table"},
            ],
        }
        self.fields_by_entity = {
            ("public", "users"): [
                {"name": "id", "types": ["integer"], "nullable": False},
                {"name": "email", "types": ["varchar"], "nullable": False},
            ],
        }

    def for_profile(self, profile_id: str) -> _FakeSession:
        return _FakeSession(
            profile=self._runtime.access_control.get_profile(profile_id),
            connector=_FakeConnector(self),
        )

    def for_profile_payload(self, profile: dict[str, Any]) -> _FakeSession:
        self.calls["profile_payload"] += 1
        return _FakeSession(profile=profile, connector=_FakeConnector(self))

    def execute(
        self,
        request,
        *,
        profile_id: str,
        permission: str,
        audit_action: str,
        audit_target_id: str,
        callback,
    ) -> Any:
        self._runtime.access_control.require_request_permission(
            request,
            permission=permission,
            profile_id=profile_id,
            audit_resource_type="profile",
            audit_resource_id=audit_target_id,
        )
        return callback(self.for_profile(profile_id))

    def ensure_namespace_allowed(self, profile: dict[str, Any], namespace: str) -> None:
        allowed = [str(item) for item in profile.get("namespaces", []) if str(item).strip()]
        if allowed and namespace not in allowed:
            raise AssertionError(f"unexpected denied namespace in test: {namespace}")

    def ensure_entity_allowed(self, profile: dict[str, Any], namespace: str, entity: str) -> None:
        self.ensure_namespace_allowed(profile, namespace)
        allowed = [str(item) for item in profile.get("entities", []) if str(item).strip()]
        if allowed and entity not in allowed and f"{namespace}.{entity}" not in allowed:
            raise AssertionError(f"unexpected denied entity in test: {namespace}.{entity}")

    def filter_namespaces(
        self,
        profile: dict[str, Any],
        namespaces: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        allowed = [str(item) for item in profile.get("namespaces", []) if str(item).strip()]
        if not allowed:
            return namespaces
        return [item for item in namespaces if str(item.get("name")) in allowed]

    def filter_entities(
        self,
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


def _client(tmp_path: Path) -> tuple[TestClient, _FakeConnectorManager]:
    app = create_api_app([str(_env_file(tmp_path))])
    fake_connectors = _FakeConnectorManager(app.state.runtime)
    app.state.runtime.connectors = fake_connectors
    app.state.runtime.access_control.bind_connector_manager(fake_connectors)
    return TestClient(app), fake_connectors
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-003")


def test_discovery_routes_cache_profile_results_and_discover_connection_namespaces(tmp_path: Path) -> None:
    client, fake_connectors = _client(tmp_path)
    headers = {"X-API-Key": "test-api-key"}

    profile_response = client.post(
        "/v1/profiles",
        headers=headers,
        json={
            "name": "pg-primary-profile",
            "source_type": "postgresql",
            "source_connection": "postgresql://example.invalid:5432/w28a871",
            "allowed_permissions": ["catalog.read", "schema.read", "profile.manage", "admin.write"],
        },
    )
    assert profile_response.status_code == 200, profile_response.text
    profile_id = profile_response.json()["data"]["profile_id"]

    first_namespaces = client.post(
        "/v1/admin/discovery/namespaces",
        headers=headers,
        json={"profile_id": profile_id, "ttl_seconds": 600},
    )
    assert first_namespaces.status_code == 200, first_namespaces.text
    assert first_namespaces.json()["data"]["items"] == [{"name": "public", "type": "schema"}]
    assert first_namespaces.json()["data"]["cache"]["status"] == "refreshed"
    assert fake_connectors.calls["namespaces"] == 1

    fake_connectors.namespaces = [{"name": "analytics", "type": "schema"}]
    cached_namespaces = client.post(
        "/v1/admin/discovery/namespaces",
        headers=headers,
        json={"profile_id": profile_id, "ttl_seconds": 600},
    )
    assert cached_namespaces.status_code == 200, cached_namespaces.text
    assert cached_namespaces.json()["data"]["items"] == [{"name": "public", "type": "schema"}]
    assert cached_namespaces.json()["data"]["cache"]["status"] == "hit"
    assert fake_connectors.calls["namespaces"] == 1

    refreshed_namespaces = client.post(
        "/v1/admin/discovery/namespaces",
        headers=headers,
        json={"profile_id": profile_id, "refresh": True, "ttl_seconds": 600},
    )
    assert refreshed_namespaces.status_code == 200, refreshed_namespaces.text
    assert refreshed_namespaces.json()["data"]["items"] == [{"name": "analytics", "type": "schema"}]
    assert refreshed_namespaces.json()["data"]["cache"]["status"] == "refreshed"
    assert fake_connectors.calls["namespaces"] == 2

    entities = client.post(
        "/v1/admin/discovery/entities",
        headers=headers,
        json={"profile_id": profile_id, "namespace": "public"},
    )
    assert entities.status_code == 200, entities.text
    assert [item["name"] for item in entities.json()["data"]["items"]] == ["users", "orders"]

    fields = client.post(
        "/v1/admin/discovery/fields",
        headers=headers,
        json={"profile_id": profile_id, "namespace": "public", "entity": "users"},
    )
    assert fields.status_code == 200, fields.text
    assert [item["name"] for item in fields.json()["data"]["items"]] == ["id", "email"]

    source_connection = client.post(
        "/v1/admin/source-connections",
        headers=headers,
        json={
            "name": "pg_primary",
            "source_type": "postgresql",
            "uri_template": "postgresql://example.invalid:5432/w28a871",
        },
    )
    assert source_connection.status_code == 200, source_connection.text

    connection_namespaces = client.post(
        "/v1/admin/discovery/namespaces",
        headers=headers,
        json={"connection_name": "pg_primary"},
    )
    assert connection_namespaces.status_code == 200, connection_namespaces.text
    assert connection_namespaces.json()["data"]["cache"]["status"] == "uncached"
    assert fake_connectors.calls["profile_payload"] == 1
