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
# Description: W28A-746 live preprod API/MCP/A2A/WebUI contract probes.
# Related requirements: CR-01, CR-02, AC-01, AC-03, AC-04, CFG-01
# Related tests: W28A-746 T0/T1/T2/T3 live

from __future__ import annotations

import os

import httpx
import pytest

pytestmark = [pytest.mark.integration, pytest.mark.security]


BASE_URL = os.environ.get("W28A746_LIVE_BASE_URL", "https://dbmcpserver0.cloud-dog.net").rstrip("/")
ADMIN_USERNAME = os.environ.get("E2E_WEB_USERNAME", "admin")
# W28A-SEC-R17: no credential literals in source. The preprod admin password is
# supplied via env (E2E_WEB_PASSWORD, from Vault/TF-env). read-only falls back to
# the admin password (the service's admin-fallback), so it needs no literal either.
ADMIN_PASSWORD = os.environ.get("E2E_WEB_PASSWORD", "")
READ_ONLY_USERNAME = os.environ.get("E2E_READ_ONLY_USERNAME", "read-only")
READ_ONLY_PASSWORD = os.environ.get("E2E_READ_ONLY_PASSWORD", "") or ADMIN_PASSWORD
@pytest.mark.AT
@pytest.mark.mcp
@pytest.mark.req("FR-027")


def test_live_t0_t1_negative_auth_and_flat_login() -> None:
    with httpx.Client(base_url=BASE_URL, timeout=20.0, follow_redirects=False) as client:
        assert client.get("/health").status_code == 200

        auth_me = client.get("/auth/me")
        assert auth_me.status_code == 401
        assert "permissions" not in auth_me.text
        assert "roles" not in auth_me.text

        profiles = client.get("/api/v1/profiles")
        assert profiles.status_code in {401, 403}

        login = client.post("/auth/login", json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD})
        assert login.status_code == 200, login.text[:300]
        assert login.json()["user"]["roles"] == ["admin"]
        me = client.get("/auth/me")
        assert me.status_code == 200, me.text[:300]
        assert me.json()["user"]["roles"] == ["admin"]

        admin_profiles = client.get("/webapi/v1/profiles")
        assert admin_profiles.status_code == 200, admin_profiles.text[:300]
@pytest.mark.AT
@pytest.mark.mcp
@pytest.mark.req("FR-027")


def test_live_t2_read_only_write_denied_and_surface_proxies() -> None:
    with httpx.Client(base_url=BASE_URL, timeout=20.0, follow_redirects=False) as client:
        login = client.post(
            "/auth/login",
            json={"username": READ_ONLY_USERNAME, "password": READ_ONLY_PASSWORD},
        )
        assert login.status_code == 200, login.text[:300]
        assert login.json()["user"]["roles"] == ["read-only"]

        read_profiles = client.get("/webapi/v1/profiles")
        assert read_profiles.status_code in {200, 403}, read_profiles.text[:300]
        if read_profiles.status_code == 403:
            assert "profile.manage" in read_profiles.text, read_profiles.text[:300]

        blocked = client.post(
            "/webapi/v1/profiles",
            json={
                "name": "w28a746-live-denied",
                "source_type": "mongodb",
                "source_connection": "mongodb://example.invalid:27017",
                "allowed_permissions": ["data.read"],
            },
        )
        assert blocked.status_code == 403, blocked.text[:300]
        assert blocked.json()["role"] == "read-only"

        mcp_tools = client.get("/webmcp/tools")
        assert mcp_tools.status_code == 200, mcp_tools.text[:300]
        tools_body = mcp_tools.json()
        tools = tools_body.get("tools") or tools_body.get("data") or []
        tool_names = {tool["name"] for tool in tools}
        assert {"profiles.list", "data.read", "search.metadata"} <= tool_names

        a2a_health = client.get("/weba2a/health")
        assert a2a_health.status_code == 200, a2a_health.text[:300]
