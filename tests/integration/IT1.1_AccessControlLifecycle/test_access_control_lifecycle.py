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
# Description: Integration test for profile/user/group/key lifecycle and MCP parity.
# Related requirements: AC-01, AC-02, AC-03, CFG-01
# Related tests: IT1.1

from __future__ import annotations

import subprocess
import time
from pathlib import Path

import httpx
import pytest

from tests.helpers.server_runtime import active_env_file, resolved_api_key, service_base_url

pytestmark = [pytest.mark.integration, pytest.mark.timeout(240)]


def _start_servers(root: Path, env_file: Path) -> None:
    subprocess.run(["bash", str(root / "server_control.sh"), "--env", str(env_file), "stop", "all"], check=False, cwd=root)
    subprocess.run(["bash", str(root / "server_control.sh"), "--env", str(env_file), "start", "all"], check=True, cwd=root)


def _stop_servers(root: Path, env_file: Path) -> None:
    subprocess.run(["bash", str(root / "server_control.sh"), "--env", str(env_file), "stop", "all"], check=True, cwd=root)


def _wait(url: str) -> None:
    deadline = time.time() + 60
    while time.time() < deadline:
        try:
            response = httpx.get(url, timeout=5.0)
            if response.status_code == 200:
                return
        except httpx.HTTPError:
            pass
        time.sleep(1)
    pytest.fail(f"Timed out waiting for {url}")
@pytest.mark.IT
@pytest.mark.mcp
@pytest.mark.probe  # rtt-2026-06-12 INST3: KEEP-AS-PROBE pending operator REQ-binding


def test_profile_user_group_api_key_lifecycle_and_mcp_admin_parity() -> None:
    """Admin API and MCP surfaces should manage access state and enforce least privilege."""
    root = Path(__file__).resolve().parents[3]
    env_file = active_env_file(default_tier="IT")

    _start_servers(root, env_file)
    try:
        api_base_url = service_base_url("api", env_file, default_tier="IT")
        mcp_base_url = service_base_url("mcp", env_file, default_tier="IT")
        _wait(f"{api_base_url}/health")
        _wait(f"{mcp_base_url}/health")
        api = httpx.Client(base_url=api_base_url, timeout=10.0)
        mcp = httpx.Client(base_url=mcp_base_url, timeout=10.0)
        admin_headers = {"X-API-Key": resolved_api_key(env_file, default_tier="IT")}

        profile_response = api.post(
            "/v1/profiles",
            headers=admin_headers,
            json={
                "name": "it-profile",
                "source_type": "elasticsearch",
                "source_connection": "es-it",
                "allowed_permissions": ["catalog.read", "data.read", "profile.manage"],
                "enabled_tools": ["profiles.list", "profiles.get"],
            },
        )
        assert profile_response.status_code == 200, profile_response.text
        profile_id = profile_response.json()["data"]["profile_id"]

        user_response = api.post(
            "/v1/users",
            headers=admin_headers,
            json={
                "username": "it-auditor",
                "display_name": "IT Auditor",
                "roles": ["auditor"],
            },
        )
        assert user_response.status_code == 200, user_response.text
        user_id = user_response.json()["data"]["user_id"]

        group_response = api.post(
            "/v1/groups",
            headers=admin_headers,
            json={
                "name": "it-analysts",
                "roles": ["analyst"],
                "member_user_ids": [user_id],
            },
        )
        assert group_response.status_code == 200, group_response.text

        key_response = api.post(
            "/v1/api-keys",
            headers=admin_headers,
            json={
                "owner_user_id": user_id,
                "name": "it-auditor-key",
                "scopes": ["data.read"],
                "profile_ids": [profile_id],
            },
        )
        assert key_response.status_code == 200, key_response.text
        limited_key = key_response.json()["data"]["raw_key"]

        allow_response = api.get(
            f"/v1/profiles/{profile_id}/authorise/data.read",
            headers={"X-API-Key": limited_key},
        )
        assert allow_response.status_code == 200, allow_response.text
        allow_payload = allow_response.json()["data"]
        assert allow_payload["authorised"] is True
        assert allow_payload["principal"]["user_id"] == user_id

        deny_response = api.get(
            f"/v1/profiles/{profile_id}/authorise/profile.manage",
            headers={"X-API-Key": limited_key},
        )
        assert deny_response.status_code == 403, deny_response.text

        tool_list = mcp.get("/mcp/tools", headers=admin_headers)
        assert tool_list.status_code == 200, tool_list.text
        tool_names = {item["name"] for item in tool_list.json()["data"]}
        assert "profiles.list" in tool_names
        assert "api_keys.create" in tool_names

        admin_tool_call = mcp.post(
            "/mcp/tools/profiles.list",
            headers=admin_headers,
            json={},
        )
        assert admin_tool_call.status_code == 200, admin_tool_call.text
        assert any(item["profile_id"] == profile_id for item in admin_tool_call.json()["data"]["items"])

        denied_tool_call = mcp.post(
            "/mcp/tools/profiles.list",
            headers={"X-API-Key": limited_key},
            json={},
        )
        assert denied_tool_call.status_code == 403, denied_tool_call.text
    finally:
        _stop_servers(root, env_file)
