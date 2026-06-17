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
# Description: Unit tests for the db-mcp A2A websocket surface.
# Related requirements: W28A-274-A deliverables 1, 2
# Related tests: W28A-497

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
import pytest
from starlette.websockets import WebSocketDisconnect

from src.servers.a2a.app import create_a2a_app

pytestmark = pytest.mark.unit


@pytest.fixture()
def a2a_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Return a test client for the A2A surface."""
    monkeypatch.setenv("CLOUD_DOG__FLAT_LOGIN__DEMO_KEYS_DIR", str(tmp_path / "flat_role_keys"))
    client = TestClient(create_a2a_app(["tests/env-UT"]))
    client.flat_key_dir = tmp_path / "flat_role_keys"  # type: ignore[attr-defined]
    return client


def _flat_key(a2a_client: TestClient, role: str) -> str:
    return (a2a_client.flat_key_dir / f"{role}.key").read_text(encoding="utf-8").strip()  # type: ignore[attr-defined]
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-021")


def test_a2a_root_reports_websocket_path(a2a_client: TestClient) -> None:
    """The A2A metadata route should advertise the websocket path."""
    response = a2a_client.get("/", headers={"X-API-Key": "test-api-key"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["surface"] == "a2a"
    assert payload["websocket_path"] == "/a2a/ws"
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-021")


def test_a2a_websocket_accepts_valid_api_key_and_replies_to_health(a2a_client: TestClient) -> None:
    """The websocket endpoint should accept a valid API key and answer health probes."""
    with a2a_client.websocket_connect("/a2a/ws?api_key=test-api-key") as websocket:
        websocket.send_text("health")
        assert websocket.receive_json() == {"topic": "health", "status": "ok", "surface": "a2a"}
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-021")


def test_a2a_websocket_proxy_alias_accepts_valid_api_key(a2a_client: TestClient) -> None:
    """The proxy-facing websocket alias should mirror the canonical A2A route."""
    with a2a_client.websocket_connect("/ws?api_key=test-api-key") as websocket:
        websocket.send_text("health")
        assert websocket.receive_json() == {"topic": "health", "status": "ok", "surface": "a2a"}
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-021")


def test_a2a_websocket_rejects_missing_api_key(a2a_client: TestClient) -> None:
    """The websocket endpoint should reject unauthenticated callers."""
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with a2a_client.websocket_connect("/a2a/ws"):
            pass
    assert exc_info.value.code == 4401
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-021")


def test_a2a_task_rejects_missing_api_key(a2a_client: TestClient) -> None:
    """A2A task submission must not be anonymous."""
    response = a2a_client.post("/a2a/tasks", json={"id": "anon", "skill_id": "health", "input": {"text": ""}})

    assert response.status_code == 401
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-021")


def test_a2a_read_only_key_is_forbidden_on_write_task(a2a_client: TestClient) -> None:
    """A read-only key must not be promoted to the A2A synthetic admin."""
    response = a2a_client.post(
        "/a2a/tasks",
        headers={"X-API-Key": _flat_key(a2a_client, "read-only")},
        json={"id": "ro-write", "skill_id": "data_update", "input": {"text": "{}"}},
    )

    assert response.status_code == 403
