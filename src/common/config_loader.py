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
# Description: Platform-config bootstrap for db-mcp-server.
# Related requirements: W28A-274-A deliverables 1, 2
# Covers: CFG-02, CFG-03
# Related tests: UT1.1, ST1.1

"""Configuration bootstrap for db-mcp-server."""

from __future__ import annotations

from cloud_dog_config import get_config, load_config
from cloud_dog_config.config import GlobalConfig

from src.common.env_loader import repo_root, resolve_env_files


def load_runtime_config(explicit_env_files: list[str] | None = None) -> GlobalConfig:
    """Load the service configuration using the platform precedence chain."""
    root = repo_root()
    env_files = resolve_env_files(explicit_env_files)
    return load_config(
        env_files=env_files,
        config_yaml=str(root / "config.yaml"),
        defaults_yaml=str(root / "defaults.yaml"),
        unresolved_policy="strict",
    )


def get_runtime_value(path: str):
    """Return a single value from the active configuration snapshot."""
    return get_config(path)
