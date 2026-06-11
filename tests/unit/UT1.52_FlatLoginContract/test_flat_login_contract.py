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
# Description: W28A-732-R5 flat username/password WebUI login-contract tests.
# Proves the platform flat-login contract: cookie AUTH_MODE, three flat roles
# (admin / read-write / read-only) logging in by username+password, read-only
# write -> 403, and anon -> 401.
# Related requirements: W28A-732-R5 (login-contract reopen)
# Related tests: UT1.52, ST1.8, AT_WEBUI_E2E

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from cloud_dog_api_kit.web.proxy import ProxyResponse, WebApiProxy

from src.servers.web.app import create_web_app

pytestmark = [pytest.mark.unit, pytest.mark.security, pytest.mark.fast]

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENV_UT = str(PROJECT_ROOT / "tests" / "env-UT")
_COOKIE_NAME = "db_web_session"

# env-UT admin password; read-write/read-only use the in-code estate-canonical
# demo defaults so all three flat roles log in without a Terraform/Vault write.
ADMIN_CREDS = ("admin", "test-password")
READ_WRITE_CREDS = ("read-write", "BlueRiverChair")
READ_ONLY_CREDS = ("read-only", "GreenRiverDesk")

WRITE_PATH = "/webapi/v1/profiles"


@pytest.fixture()
def web_app(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    ui_dist = tmp_path / "ui" / "dist"
    ui_dist.mkdir(parents=True)
    (ui_dist / "index.html").write_text(
        "<html><body><div id='root'>db-mcp-webui</div></body></html>", encoding="utf-8"
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("CLOUD_DOG__FLAT_LOGIN__DEMO_KEYS_DIR", str(tmp_path / "flat_role_keys"))
    return create_web_app([ENV_UT])


def _login(client: TestClient, username: str, password: str):
    return client.post("/auth/login", json={"username": username, "password": password})


def test_runtime_config_advertises_cookie_not_api_key(web_app) -> None:
    """The WebUI login mode MUST be cookie (username/password), never api_key."""
    client = TestClient(web_app, raise_server_exceptions=False)
    resp = client.get("/runtime-config.js")
    assert resp.status_code == 200
    assert '"AUTH_MODE": "cookie"' in resp.text
    assert '"AUTH_MODE": "api_key"' not in resp.text


@pytest.mark.parametrize(
    ("creds", "role"),
    [
        (ADMIN_CREDS, "admin"),
        (READ_WRITE_CREDS, "read-write"),
        (READ_ONLY_CREDS, "read-only"),
    ],
)
def test_three_flat_roles_login_by_username_password(web_app, creds, role) -> None:
    """admin / read-write / read-only all authenticate by username+password (200)."""
    client = TestClient(web_app, raise_server_exceptions=False)
    resp = _login(client, *creds)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["user"]["roles"] == [role]
    assert client.cookies.get(_COOKIE_NAME), "login must mint a cookie session"

    # /auth/me reflects the same flat role from the cookie session.
    me = client.get("/auth/me")
    assert me.status_code == 200
    assert me.json()["user"]["roles"] == [role]


def test_bad_password_is_unauthorized(web_app) -> None:
    client = TestClient(web_app, raise_server_exceptions=False)
    assert _login(client, "admin", "wrong-password").status_code == 401
    assert _login(client, "read-only", "BlueRiverChair").status_code == 401
    assert _login(client, "ghost", "GreenRiverDesk").status_code == 401


def test_missing_credentials_is_bad_request(web_app) -> None:
    client = TestClient(web_app, raise_server_exceptions=False)
    assert _login(client, "", "").status_code == 400
    assert _login(client, "admin", "").status_code == 400


def test_read_only_write_is_forbidden(web_app) -> None:
    """A read-only session is denied mutations at the web tier (403, inline)."""
    client = TestClient(web_app, raise_server_exceptions=False)
    assert _login(client, *READ_ONLY_CREDS).status_code == 200

    for method in ("POST", "PUT", "PATCH", "DELETE"):
        resp = client.request(method, WRITE_PATH, json={"name": "x"})
        assert resp.status_code == 403, f"{method} must be 403 for read-only: {resp.status_code} {resp.text[:200]}"
        assert resp.json()["role"] == "read-only"


def test_read_only_can_read(web_app, monkeypatch: pytest.MonkeyPatch) -> None:
    """A read-only session may still VIEW data surfaces (GET falls through)."""
    captured: dict = {}

    async def _spy(self, method, path, **kwargs):  # noqa: ANN001
        captured["method"] = method
        return ProxyResponse(status_code=200, data={"items": []})

    monkeypatch.setattr(WebApiProxy, "request", _spy, raising=True)
    client = TestClient(web_app, raise_server_exceptions=False)
    assert _login(client, *READ_ONLY_CREDS).status_code == 200

    resp = client.get(WRITE_PATH)
    assert resp.status_code == 200, resp.text
    assert captured["method"] == "GET"


def test_read_write_can_write_and_forwards_role_principal(web_app, monkeypatch: pytest.MonkeyPatch) -> None:
    """read-write writes fall through and forward the seeded flat-read-write principal."""
    captured: dict = {}

    async def _spy(self, method, path, *, headers=None, **kwargs):  # noqa: ANN001
        captured["method"] = method
        captured["headers"] = {str(k).lower(): v for k, v in (headers or {}).items()}
        return ProxyResponse(status_code=200, data={"ok": True})

    monkeypatch.setattr(WebApiProxy, "request", _spy, raising=True)
    client = TestClient(web_app, raise_server_exceptions=False)
    assert _login(client, *READ_WRITE_CREDS).status_code == 200

    resp = client.post(WRITE_PATH, json={"name": "x"})
    assert resp.status_code == 200, resp.text
    assert captured["method"] == "POST"
    assert captured["headers"].get("x-request-user") == "flat-read-write"
    assert captured["headers"].get("x-request-source") == "webui"


@pytest.mark.parametrize(
    ("creds", "role"),
    [
        (ADMIN_CREDS, "admin"),
        (READ_WRITE_CREDS, "read-write"),
        (READ_ONLY_CREDS, "read-only"),
    ],
)
def test_mcp_proxy_forwards_session_role_key(tmp_path, monkeypatch, creds, role) -> None:
    """Each cookie session injects its OWN seeded flat role key on /webmcp so the MCP
    tier enforces per-role RBAC (it authorises by api-key role, not X-Request-User).
    The service api-key is a distinct sentinel so a read-only session can be proven
    NOT to inherit it."""
    import httpx

    ui_dist = tmp_path / "ui" / "dist"
    ui_dist.mkdir(parents=True)
    (ui_dist / "index.html").write_text("<html></html>", encoding="utf-8")
    key_dir = tmp_path / "flat_role_keys"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("CLOUD_DOG__FLAT_LOGIN__DEMO_KEYS_DIR", str(key_dir))
    monkeypatch.setenv("CLOUD_DOG__AUTH__API_KEY", "service-sentinel-key")

    seen: dict = {}

    async def fake_request(self, method, url, *, content=None, headers=None, **kwargs):
        seen["x-api-key"] = dict(headers or {}).get("x-api-key")
        return httpx.Response(200, json={"ok": True}, request=httpx.Request(method, str(url), headers=headers, content=content))

    monkeypatch.setattr(httpx.AsyncClient, "request", fake_request)
    # create_web_app builds access_control, which SEEDS the flat demo keys into
    # key_dir; the forwarded key must be that seeded role key.
    client = TestClient(create_web_app([ENV_UT]), raise_server_exceptions=False)
    seeded_key = (key_dir / f"{role}.key").read_text(encoding="utf-8").strip()
    assert seeded_key and seeded_key != "service-sentinel-key"
    assert _login(client, *creds).status_code == 200

    assert client.get("/webmcp/tools").status_code == 200
    assert seen["x-api-key"] == seeded_key
    assert seen["x-api-key"] != "service-sentinel-key", "MCP forward must be the role key, not the service key"


def test_anon_write_is_unauthorized(web_app, monkeypatch: pytest.MonkeyPatch) -> None:
    """An anonymous write selects the KEYLESS proxy (no service key injected)."""
    captured: dict = {}

    async def _spy(self, method, path, **kwargs):  # noqa: ANN001
        captured["api_key"] = self._api_key
        return ProxyResponse(status_code=401, data={"detail": "Not authenticated"})

    monkeypatch.setattr(WebApiProxy, "request", _spy, raising=True)
    client = TestClient(web_app, raise_server_exceptions=False)

    resp = client.post(WRITE_PATH, json={"name": "x"})
    assert resp.status_code == 401, resp.text
    assert captured["api_key"] == "", "anon write must NOT inject the service admin key"
