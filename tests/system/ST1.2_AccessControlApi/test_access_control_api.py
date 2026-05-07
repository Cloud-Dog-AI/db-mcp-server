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
# Description: System test for access-control API CRUD, auth, and audit logging.
# Related requirements: AC-01, AC-02, AC-03, CFG-01
# Related tests: ST1.2

from __future__ import annotations

import os
import json
import subprocess
import time
from pathlib import Path

import httpx
import pytest

from tests.helpers.server_runtime import resolved_api_key, service_base_url

pytestmark = [pytest.mark.system, pytest.mark.timeout(180)]


def _start_servers(root: Path, env_file: Path) -> None:
    subprocess.run(["bash", str(root / "server_control.sh"), "--env", str(env_file), "stop", "all"], check=False, cwd=root)
    subprocess.run(["bash", str(root / "server_control.sh"), "--env", str(env_file), "start", "api"], check=True, cwd=root)


def _stop_servers(root: Path, env_file: Path) -> None:
    subprocess.run(["bash", str(root / "server_control.sh"), "--env", str(env_file), "stop", "all"], check=True, cwd=root)


def _wait_for_api() -> None:
    deadline = time.time() + 90
    api_health_url = f"{service_base_url('api')}/health"
    while time.time() < deadline:
        try:
            response = httpx.get(api_health_url, timeout=5.0)
            if response.status_code == 200:
                return
        except httpx.HTTPError:
            pass
        time.sleep(1)
    pytest.fail("Timed out waiting for API health endpoint")


def test_access_control_api_crud_and_audit() -> None:
    """API CRUD should enforce auth, persist state, and emit audit events."""
    root = Path(__file__).resolve().parents[3]
    env_file = Path(os.environ.get("DB_MCP_SERVER_ENV_FILE", str(root / "tests" / "env-ST")))
    audit_log = root / "logs" / "audit.log.jsonl"
    audit_log.unlink(missing_ok=True)

    _start_servers(root, env_file)
    try:
        _wait_for_api()
        client = httpx.Client(base_url=service_base_url("api", env_file), timeout=10.0)

        unauth = client.get("/v1/profiles")
        assert unauth.status_code == 401

        headers = {"X-API-Key": resolved_api_key(env_file)}
        created_profile = client.post(
            "/v1/profiles",
            headers=headers,
            json={
                "name": "st-profile",
                "source_type": "mongodb",
                "source_connection": "mongo-st",
                "allowed_permissions": ["data.read", "profile.manage"],
                "field_masks": {"salary": "***MASKED***"},
                "field_exclusions": ["ssn"],
            },
        )
        assert created_profile.status_code == 200, created_profile.text
        profile_id = created_profile.json()["data"]["profile_id"]

        created_user = client.post(
            "/v1/users",
            headers=headers,
            json={
                "username": "st-analyst",
                "display_name": "ST Analyst",
                "roles": ["analyst"],
            },
        )
        assert created_user.status_code == 200, created_user.text
        user_id = created_user.json()["data"]["user_id"]

        created_group = client.post(
            "/v1/groups",
            headers=headers,
            json={
                "name": "st-auditors",
                "roles": ["auditor"],
                "member_user_ids": [user_id],
            },
        )
        assert created_group.status_code == 200, created_group.text

        created_key = client.post(
            "/v1/api-keys",
            headers=headers,
            json={
                "owner_user_id": user_id,
                "name": "st-analyst-key",
                "scopes": ["data.read"],
                "profile_ids": [profile_id],
            },
        )
        assert created_key.status_code == 200, created_key.text
        analyst_key = created_key.json()["data"]["raw_key"]

        denied = client.post(
            "/v1/users",
            headers={"X-API-Key": analyst_key},
            json={"username": "blocked-user", "roles": ["analyst"]},
        )
        assert denied.status_code == 403, denied.text

        mask_preview = client.post(
            f"/v1/profiles/{profile_id}/mask-preview",
            headers={"X-API-Key": analyst_key},
            json={"record": {"salary": 10, "ssn": "123", "name": "ok"}},
        )
        assert mask_preview.status_code == 200, mask_preview.text
        assert mask_preview.json()["data"] == {"salary": "***MASKED***", "name": "ok"}

        lines = [json.loads(line) for line in audit_log.read_text(encoding="utf-8").splitlines() if line.strip()]
        event_types = {line["event_type"] for line in lines}
        outcomes = {line["outcome"] for line in lines}
        assert "profile.create" in event_types
        assert "user.create" in event_types
        assert "group.create" in event_types
        assert "api_key.create" in event_types
        assert "denied" in outcomes
    finally:
        _stop_servers(root, env_file)
