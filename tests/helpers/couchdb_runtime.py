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

import os
from pathlib import Path
from urllib.parse import urlparse, urlunparse

import pytest
import requests

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _env_map() -> dict[str, str]:
    values: dict[str, str] = {}
    for key, value in os.environ.items():
        if key.startswith("DB_MCP_TEST_COUCHDB_"):
            values[key] = value
    for env_file in (PROJECT_ROOT / "tests" / "env-all", PROJECT_ROOT / "tests" / "env-couchdb"):
        if not env_file.exists():
            continue
        for raw_line in env_file.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            if key.startswith("DB_MCP_TEST_COUCHDB_") and key not in values:
                values[key] = value.strip()
    return values


def _configured_url() -> str:
    values = _env_map()
    base_url = values.get("DB_MCP_TEST_COUCHDB_URL", "").rstrip("/")
    if not base_url:
        pytest.fail("DB_MCP_TEST_COUCHDB_URL is not configured in the active repo env files.")
    username = values.get("DB_MCP_TEST_COUCHDB_USERNAME", "")
    password = values.get("DB_MCP_TEST_COUCHDB_PASSWORD", "")
    parsed = urlparse(base_url)
    if username and "@" not in parsed.netloc:
        netloc = f"{username}:{password}@{parsed.hostname}"
        if parsed.port:
            netloc = f"{netloc}:{parsed.port}"
        return urlunparse((parsed.scheme, netloc, parsed.path, "", "", ""))
    return base_url


def _session() -> requests.Session:
    session = requests.Session()
    values = _env_map()
    username = values.get("DB_MCP_TEST_COUCHDB_USERNAME")
    password = values.get("DB_MCP_TEST_COUCHDB_PASSWORD")
    if username:
        session.auth = (username, password or "")
    session.headers.update({"Accept": "application/json"})
    return session


def _ensure_system_databases(session: requests.Session, base_url: str) -> None:
    """Create the mandatory CouchDB system databases used by auth/cache services."""
    for name in ("_users", "_replicator"):
        response = session.put(f"{base_url}/{name}", timeout=10)
        if response.status_code not in {201, 202, 412}:
            response.raise_for_status()


def ensure_real_couchdb() -> str:
    """Ensure the configured shared CouchDB runtime is reachable."""
    uri = _configured_url()
    parsed = urlparse(uri)
    base_url = urlunparse((parsed.scheme, f"{parsed.hostname}:{parsed.port}" if parsed.port else parsed.hostname or "", parsed.path, "", "", "")).rstrip("/")
    session = _session()
    try:
        response = session.get(f"{base_url}/_up", timeout=10)
        if response.status_code == 200:
            _ensure_system_databases(session, base_url)
            return uri
        pytest.fail(f"CouchDB shared runtime returned HTTP {response.status_code}: {response.text[:200]!r}")
    except requests.RequestException as exc:
        pytest.fail(f"CouchDB shared runtime is not reachable at {base_url!r}: {exc}")
    finally:
        session.close()


def cleanup_database(name: str) -> None:
    """Drop a test database from the configured CouchDB runtime."""
    uri = _configured_url()
    parsed = urlparse(uri)
    base_url = urlunparse((parsed.scheme, f"{parsed.hostname}:{parsed.port}" if parsed.port else parsed.hostname or "", parsed.path, "", "", "")).rstrip("/")
    session = _session()
    try:
        session.delete(f"{base_url}/{name}", timeout=10)
    finally:
        session.close()
