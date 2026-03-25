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
# Description: Quality checks for db-mcp-server runtime skeleton assets.
# Related requirements: W28A-274-A deliverables 1, 3, 4, 5
# Related tests: QT1.1

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.quality


REQUIRED_FILES = [
    "start_api_server.py",
    "start_web_server.py",
    "start_mcp_server.py",
    "start_a2a_server.py",
    "server_control.sh",
    "Dockerfile",
    "docker-build.sh",
    "docker-compose.yml",
    "src/common/runtime.py",
    "src/servers/api/app.py",
    "src/servers/web/app.py",
    "src/servers/mcp/app.py",
    "src/servers/a2a/app.py",
]


def test_required_runtime_files_exist() -> None:
    """Ensure the runtime skeleton assets exist in the repository."""
    root = Path(__file__).resolve().parents[3]
    missing = [path for path in REQUIRED_FILES if not (root / path).exists()]
    assert not missing, f"Missing required files: {missing}"
