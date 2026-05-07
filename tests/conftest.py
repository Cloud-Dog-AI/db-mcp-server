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
# Description: Pytest env-file bootstrap for db-mcp-server.
# Related requirements: W28A-274-A deliverable 5
# Related tests: QT1.1, UT1.1, UT1.2, ST1.1, ST1.4, ST1.5, ST1.6, IT1.3, IT1.4, IT1.5

"""Pytest support for env-driven db-mcp-server tests."""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

import httpx
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INITIAL_ENV_KEYS = set(os.environ.keys())


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register repeatable `--env` options for test runs."""
    try:
        parser.addoption(
            "--env",
            action="append",
            default=None,
            help="Env files to load before tests run.",
        )
    except ValueError:
        return


def _normalise_env_args(raw: list[str] | None) -> list[Path]:
    """Resolve repeated or comma-separated env arguments to absolute paths."""
    out: list[Path] = []
    for value in raw or []:
        for part in value.split(","):
            item = part.strip()
            if not item:
                continue
            path = Path(item)
            if not path.is_absolute():
                path = (PROJECT_ROOT / item).resolve()
            out.append(path)
    return out


def _load_env_file(path: Path) -> None:
    """Load a simple KEY=VALUE env file, allowing later env overlays to win."""
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        line = line.removeprefix("export ")
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        if key in INITIAL_ENV_KEYS:
            continue
        os.environ[key] = value


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: pytest.Config) -> None:
    """Require at least one env file and load it before test execution."""
    env_files = _normalise_env_args(config.getoption("env"))
    if not env_files:
        raise pytest.UsageError("Tests require at least one --env <path> argument")
    os.environ.setdefault("DB_MCP_SERVER_ENV_FILE", str(env_files[0]))
    for env_path in env_files:
        _load_env_file(env_path)


@pytest.fixture(scope="module", autouse=True)
def ensure_application_stack(request: pytest.FixtureRequest):
    """Start the four-surface stack for application tests via server_control.sh."""
    if request.node.get_closest_marker("application") is None:
        yield
        return

    from tests.helpers.server_runtime import resolve_env_file, service_base_url

    env_file = resolve_env_file(os.environ.get("DB_MCP_SERVER_ENV_FILE"), default_tier="AT")
    control = PROJECT_ROOT / "server_control.sh"

    subprocess.run(["bash", str(control), "--env", str(env_file), "stop", "all"], check=False, cwd=PROJECT_ROOT)
    subprocess.run(["bash", str(control), "--env", str(env_file), "start", "all"], check=True, cwd=PROJECT_ROOT)

    deadline = time.time() + 90
    health_urls = [
        f"{service_base_url('api', env_file)}/health",
        f"{service_base_url('web', env_file)}/health",
        f"{service_base_url('mcp', env_file)}/health",
        f"{service_base_url('a2a', env_file)}/health",
    ]

    try:
        for url in health_urls:
            while time.time() < deadline:
                try:
                    if httpx.get(url, timeout=5.0).status_code == 200:
                        break
                except httpx.HTTPError:
                    pass
                time.sleep(1)
            else:
                pytest.fail(f"Timed out waiting for application stack health endpoint: {url}")
        yield
    finally:
        subprocess.run(["bash", str(control), "--env", str(env_file), "stop", "all"], check=True, cwd=PROJECT_ROOT)
