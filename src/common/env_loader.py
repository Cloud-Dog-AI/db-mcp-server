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
# Description: Helpers for resolving env-file input for db-mcp-server runtime
# and tests.
# Related requirements: W28A-274-A deliverables 1, 3, 5
# Related tests: UT1.1, ST1.1

"""Environment-file helpers for db-mcp-server."""

from __future__ import annotations

from pathlib import Path

from cloud_dog_config import resolve_runtime_env_files


def repo_root() -> Path:
    """Return the repository root for this service."""
    return Path(__file__).resolve().parents[2]


def resolve_env_files(explicit_env_files: list[str] | None = None) -> list[str]:
    """Resolve env files from explicit input or process environment.

    The server control script exports `CLOUD_DOG_ENV_FILES`. Tests may pass an
    explicit list instead.
    """
    if explicit_env_files:
        return [str(Path(path)) for path in explicit_env_files]
    return resolve_runtime_env_files()
