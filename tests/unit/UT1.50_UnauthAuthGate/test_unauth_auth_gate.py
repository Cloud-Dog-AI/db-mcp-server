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

"""
UT1.50 — Unauthenticated auth-gate (negative-auth) regression guard.

W28A-889-B estate unauth auth-gate hardening. The missing NEGATIVE-auth test for
the unauthenticated front door (the index-retriever WebApiProxy admin-key
injection class, W28A-734-R2).

db-mcp's web tier proxies /webapi to the API server and chooses the proxy by
session: ``api_session_proxy if _get_session(request) else api_proxy``
(app.py proxy_web_api). ``api_session_proxy`` injects the service api-key;
``api_proxy`` is KEYLESS. The correct unauthenticated behaviour is to select the
KEYLESS proxy so the API server's own key check denies the anonymous caller
(401), and the service admin key is NEVER injected for an anonymous request.

This test proves, with a service key explicitly configured, that an anonymous
request still selects the keyless proxy (no key injected) and that the local
/auth/me web session gate returns 401. The authenticated-session path (which
DOES inject the service key — tracked separately as W28A-890) is out of scope
for this unauth front-door lane.

Related Tasks: W28A-889-B

Recent Changes:
- 2026-06-09: W28A-889-B — initial negative-auth regression guard.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from cloud_dog_api_kit.web.proxy import ProxyResponse, WebApiProxy

pytestmark = [pytest.mark.unit, pytest.mark.security, pytest.mark.fast]

SENTINEL_SERVICE_KEY = "svc-key-889b-unit-only"
PRINCIPAL_PATH = "/auth/me"
PROTECTED_DATA_PATH = "/webapi/v1/profiles"
_COOKIE_NAME = "db_web_session"


@pytest.fixture()
def web_app(monkeypatch, tmp_path):
    """Build the db-mcp web app with a NON-EMPTY service api-key configured.

    A non-empty ``auth.api_key`` makes the keyless-for-anon assertion meaningful:
    the session proxy would carry this key, so proving the anon request uses an
    EMPTY key proves the keyless proxy was selected (no injection).
    """
    monkeypatch.setenv("CLOUD_DOG__AUTH__API_KEY", SENTINEL_SERVICE_KEY)
    monkeypatch.setenv("CLOUD_DOG__FLAT_LOGIN__DEMO_KEYS_DIR", str(tmp_path / "flat_role_keys"))
    from src.servers.web.app import create_web_app

    app = create_web_app(["tests/env-UT"])
    # Non-vacuity guard: prove the sentinel actually plumbed into config.
    assert str(app.state.runtime.config.get("auth.api_key", "")) == SENTINEL_SERVICE_KEY
    app.state.flat_key_dir = tmp_path / "flat_role_keys"
    return app
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.probe  # rtt-2026-06-12 INST3: KEEP-AS-PROBE pending operator REQ-binding


def test_unauth_principal_denied(web_app) -> None:
    client = TestClient(web_app, raise_server_exceptions=False)
    resp = client.get(PRINCIPAL_PATH)
    assert resp.status_code == 401, f"anon {PRINCIPAL_PATH} must be 401: {resp.status_code} {resp.text[:200]}"
    assert '"roles"' not in resp.text and '"permissions"' not in resp.text, resp.text
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.probe  # rtt-2026-06-12 INST3: KEEP-AS-PROBE pending operator REQ-binding


def test_anon_proxy_request_is_keyless(web_app, monkeypatch) -> None:
    """An anonymous /webapi request must select the KEYLESS proxy (no key injected)."""
    captured: dict = {}

    async def _spy(self, method, path, **kwargs):  # noqa: ANN001
        captured["api_key"] = self._api_key
        captured["api_key_header_present"] = bool(
            kwargs.get("headers", {}).get("X-API-Key") or kwargs.get("headers", {}).get("x-api-key")
        )
        return ProxyResponse(status_code=200, data={"ok": True, "spy": "intercepted"})

    monkeypatch.setattr(WebApiProxy, "request", _spy, raising=True)

    client = TestClient(web_app, raise_server_exceptions=False)
    resp = client.get(PROTECTED_DATA_PATH)
    # The spy short-circuits the network call; we only care which proxy was used.
    assert resp.status_code == 200, resp.text
    assert captured, "proxy.request was not invoked"
    assert captured["api_key"] == "", (
        "anonymous request selected a KEY-INJECTING proxy "
        f"(api_key={captured['api_key']!r}); the service admin key must NOT be "
        "injected for an unauthenticated caller"
    )
    assert captured["api_key"] != SENTINEL_SERVICE_KEY
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.probe  # rtt-2026-06-12 INST3: KEEP-AS-PROBE pending operator REQ-binding


def test_forged_session_cookie_does_not_bypass(web_app) -> None:
    client = TestClient(web_app, raise_server_exceptions=False)
    client.cookies.set(_COOKIE_NAME, "forged-not-a-real-session-token")
    resp = client.get(PRINCIPAL_PATH)
    assert resp.status_code == 401, f"forged cookie must not authenticate: {resp.status_code} {resp.text[:200]}"
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.probe  # rtt-2026-06-12 INST3: KEEP-AS-PROBE pending operator REQ-binding


def test_auth_me_resolves_managed_api_key(web_app) -> None:
    read_only_key = (web_app.state.flat_key_dir / "read-only.key").read_text(encoding="utf-8").strip()
    client = TestClient(web_app, raise_server_exceptions=False)

    resp = client.get(PRINCIPAL_PATH, headers={"X-API-Key": read_only_key})

    assert resp.status_code == 200, resp.text
    user = resp.json()["user"]
    assert user["username"] == "flat-read-only"
    assert user["roles"] == ["read-only"]
    assert "data.read" in user["permissions"]
    assert "data.create" not in user["permissions"]
