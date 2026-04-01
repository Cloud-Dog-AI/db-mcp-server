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
import socket
import subprocess
import time
from pathlib import Path

import pytest

from src.core.connectors.cassandra.adapter import CassandraConnector
from tests.fixtures.cassandra_seed import seed_cassandra

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CASSANDRA_COMPOSE_FILE = PROJECT_ROOT / "docker" / "docker-compose.cassandra.yml"
CASSANDRA_CONTAINER = "db-mcp-cassandra"
CASSANDRA_HOST = os.getenv("DB_MCP_TEST_CASSANDRA_HOST", "127.0.0.1")
CASSANDRA_PORT = int(os.getenv("DB_MCP_TEST_CASSANDRA_PORT", "9042"))
CASSANDRA_KEYSPACE = os.getenv("DB_MCP_TEST_CASSANDRA_KEYSPACE", "dbmcp_ecommerce")


def _port_open(host: str, port: int) -> bool:
    sock = socket.socket()
    sock.settimeout(1.0)
    try:
        sock.connect((host, port))
        return True
    except OSError:
        return False
    finally:
        sock.close()


def _compose_up() -> None:
    subprocess.run(
        ["docker", "compose", "-f", str(CASSANDRA_COMPOSE_FILE), "up", "-d", "cassandra"],
        check=True,
        cwd=PROJECT_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _container_health(container_name: str) -> str:
    result = subprocess.run(
        [
            "docker",
            "inspect",
            "--format",
            "{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}",
            container_name,
        ],
        check=False,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def _seeded_runtime_ready() -> bool:
    connector: CassandraConnector | None = None
    try:
        connector = CassandraConnector(
            host=CASSANDRA_HOST,
            port=CASSANDRA_PORT,
            timeout_seconds=15,
        )
        connector.validate_profile()
        namespaces = {item["name"] for item in connector.list_namespaces()}
        return CASSANDRA_KEYSPACE in namespaces
    except Exception:
        return False
    finally:
        if connector is not None:
            connector.close()


def ensure_real_cassandra() -> tuple[str, int, str]:
    """Ensure a real Cassandra runtime is reachable and seeded."""
    if _seeded_runtime_ready():
        return CASSANDRA_HOST, CASSANDRA_PORT, CASSANDRA_KEYSPACE

    if CASSANDRA_HOST not in {"127.0.0.1", "localhost"}:
        pytest.fail(
            f"Cassandra runtime is not ready at {CASSANDRA_HOST}:{CASSANDRA_PORT}"
        )

    _compose_up()

    deadline = time.time() + 300
    last_error: Exception | None = None
    while time.time() < deadline:
        if _container_health(CASSANDRA_CONTAINER) != "healthy":
            time.sleep(2)
            continue
        try:
            seed_cassandra(keyspace=CASSANDRA_KEYSPACE)
            return CASSANDRA_HOST, CASSANDRA_PORT, CASSANDRA_KEYSPACE
        except Exception as exc:
            last_error = exc
            time.sleep(5)

    pytest.fail(
        "Cassandra test instance did not become ready"
        if last_error is None
        else f"Cassandra test instance did not become ready: {last_error}"
    )
