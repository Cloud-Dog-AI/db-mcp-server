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
# Description: Unit tests for PS-30 runtime-config and SPA history serving.
# Related requirements: W28A-274-J deliverables 2, 4, 5
# Related tests: UT1.11, ST1.8

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from src.servers.web.app import create_web_app

pytestmark = pytest.mark.unit

PROJECT_ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture()
def web_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    ui_dist = tmp_path / "ui" / "dist"
    assets = ui_dist / "assets"
    assets.mkdir(parents=True)
    (ui_dist / "index.html").write_text("<html><body><div id='root'>db-mcp-webui</div></body></html>", encoding="utf-8")
    (assets / "app.js").write_text("console.log('ok');", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    return TestClient(create_web_app([str(PROJECT_ROOT / "tests" / "env-UT")]))


def test_runtime_config_is_served_for_spa_bootstrap(web_client: TestClient) -> None:
    response = web_client.get("/runtime-config.js")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/javascript")
    assert 'window.__RUNTIME_CONFIG__' in response.text
    assert '"AUTH_MODE":"api_key"' in response.text
    assert '"API_KEY_HEADER":"X-API-Key"' in response.text


def test_history_routes_resolve_to_index_html(web_client: TestClient) -> None:
    response = web_client.get("/search")
    assert response.status_code == 200
    assert "db-mcp-webui" in response.text


def test_dist_assets_are_served_from_ui_dist(web_client: TestClient) -> None:
    response = web_client.get("/assets/app.js")
    assert response.status_code == 200
    assert "console.log('ok');" in response.text
