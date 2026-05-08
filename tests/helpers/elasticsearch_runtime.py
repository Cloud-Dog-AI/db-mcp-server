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
# Description: Real Elasticsearch test runtime helper using shared preprod Elasticsearch.
# Related requirements: CN-01
# Related tests: ST1.12, IT1.11
# Recent changes:
#   W28A-274-F — Initial implementation

"""Real Elasticsearch test runtime helper."""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlparse

import pytest
import requests

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ELASTICSEARCH_DEFAULT_URL = os.getenv("DB_MCP_TEST_ELASTICSEARCH_URL", "")


def _configured_url() -> str:
    if ELASTICSEARCH_DEFAULT_URL:
        return ELASTICSEARCH_DEFAULT_URL
    for env_file in (PROJECT_ROOT / "tests" / "env-elasticsearch", PROJECT_ROOT / "tests" / "env-all"):
        if not env_file.exists():
            continue
        for raw_line in env_file.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key.strip() == "DB_MCP_TEST_ELASTICSEARCH_URL" and value.strip():
                return value.strip()
    pytest.fail("DB_MCP_TEST_ELASTICSEARCH_URL is not configured in the active repo env files.")


def ensure_real_elasticsearch() -> str:
    """Ensure a real Elasticsearch 8 test instance is reachable.

    The function checks ``DB_MCP_TEST_ELASTICSEARCH_URL`` from the active
    environment or repo env files. It never starts local Docker backends.

    Returns:
        The base URL (with embedded credentials when applicable).

    Raises:
        pytest.fail: When no Elasticsearch instance can be reached.
    """
    base_url = _configured_url()
    parsed = urlparse(base_url)
    kwargs: dict = {"timeout": 10}
    if parsed.username:
        kwargs["auth"] = (parsed.username, parsed.password or "")
    check_url = f"{parsed.scheme}://{parsed.hostname}:{parsed.port}/_cluster/health"
    try:
        response = requests.get(check_url, **kwargs)
    except requests.RequestException as exc:
        pytest.fail(f"Elasticsearch shared runtime is not reachable at {base_url!r}: {exc}")
    if response.status_code not in (200, 401):
        pytest.fail(f"Elasticsearch shared runtime returned HTTP {response.status_code}: {response.text[:200]!r}")
    return base_url


def cleanup_index(name: str, base_url: str | None = None) -> None:
    """Drop a test index from the Elasticsearch instance.

    Args:
        name: Index name.
        base_url: Override base URL (defaults to the env var).
    """
    url = base_url or _configured_url()
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
    url = base_url or _configured_url()
    parsed = urlparse(url)
    kwargs: dict = {"timeout": 10}
    if parsed.username:
        kwargs["auth"] = (parsed.username, parsed.password or "")
    clean_url = f"{parsed.scheme}://{parsed.hostname}:{parsed.port}/_index_template/{name}"
    requests.delete(clean_url, **kwargs)
