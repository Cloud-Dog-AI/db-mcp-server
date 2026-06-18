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

import httpx
from fastapi.testclient import TestClient
import pytest
from cloud_dog_api_kit.middleware import TimeoutMiddleware

from src.servers.web.app import create_web_app
from tests.helpers.server_runtime import service_base_url

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
@pytest.mark.UT
@pytest.mark.webui
@pytest.mark.req("FR-022")


def test_runtime_config_is_served_for_spa_bootstrap(web_client: TestClient) -> None:
    response = web_client.get("/runtime-config.js")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/javascript")
    assert 'window.__RUNTIME_CONFIG__' in response.text
    # W28A-732-R5 (login-contract reopen): the WebUI front door is username/password
    # (cookie). The SPA bundle branches AUTH_MODE === "cookie" ? cookie : api_key,
    # so the served runtime-config MUST advertise "cookie" — never "api_key".
    assert '"AUTH_MODE": "cookie"' in response.text
    assert '"AUTH_MODE": "api_key"' not in response.text
    assert '"API_KEY_HEADER": "X-API-Key"' in response.text
    assert '"A2A_BASE_URL": __origin' in response.text
@pytest.mark.UT
@pytest.mark.webui
@pytest.mark.req("FR-022")


def test_history_routes_resolve_to_index_html(web_client: TestClient) -> None:
    for path in (
        "/search",
        "/audit-log",
        "/developer/api-docs",
        "/developer/mcp-console",
        "/developer/a2a-console",
        "/system/jobs",
        "/system/settings",
        "/system/about",
        "/admin/users",
        "/admin/api-keys",
        "/admin/rbac",
    ):
        response = web_client.get(path)
        assert response.status_code == 200
        assert "db-mcp-webui" in response.text
@pytest.mark.UT
@pytest.mark.webui
@pytest.mark.req("FR-022")


def test_legacy_webui_routes_redirect_to_canonical_urls(web_client: TestClient) -> None:
    aliases = {
        "/ui/login": "/login",
        "/audit": "/audit-log",
        "/logs": "/audit-log",
        "/idam/users": "/admin/users",
        "/idam/groups": "/admin/groups",
        "/idam/api-keys": "/admin/api-keys",
        "/apikeys": "/admin/api-keys",
        "/api-keys": "/admin/api-keys",
        "/idam/roles": "/admin/roles",
        "/idam/rbac": "/admin/rbac",
        "/rbac": "/admin/rbac",
        "/api-docs": "/developer/api-docs",
        "/docs": "/developer/api-docs",
        "/openapi": "/developer/api-docs",
        "/redoc": "/developer/api-docs",
        "/mcp-console": "/developer/mcp-console",
        "/a2a-console": "/developer/a2a-console",
        "/jobs": "/system/jobs",
        "/settings": "/system/settings",
        "/about": "/system/about",
    }
    for source, target in aliases.items():
        response = web_client.get(f"{source}?actor_id=admin", follow_redirects=False)
        assert response.status_code == 308
        assert response.headers["location"] == f"{target}?actor_id=admin"


@pytest.mark.UT
@pytest.mark.webui
@pytest.mark.req("FR-022")
def test_unknown_extensionless_webui_route_is_not_spa_entry(web_client: TestClient) -> None:
    response = web_client.get("/not-a-real-webui-route")
    assert response.status_code == 404


@pytest.mark.UT
@pytest.mark.webui
@pytest.mark.req("FR-022")
def test_idam_webui_compatibility_reads_are_session_protected(web_client: TestClient) -> None:
    anonymous = web_client.get("/webapi/auth/status")
    assert anonymous.status_code == 401

    api_key_status = web_client.get("/webapi/auth/status", headers={"X-API-Key": "test-api-key"})
    assert api_key_status.status_code == 200
    assert api_key_status.json()["is_system_admin"] is True

    api_key_bindings = web_client.get("/webapi/v1/idam/v1/rbac-bindings", headers={"X-API-Key": "test-api-key"})
    assert api_key_bindings.status_code == 200
    assert api_key_bindings.json() == {"bindings": []}

    login = web_client.post("/auth/login", json={"username": "admin", "password": "test-password"})
    assert login.status_code == 200

    status = web_client.get("/webapi/auth/status")
    assert status.status_code == 200
    assert status.json()["is_system_admin"] is True

    permissions = web_client.get("/webapi/v1/admin/permissions")
    assert permissions.status_code == 200
    assert "permissions" in permissions.json()

    bindings = web_client.get("/webapi/v1/idam/v1/rbac-bindings")
    assert bindings.status_code == 200
    assert bindings.json() == {"bindings": []}


