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
# Description: Unit tests for db-mcp-server config loading and runtime config JS.
# Related requirements: W28A-274-A deliverables 1, 2, 5
# Related tests: UT1.1

from __future__ import annotations

from fastapi.testclient import TestClient
import pytest

from src.common.config_loader import load_runtime_config
from src.servers.web.app import create_web_app

pytestmark = pytest.mark.unit


def test_load_runtime_config_reads_ports_and_auth_key() -> None:
    """Config should honour env overrides supplied via `--env`."""
    config = load_runtime_config(["tests/env-UT"])
    assert config.get("api_server.port") == 8086
    assert config.get("web_server.port") == 8087
    assert config.get("auth.api_key") == "test-api-key"


def test_runtime_config_js_exposes_web_settings() -> None:
    """The web surface should render `runtime-config.js` for the future SPA."""
    client = TestClient(create_web_app(["tests/env-UT"]))
    response = client.get("/runtime-config.js")
    assert response.status_code == 200
    assert "window.__RUNTIME_CONFIG__" in response.text
    assert "API_BASE_URL" in response.text
