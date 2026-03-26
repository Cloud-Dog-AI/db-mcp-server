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
# Description: Real CouchDB test runtime helper using a local Docker CouchDB 3 container.
# Related requirements: CN-01
# Related tests: ST1.9, IT1.8

"""Real CouchDB test runtime helper."""

from __future__ import annotations

import socket
import subprocess
import time

import requests

COUCHDB_TEST_CONTAINER = "db-mcp-server-test-couchdb3"
COUCHDB_TEST_URL = "http://127.0.0.1:5984"
COUCHDB_USERNAME = "admin"
COUCHDB_PASSWORD = "cloud-dog-test"


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


def _session() -> requests.Session:
    session = requests.Session()
    session.auth = (COUCHDB_USERNAME, COUCHDB_PASSWORD)
    session.headers.update({"Accept": "application/json"})
    return session


def _ensure_system_databases(session: requests.Session) -> None:
    """Create the mandatory CouchDB system databases used by auth/cache services."""
    for name in ("_users", "_replicator"):
        response = session.put(f"{COUCHDB_TEST_URL}/{name}", timeout=10)
        if response.status_code not in {201, 202, 412}:
            response.raise_for_status()


def ensure_real_couchdb() -> str:
    """Ensure a real CouchDB 3 test container is running locally."""
    if _port_open("127.0.0.1", 5984):
        session = _session()
        try:
            response = session.get(f"{COUCHDB_TEST_URL}/_up", timeout=3)
            if response.status_code == 200:
                _ensure_system_databases(session)
                return f"http://{COUCHDB_USERNAME}:{COUCHDB_PASSWORD}@127.0.0.1:5984"
        except requests.RequestException:
            pass
        finally:
            session.close()

    subprocess.run(
        ["docker", "rm", "-f", COUCHDB_TEST_CONTAINER],
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
            COUCHDB_TEST_CONTAINER,
            "--network",
            "host",
            "-e",
            f"COUCHDB_USER={COUCHDB_USERNAME}",
            "-e",
            f"COUCHDB_PASSWORD={COUCHDB_PASSWORD}",
            "couchdb:3",
        ],
        check=True,
        stdout=subprocess.DEVNULL,
    )

    deadline = time.time() + 120
    session = _session()
    try:
        while time.time() < deadline:
            try:
                response = session.get(f"{COUCHDB_TEST_URL}/_up", timeout=3)
                if response.status_code == 200:
                    _ensure_system_databases(session)
                    return f"http://{COUCHDB_USERNAME}:{COUCHDB_PASSWORD}@127.0.0.1:5984"
            except Exception:
                time.sleep(1)
                continue
            time.sleep(1)
    finally:
        session.close()
    raise RuntimeError("CouchDB test container did not become ready")


def cleanup_database(name: str) -> None:
    """Drop a test database from the local CouchDB runtime."""
    session = _session()
    try:
        session.delete(f"{COUCHDB_TEST_URL}/{name}", timeout=10)
    finally:
        session.close()
