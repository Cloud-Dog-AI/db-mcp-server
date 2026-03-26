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
# Description: Real OpenSearch test runtime helper using a local Docker OpenSearch 2 container.
# Related requirements: CN-01
# Related tests: ST1.10, IT1.9

"""Real OpenSearch test runtime helper."""

from __future__ import annotations

import socket
import subprocess
import time

import requests

OPENSEARCH_TEST_CONTAINER = "db-mcp-server-test-opensearch2"
OPENSEARCH_TEST_URL = "http://127.0.0.1:9200"
OPENSEARCH_INITIAL_ADMIN_PASSWORD = "Cloud-Dog-Test-Password1!"


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


def ensure_real_opensearch() -> str:
    """Ensure a real OpenSearch 2 test container is running locally."""
    if _port_open("127.0.0.1", 9200):
        try:
            response = requests.get(f"{OPENSEARCH_TEST_URL}/_cluster/health", timeout=3)
            if response.status_code == 200:
                return OPENSEARCH_TEST_URL
        except requests.RequestException:
            pass

    subprocess.run(
        ["docker", "rm", "-f", OPENSEARCH_TEST_CONTAINER],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.run(
        [
            "docker",
            "run",
            "-d",
            "--name",
            OPENSEARCH_TEST_CONTAINER,
            "--network",
            "host",
            "-e",
            "discovery.type=single-node",
            "-e",
            "plugins.security.disabled=true",
            "-e",
            f"OPENSEARCH_INITIAL_ADMIN_PASSWORD={OPENSEARCH_INITIAL_ADMIN_PASSWORD}",
            "-e",
            "OPENSEARCH_JAVA_OPTS=-Xms512m -Xmx512m",
            "opensearchproject/opensearch:2.14.0",
        ],
        check=True,
        stdout=subprocess.DEVNULL,
    )

    deadline = time.time() + 180
    while time.time() < deadline:
        try:
            response = requests.get(f"{OPENSEARCH_TEST_URL}/_cluster/health", timeout=5)
            if response.status_code == 200:
                return OPENSEARCH_TEST_URL
        except requests.RequestException:
            time.sleep(1)
            continue
        time.sleep(1)
    raise RuntimeError("OpenSearch test container did not become ready")


def cleanup_index(name: str) -> None:
    """Drop a test index from the local OpenSearch runtime."""
    requests.delete(f"{OPENSEARCH_TEST_URL}/{name}", timeout=10)


def cleanup_template(name: str) -> None:
    """Drop a test index template from the local OpenSearch runtime."""
    requests.delete(f"{OPENSEARCH_TEST_URL}/_index_template/{name}", timeout=10)
