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
# Description: Real MongoDB test runtime helper using shared preprod MongoDB.
# Related requirements: CN-01
# Related tests: ST1.3, IT1.2

"""Real MongoDB test runtime helper."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from pymongo import MongoClient

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _env_value(*keys: str) -> str:
    for key in keys:
        value = os.environ.get(key)
        if value:
            return value
    for env_file in (PROJECT_ROOT / "tests" / "env-mongodb", PROJECT_ROOT / "tests" / "env-all"):
        if not env_file.exists():
            continue
        for raw_line in env_file.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key.strip() in keys and value.strip():
                return value.strip()
    return ""


def ensure_real_mongodb() -> str:
    """Ensure the configured shared MongoDB runtime is reachable."""
    uri = _env_value("DB_MCP_TEST_MONGODB_URI", "CLOUD_DOG__CONNECTORS__MONGODB__DEFAULT_URI")
    if not uri:
        pytest.fail(
            "MongoDB test URI is not configured. Provide DB_MCP_TEST_MONGODB_URI "
            "or CLOUD_DOG__CONNECTORS__MONGODB__DEFAULT_URI via a repo env file."
        )

    client = MongoClient(uri, serverSelectionTimeoutMS=3000)
    try:
        client.admin.command("ping")
        return uri
    except Exception as exc:
        pytest.fail(f"MongoDB shared runtime is not reachable: {exc}")
    finally:
        client.close()


def cleanup_database(name: str) -> None:
    """Drop a test database from the configured MongoDB runtime."""
    uri = _env_value("DB_MCP_TEST_MONGODB_URI", "CLOUD_DOG__CONNECTORS__MONGODB__DEFAULT_URI")
    if not uri:
        return
    client = MongoClient(uri, serverSelectionTimeoutMS=3000)
    try:
        client.drop_database(name)
    finally:
        client.close()
