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
# Description: Workspace bootstrap for db-mcp-server imports.
# Related requirements: W28A-274-A deliverables 1, 2, 4
# Related tests: QT1.1, UT1.1, UT1.2, ST1.1

"""Workspace bootstrap for db-mcp-server.

This project consumes sibling platform packages from the shared workspace.
"""

from __future__ import annotations

import sys
from pathlib import Path


def _inject_workspace_package_paths() -> None:
    """Add sibling platform package roots to `sys.path` when running locally."""
    workspace_root = Path(__file__).resolve().parents[2]
    package_root = workspace_root / "cloud-dog-ai-platform-standards" / "packages" / "backend"
    for name in (
        "platform-config",
        "platform-logging",
        "platform-api-kit",
        "platform-idam",
        "platform-jobs",
        "platform-db",
    ):
        candidate = package_root / name
        candidate_str = str(candidate)
        if candidate.exists() and candidate_str not in sys.path:
            sys.path.insert(0, candidate_str)


_inject_workspace_package_paths()
