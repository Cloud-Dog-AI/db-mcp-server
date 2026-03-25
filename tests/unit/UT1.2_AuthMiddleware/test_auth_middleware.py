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

from fastapi.testclient import TestClient
import pytest

from src.servers.api.app import create_api_app

pytestmark = pytest.mark.unit


@pytest.fixture()
def api_client() -> TestClient:
    """Return a test client for the API surface."""
    return TestClient(create_api_app(["tests/env-UT"]))


def test_health_route_is_public(api_client: TestClient) -> None:
    """Health probes must stay reachable without an API key."""
    response = api_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_protected_route_rejects_missing_api_key(api_client: TestClient) -> None:
    """Protected routes must reject unauthenticated callers."""
    response = api_client.get("/api/v1/ping")
    assert response.status_code == 401


def test_protected_route_accepts_valid_api_key(api_client: TestClient) -> None:
    """Protected routes must accept the configured API key."""
    response = api_client.get("/api/v1/ping", headers={"X-API-Key": "test-api-key"})
    assert response.status_code == 200
    assert response.json()["ok"] is True
