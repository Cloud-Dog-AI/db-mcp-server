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


def _normalise_path(value: str) -> str:
    raw = str(value or "").replace("\\", "/")
    if not raw:
        return "."

    absolute = raw.startswith("/")
    parts: list[str] = []
    for part in raw.split("/"):
        if part in {"", "."}:
            continue
        if part == "..":
            if parts and parts[-1] != "..":
                parts.pop()
            elif not absolute:
                parts.append(part)
            continue
        parts.append(part)

    joined = "/".join(parts)
    if absolute:
        return f"/{joined}" if joined else "/"
    return joined or "."


def _join_path(base: str, *segments: str) -> str:
    current = _normalise_path(base)
    for segment in segments:
        piece = str(segment or "").replace("\\", "/")
        if not piece:
            continue
        if current == "/":
            current = f"/{piece.lstrip('/')}"
        elif current in {"", "."}:
            current = piece
        else:
            current = f"{current.rstrip('/')}/{piece.lstrip('/')}"
        current = _normalise_path(current)
    return current


def _parent_path(value: str) -> str:
    current = _normalise_path(value)
    if current == "/":
        return "/"
    trimmed = current.rstrip("/")
    if "/" not in trimmed:
        return "."
    parent = trimmed[: trimmed.rfind("/")]
    return parent or "/"


def _inject_workspace_package_paths() -> None:
    """Add sibling platform package roots to `sys.path` when running locally."""
    project_root = _parent_path(_parent_path(__file__))
    workspace_root = _parent_path(project_root)
    package_root = _join_path(workspace_root, "cloud-dog-ai-platform-standards", "packages", "backend")
    for name in (
        "platform-config",
        "platform-logging",
        "platform-api-kit",
        "platform-idam",
        "platform-jobs",
        "platform-db",
        "platform-storage",
    ):
        candidate_str = _join_path(package_root, name)
        if candidate_str not in sys.path:
            sys.path.insert(0, candidate_str)


_inject_workspace_package_paths()
