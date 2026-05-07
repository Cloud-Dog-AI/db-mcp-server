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
# Description: Shared live-runtime helpers for core MCP tool tests.
# Related requirements: CD-02, CO-01, RL-01, CN-01
# Related tests: ST1.4, ST1.5, ST1.6, IT1.3, IT1.4, IT1.5

"""Live runtime helpers for core tool tests."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import Any

import httpx

from tests.fixtures.seed_data import clone_seed_collections
from tests.helpers.mongo_runtime import ensure_real_mongodb
from tests.helpers.server_runtime import resolved_api_key, service_base_url

API_BASE_URL = service_base_url("api")
MCP_BASE_URL = service_base_url("mcp")
TEST_HEADERS = {"X-API-Key": resolved_api_key()}


def _read_env_map(env_file: Path) -> dict[str, str]:
    """Read a simple KEY=VALUE env file into a dictionary."""
    values: dict[str, str] = {}
    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def start_servers(root: Path, env_file: Path, surfaces: tuple[str, ...] = ("api", "mcp")) -> None:
    """Start only the server surfaces required by the MCP/API system tests."""
    env_values = _read_env_map(env_file)
    index_path = env_values.get("CLOUD_DOG__SEARCH__DISCOVERY_INDEX_PATH")
    if index_path:
        resolved = (root / index_path).resolve() if not Path(index_path).is_absolute() else Path(index_path)
        resolved.unlink(missing_ok=True)
    subprocess.run(["bash", str(root / "server_control.sh"), "--env", str(env_file), "stop", "all"], check=False, cwd=root)
    for surface in surfaces:
        subprocess.run(
            ["bash", str(root / "server_control.sh"), "--env", str(env_file), "start", surface],
            check=True,
            cwd=root,
        )


def stop_servers(root: Path, env_file: Path) -> None:
    """Stop all four server surfaces using the approved process manager."""
    subprocess.run(["bash", str(root / "server_control.sh"), "--env", str(env_file), "stop", "all"], check=True, cwd=root)


def wait_for(url: str, *, timeout_seconds: int = 90) -> None:
    """Wait until an HTTP endpoint returns 200."""
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            response = httpx.get(url, timeout=5.0)
            if response.status_code == 200:
                return
        except httpx.HTTPError:
            pass
        time.sleep(1)
    raise AssertionError(f"Timed out waiting for {url}")


def create_profile(
    *,
    base_url: str,
    profile_name: str,
    allowed_permissions: list[str],
    field_masks: dict[str, str] | None = None,
    field_exclusions: list[str] | None = None,
    description: str = "",
    index_policy: dict[str, Any] | None = None,
    namespaces: list[str] | None = None,
    entities: list[str] | None = None,
) -> str:
    """Create a profile for live MCP tool tests."""
    response = httpx.post(
        f"{base_url}/v1/profiles",
        headers=TEST_HEADERS,
        json={
            "name": profile_name,
            "source_type": "mongodb",
            "source_connection": ensure_real_mongodb(),
            "description": description,
            "namespaces": namespaces or [],
            "entities": entities or [],
            "allowed_permissions": allowed_permissions,
            "field_masks": field_masks or {},
            "field_exclusions": field_exclusions or [],
            "index_policy": index_policy or {},
        },
        timeout=10.0,
    )
    assert response.status_code == 200, response.text
    return str(response.json()["data"]["profile_id"])


def call_tool(tool_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Invoke an MCP tool and return its data payload."""
    response = httpx.post(
        f"{MCP_BASE_URL}/mcp/tools/{tool_name}",
        headers=TEST_HEADERS,
        json=payload,
        timeout=20.0,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    return dict(body["data"])


def seed_via_mcp(profile_id: str, namespace: str) -> None:
    """Seed the deterministic dataset through the MCP content tools."""
    for entity, documents in clone_seed_collections().items():
        call_tool(
            "data.create",
            {
                "profile_id": profile_id,
                "namespace": namespace,
                "entity": entity,
                "documents": documents,
            },
        )


def unique_db_name(prefix: str) -> str:
    """Return a unique database name for a live test."""
    return f"{prefix}_{int(time.time())}"
