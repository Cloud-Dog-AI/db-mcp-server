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
# Description: System test covering PS-30 SPA serving and same-origin API proxy.
# Related requirements: W28A-274-J deliverables 2, 4, 5
# Related tests: ST1.8, UT1.11

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

import httpx
import pytest

from tests.helpers.server_runtime import resolved_api_key, service_base_url

pytestmark = [pytest.mark.system, pytest.mark.timeout(180)]


def test_web_server_serves_spa_runtime_config_and_api_proxy() -> None:
    root = Path(__file__).resolve().parents[3]
    env_file = Path(os.environ.get("DB_MCP_SERVER_ENV_FILE", str(root / "tests" / "env-ST-WEBUI")))
    control = root / "server_control.sh"

    subprocess.run(["bash", str(control), "--env", str(env_file), "start", "all"], check=True, cwd=root)
    try:
        web_base_url = service_base_url("web", env_file)
        deadline = time.time() + 60
        while time.time() < deadline:
            try:
                if httpx.get(f"{web_base_url}/health", timeout=5.0).status_code == 200:
                    break
            except httpx.HTTPError:
                pass
            time.sleep(1)
        else:
            pytest.fail("Timed out waiting for web server health")

        runtime = httpx.get(f"{web_base_url}/runtime-config.js", timeout=10.0)
        assert runtime.status_code == 200
        assert 'window.__RUNTIME_CONFIG__' in runtime.text

        root_page = httpx.get(f"{web_base_url}/", timeout=10.0)
        assert root_page.status_code == 200

        search_page = httpx.get(f"{web_base_url}/search", timeout=10.0)
        assert search_page.status_code == 200

        proxied_ping = httpx.get(
            f"{web_base_url}/api/v1/ping",
            headers={"X-API-Key": resolved_api_key(env_file)},
            timeout=10.0,
        )
        assert proxied_ping.status_code == 200, proxied_ping.text
        assert proxied_ping.json()["data"]["service"] == "db-mcp-server"
    finally:
        subprocess.run(["bash", str(control), "--env", str(env_file), "stop", "all"], check=True, cwd=root)
