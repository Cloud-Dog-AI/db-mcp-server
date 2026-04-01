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
# Description: Shared test helpers for config-derived local server addresses.
# Related requirements: W28A-473 C7, C9, C10 remediation
# Related tests: ST1.1, ST1.2, ST1.8, IT1.1, IT1.2, IT1.8, IT1.9, AT_WEBUI_E2E

"""Config-driven server runtime helpers for db-mcp-server tests."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from src.common.config_loader import load_runtime_config

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def resolve_env_file(explicit_env_file: str | Path | None = None, *, default_tier: str = "ST") -> Path:
    """Resolve the env file path used to derive local test server settings."""
    candidate = explicit_env_file or os.environ.get("DB_MCP_SERVER_ENV_FILE")
    if candidate is None:
        candidate = PROJECT_ROOT / "tests" / f"env-{default_tier}"
    path = Path(candidate)
    if not path.is_absolute():
        path = (PROJECT_ROOT / path).resolve()
    return path


def load_test_runtime_config(explicit_env_file: str | Path | None = None, *, default_tier: str = "ST") -> Any:
    """Load service config for the given test env file via cloud_dog_config."""
    env_file = resolve_env_file(explicit_env_file, default_tier=default_tier)
    return load_runtime_config([str(env_file)])


def _loopback_host(host: str | None) -> str:
    resolved = str(host or "").strip()
    if resolved in {"", "0.0.0.0", "::"}:
        return "127.0.0.1"
    return resolved


def service_host(surface: str, explicit_env_file: str | Path | None = None, *, default_tier: str = "ST") -> str:
    """Return the loopback-safe host for a server surface."""
    config = load_test_runtime_config(explicit_env_file, default_tier=default_tier)
    return _loopback_host(config.get(f"{surface}_server.host"))


def service_port(surface: str, explicit_env_file: str | Path | None = None, *, default_tier: str = "ST") -> int:
    """Return the configured port for a server surface."""
    config = load_test_runtime_config(explicit_env_file, default_tier=default_tier)
    return int(config.get(f"{surface}_server.port"))


def service_base_url(surface: str, explicit_env_file: str | Path | None = None, *, default_tier: str = "ST") -> str:
    """Return the base URL for a configured server surface."""
    return (
        f"http://{service_host(surface, explicit_env_file, default_tier=default_tier)}:"
        f"{service_port(surface, explicit_env_file, default_tier=default_tier)}"
    )


def resolved_api_key(explicit_env_file: str | Path | None = None, *, default_tier: str = "ST") -> str:
    """Return the resolved API key for the active test env file."""
    config = load_test_runtime_config(explicit_env_file, default_tier=default_tier)
    return str(config.get("auth.api_key"))
