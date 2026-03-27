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
# Description: System test covering startup and health probes for all four server surfaces.
# Related requirements: W28A-274-A deliverables 1, 3, 5
# Tests: CR-01, CR-02, CR-03
# Related tests: ST1.1

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

import httpx
import pytest

pytestmark = [pytest.mark.system, pytest.mark.timeout(120)]


def test_all_servers_start_and_report_health() -> None:
    """Start all four servers and verify each health endpoint returns 200."""
    root = Path(__file__).resolve().parents[3]
    env_file = Path(os.environ.get("DB_MCP_SERVER_ENV_FILE", str(root / "tests" / "env-ST")))
    control = root / "server_control.sh"

    subprocess.run(["bash", str(control), "--env", str(env_file), "stop", "all"], check=False, cwd=root)
    subprocess.run(["bash", str(control), "--env", str(env_file), "start", "all"], check=True, cwd=root)
    try:
        deadline = time.time() + 90
        urls = [
            "http://127.0.0.1:8086/health",
            "http://127.0.0.1:8087/health",
            "http://127.0.0.1:8088/health",
            "http://127.0.0.1:8089/health",
        ]
        for url in urls:
            while True:
                try:
                    response = httpx.get(url, timeout=5.0)
                    if response.status_code == 200:
                        break
                except httpx.HTTPError:
                    pass
                if time.time() > deadline:
                    pytest.fail(f"Timed out waiting for health endpoint: {url}")
                time.sleep(1)
    finally:
        subprocess.run(["bash", str(control), "--env", str(env_file), "stop", "all"], check=True, cwd=root)