@pytest.mark.UT
@pytest.mark.webui
@pytest.mark.req("FR-022")


def test_dist_assets_are_served_from_ui_dist(web_client: TestClient) -> None:
    response = web_client.get("/assets/app.js")
    assert response.status_code == 200
    assert "console.log('ok');" in response.text
@pytest.mark.UT
@pytest.mark.webui
@pytest.mark.req("FR-022")


def test_cookie_authenticated_browser_proxies_inject_role_key(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """W28A-732-R5: a cookie session injects the session ROLE's flat demo key on the
    MCP/A2A proxies (not the blanket service key), so those tiers — which authorise
    by api-key role — enforce per-role RBAC (read-only writes -> 403)."""
    ui_dist = tmp_path / "ui" / "dist"
    ui_dist.mkdir(parents=True)
    (ui_dist / "index.html").write_text("<html><body><div id='root'>db-mcp-webui</div></body></html>", encoding="utf-8")
    key_dir = tmp_path / "flat_role_keys"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("CLOUD_DOG_WEB_LOGIN_PASSWORD", "test-password")
    monkeypatch.setenv("CLOUD_DOG__FLAT_LOGIN__DEMO_KEYS_DIR", str(key_dir))

    captured: list[dict[str, object]] = []

    async def fake_request(self, method, url, *, content=None, headers=None, **kwargs):
        captured.append({
            "method": method,
            "url": str(url),
            "headers": dict(headers or {}),
        })
        request = httpx.Request(method, str(url), headers=headers, content=content)
        return httpx.Response(200, json={"ok": True}, request=request)

    monkeypatch.setattr(httpx.AsyncClient, "request", fake_request)

    # create_web_app builds access_control, which SEEDS the flat demo keys into
    # key_dir; the admin session must forward its seeded admin role key downstream.
    client = TestClient(create_web_app([str(PROJECT_ROOT / "tests" / "env-UT")]))
    admin_key = (key_dir / "admin.key").read_text(encoding="utf-8").strip()
    login = client.post("/auth/login", json={"username": "admin", "password": "test-password"})
    assert login.status_code == 200

    webmcp = client.get("/webmcp/tools")
    assert webmcp.status_code == 200

    weba2a = client.get("/weba2a/health")
    assert weba2a.status_code == 200

    assert [item["method"] for item in captured] == ["GET", "GET"]
    assert [item["url"] for item in captured] == [
        f"{service_base_url('mcp', PROJECT_ROOT / 'tests' / 'env-UT', default_tier='UT')}/mcp/tools",
        f"{service_base_url('a2a', PROJECT_ROOT / 'tests' / 'env-UT', default_tier='UT')}/a2a/health",
    ]
    assert admin_key and admin_key != "test-api-key"
    for item in captured:
        headers = item["headers"]
        assert headers["x-api-key"] == admin_key
        assert headers["authorization"] == f"Bearer {admin_key}"
        assert "db_web_session=" in headers["cookie"]
@pytest.mark.UT
@pytest.mark.webui
@pytest.mark.req("FR-022")


def test_web_surface_raises_request_timeout_budget() -> None:
    app = create_web_app([str(PROJECT_ROOT / "tests" / "env-UT")])
    for middleware in app.user_middleware:
        if middleware.cls is TimeoutMiddleware:
            assert middleware.kwargs["timeout_seconds"] == 120.0
            break
    else:
        pytest.fail("TimeoutMiddleware not installed")
