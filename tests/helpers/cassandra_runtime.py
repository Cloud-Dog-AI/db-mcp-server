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
# Description: Real Cassandra test runtime helper.
# Related requirements: CN-01
# Related tests: ST1.13

"""Real Cassandra test runtime helper."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from src.core.connectors.cassandra.adapter import CassandraConnector

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CASSANDRA_HOST = os.getenv("DB_MCP_TEST_CASSANDRA_HOST", "127.0.0.1")
CASSANDRA_PORT = int(os.getenv("DB_MCP_TEST_CASSANDRA_PORT", "9042"))
CASSANDRA_KEYSPACE = os.getenv("DB_MCP_TEST_CASSANDRA_KEYSPACE", "dbmcp_ecommerce")


def _env_value(key: str, default: str = "") -> str:
    value = os.environ.get(key)
    if value:
        return value
    for env_file in (PROJECT_ROOT / "tests" / "env-all", PROJECT_ROOT / "tests" / "env-cassandra"):
        if not env_file.exists():
            continue
        for raw_line in env_file.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            found_key, found_value = line.split("=", 1)
            if found_key.strip() == key and found_value.strip():
                return found_value.strip()
    return default


def _seeded_runtime_ready() -> bool:
    host = _env_value("DB_MCP_TEST_CASSANDRA_HOST", CASSANDRA_HOST)
    port = int(_env_value("DB_MCP_TEST_CASSANDRA_PORT", str(CASSANDRA_PORT)))
    keyspace = _env_value("DB_MCP_TEST_CASSANDRA_KEYSPACE", CASSANDRA_KEYSPACE)
    connector: CassandraConnector | None = None
    try:
        connector = CassandraConnector(
            host=host,
            port=port,
            timeout_seconds=15,
        )
        connector.validate_profile()
        namespaces = {item["name"] for item in connector.list_namespaces()}
        return keyspace in namespaces
    except Exception:
        return False
    finally:
        if connector is not None:
            connector.close()


def ensure_real_cassandra() -> tuple[str, int, str]:
    """Ensure a real Cassandra runtime is reachable and seeded."""
    host = _env_value("DB_MCP_TEST_CASSANDRA_HOST", CASSANDRA_HOST)
    port = int(_env_value("DB_MCP_TEST_CASSANDRA_PORT", str(CASSANDRA_PORT)))
    keyspace = _env_value("DB_MCP_TEST_CASSANDRA_KEYSPACE", CASSANDRA_KEYSPACE)
    if _seeded_runtime_ready():
        return host, port, keyspace

    pytest.fail(
        f"Cassandra shared runtime is not ready at {host}:{port}/{keyspace}. "
        "Local Docker fallback is forbidden for this preprod validation."
    )
