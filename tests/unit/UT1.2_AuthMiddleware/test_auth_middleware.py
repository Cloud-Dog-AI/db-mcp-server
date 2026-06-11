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
# Description: Unit tests for API-key authentication behaviour.
# Related requirements: W28A-274-A deliverables 1, 2, 5
# Related tests: UT1.2

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from src.servers.api.app import create_api_app

pytestmark = pytest.mark.unit
PROJECT_ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture()
def api_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Return a test client for the API surface."""
    monkeypatch.setenv("CLOUD_DOG__FLAT_LOGIN__DEMO_KEYS_DIR", str(tmp_path / "flat_role_keys"))
    client = TestClient(create_api_app(["tests/env-UT"]))
    client.flat_key_dir = tmp_path / "flat_role_keys"  # type: ignore[attr-defined]
    return client


def _flat_key(api_client: TestClient, role: str) -> str:
    return (api_client.flat_key_dir / f"{role}.key").read_text(encoding="utf-8").strip()  # type: ignore[attr-defined]


def test_health_route_is_public(api_client: TestClient) -> None:
    """Health probes must stay reachable without an API key."""
    response = api_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_protected_route_rejects_missing_api_key(api_client: TestClient) -> None:
    """Protected routes must reject unauthenticated callers."""
    response = api_client.get("/v1/ping")
    assert response.status_code == 401


def test_protected_route_accepts_valid_api_key(api_client: TestClient) -> None:
    """Protected routes must accept the configured API key."""
    response = api_client.get("/v1/ping", headers={"X-API-Key": "test-api-key"})
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_api_base_path_override_exposes_prefixed_health_and_ping(monkeypatch: pytest.MonkeyPatch) -> None:
    """API routes should move when api_server.base_path is overridden."""
    monkeypatch.setenv("CLOUD_DOG__API_SERVER__BASE_PATH", "/api/v2")
    client = TestClient(create_api_app([str(PROJECT_ROOT / "tests" / "env-UT")]))

    health = client.get("/api/v2/health")
    ping = client.get("/api/v2/ping", headers={"X-API-Key": "test-api-key"})

    assert health.status_code == 200
    assert ping.status_code == 200


def test_auth_me_returns_api_key_principal(api_client: TestClient) -> None:
    """The API-key WebUI identity endpoint returns the managed key owner's flat role."""
    response = api_client.get("/v1/auth/me", headers={"X-API-Key": _flat_key(api_client, "read-only")})

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["username"] == "flat-read-only"
    assert payload["roles"] == ["read-only"]
    assert "data.read" in payload["permissions"]
    assert "data.create" not in payload["permissions"]


def test_read_only_key_is_forbidden_on_api_write(api_client: TestClient) -> None:
    """A read-only API key must receive 403 on write methods."""
    response = api_client.post(
        "/v1/users",
        headers={"X-API-Key": _flat_key(api_client, "read-only")},
        json={"username": "blocked", "display_name": "Blocked"},
    )

    assert response.status_code == 403
