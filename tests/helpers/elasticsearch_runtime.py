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
# Description: Real Elasticsearch test runtime helper.
# Related requirements: CN-01
# Related tests: ST1.12, IT1.11
# Recent changes:
#   W28A-274-F — Initial implementation

"""Real Elasticsearch test runtime helper."""

from __future__ import annotations

import os
import socket
import subprocess
import time
from pathlib import Path
from urllib.parse import urlparse

import pytest
import requests

ELASTICSEARCH_TEST_CONTAINER = "db-mcp-server-test-elasticsearch8"
ELASTICSEARCH_COMPOSE_CONTAINER = "db-mcp-elasticsearch"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ELASTICSEARCH_COMPOSE_FILE = PROJECT_ROOT / "docker" / "docker-compose.elasticsearch.yml"
ELASTICSEARCH_DEFAULT_URL = os.getenv(
    "DB_MCP_TEST_ELASTICSEARCH_URL", "http://127.0.0.1:9201"
)


def _port_open(host: str, port: int) -> bool:
    """Check whether a TCP port is accepting connections.

    Args:
        host: Hostname or IP address.
        port: TCP port number.

    Returns:
        True if the port responded within 1 second.
    """
    sock = socket.socket()
    sock.settimeout(1.0)
    try:
        sock.connect((host, port))
        return True
    except OSError:
        return False
    finally:
        sock.close()


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


def ensure_real_elasticsearch() -> str:
    """Ensure a real Elasticsearch 8 test instance is reachable.

    The function first checks ``DB_MCP_TEST_ELASTICSEARCH_URL`` (which may
    point to a remote shared instance with credentials in the URL).  If
    that is not reachable it falls back to starting a local Docker
    container on port 9201.

    Returns:
        The base URL (with embedded credentials when applicable).

    Raises:
        pytest.fail: When no Elasticsearch instance can be reached.
    """
    base_url = ELASTICSEARCH_DEFAULT_URL
    parsed = urlparse(base_url)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 9201

    if _port_open(host, port):
        try:
            kwargs: dict = {"timeout": 5}
            if parsed.username:
                kwargs["auth"] = (parsed.username, parsed.password or "")
            check_url = f"{parsed.scheme}://{host}:{port}/_cluster/health"
            response = requests.get(check_url, **kwargs)
            if response.status_code in (200, 401):
                return base_url
        except requests.RequestException:
            pass

    # Fall back to the local Docker Compose runtime
    subprocess.run(
        ["docker", "rm", "-f", ELASTICSEARCH_TEST_CONTAINER],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.run(
        [
            "docker",
            "compose",
            "-f",
            str(ELASTICSEARCH_COMPOSE_FILE),
            "up",
            "-d",
            "elasticsearch",
        ],
        check=True,
        cwd=PROJECT_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    local_url = "http://127.0.0.1:9201"
    deadline = time.time() + 300
    while time.time() < deadline:
        if _container_health(ELASTICSEARCH_COMPOSE_CONTAINER) != "healthy":
            time.sleep(2)
            continue
        try:
            response = requests.get(f"{local_url}/_cluster/health", timeout=5)
            if response.status_code == 200:
                return local_url
        except requests.RequestException:
            time.sleep(2)
            continue
        time.sleep(2)
    pytest.fail("Elasticsearch test instance did not become ready")


def cleanup_index(name: str, base_url: str | None = None) -> None:
    """Drop a test index from the Elasticsearch instance.

    Args:
        name: Index name.
        base_url: Override base URL (defaults to the env var).
    """
    url = base_url or ELASTICSEARCH_DEFAULT_URL
    parsed = urlparse(url)
    kwargs: dict = {"timeout": 10}
    if parsed.username:
        kwargs["auth"] = (parsed.username, parsed.password or "")
    clean_url = f"{parsed.scheme}://{parsed.hostname}:{parsed.port}/{name}"
    requests.delete(clean_url, **kwargs)


def cleanup_template(name: str, base_url: str | None = None) -> None:
    """Drop a test index template from the Elasticsearch instance.

    Args:
        name: Template name.
        base_url: Override base URL (defaults to the env var).
    """
    url = base_url or ELASTICSEARCH_DEFAULT_URL
    parsed = urlparse(url)
    kwargs: dict = {"timeout": 10}
    if parsed.username:
        kwargs["auth"] = (parsed.username, parsed.password or "")
    clean_url = f"{parsed.scheme}://{parsed.hostname}:{parsed.port}/_index_template/{name}"
    requests.delete(clean_url, **kwargs)
