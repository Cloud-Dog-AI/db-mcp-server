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
# Description: Real MongoDB test runtime helper using a local Docker Mongo 6 container.
# Related requirements: CN-01
# Related tests: ST1.3, IT1.2

"""Real MongoDB test runtime helper."""

from __future__ import annotations

import socket
import subprocess
import time

from pymongo import MongoClient

MONGO_TEST_CONTAINER = "db-mcp-server-test-mongo6"
MONGO_TEST_URI = "mongodb://127.0.0.1:27018"


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


def ensure_real_mongodb() -> str:
    """Ensure a real MongoDB 6 test container is running locally."""
    if _port_open("127.0.0.1", 27018):
        client = MongoClient(MONGO_TEST_URI, serverSelectionTimeoutMS=3000)
        try:
            client.admin.command("ping")
            return MONGO_TEST_URI
        finally:
            client.close()

    subprocess.run(
        ["docker", "rm", "-f", MONGO_TEST_CONTAINER],
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
            MONGO_TEST_CONTAINER,
            "--network",
            "host",
            "mongo:6.0",
            "--bind_ip",
            "127.0.0.1",
            "--port",
            "27018",
        ],
        check=True,
        stdout=subprocess.DEVNULL,
    )

    deadline = time.time() + 45
    while time.time() < deadline:
        try:
            client = MongoClient(MONGO_TEST_URI, serverSelectionTimeoutMS=2000)
            client.admin.command("ping")
            client.close()
            return MONGO_TEST_URI
        except Exception:
            time.sleep(1)
    raise RuntimeError("MongoDB test container did not become ready")


def cleanup_database(name: str) -> None:
    """Drop a test database from the local MongoDB runtime."""
    client = MongoClient(MONGO_TEST_URI, serverSelectionTimeoutMS=3000)
    try:
        client.drop_database(name)
    finally:
        client.close()
