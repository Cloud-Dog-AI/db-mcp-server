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
# Description: Real OpenSearch test runtime helper. Connects to the shared
#              deployed OpenSearch instance configured via the
#              ``DB_MCP_TEST_OPENSEARCH_URL`` environment variable. Per
#              RULES.md §3.2.3 / §5.6, tests MUST use shared infrastructure
#              and MUST NOT spin up local Docker containers.
# Related requirements: CN-01
# Related tests: ST1.10, IT1.9
# Recent changes:
#   W28A-#A125 — Removed local Docker spin-up (RULES §3.2.3 / §5.6 violation).
#                Now requires the env var ``DB_MCP_TEST_OPENSEARCH_URL`` and
#                fails loudly via ``pytest.fail`` if the deployed instance
#                is unreachable. No ``pytest.skip``.

"""Real OpenSearch test runtime helper.

This module connects test code to the shared, Terraform-managed OpenSearch
instance whose URL is provided via the ``DB_MCP_TEST_OPENSEARCH_URL``
environment variable (typically loaded from ``tests/env-all`` or
``tests/env-opensearch`` which carry the canonical
``http://opensearch0.app.vpc0.cloud-dog.net:1201`` value).

It deliberately does NOT spin up a local Docker container, in compliance
with RULES.md §3.2.3 (Infrastructure Reuse — do not spin up new backends)
and §5.6 (Use shared test services — never spin up local duplicates). If
the deployed instance is unreachable the helper fails loudly via
``pytest.fail`` per §5.3 / §5.6 — never ``pytest.skip``.
"""

from __future__ import annotations

import os
from urllib.parse import urlparse

import pytest
import requests


def _opensearch_url() -> str:
    """Return the canonical OpenSearch URL from the environment.

    Returns:
        The shared OpenSearch URL.

    Raises:
        pytest.fail: If ``DB_MCP_TEST_OPENSEARCH_URL`` is not set. Per
            RULES §2.4 (zero hardcoded values) tests MUST source the
            URL from the env-file rather than assume a default.
    """
    url = os.environ.get("DB_MCP_TEST_OPENSEARCH_URL")
    if not url:
        pytest.fail(
            "DB_MCP_TEST_OPENSEARCH_URL is not set. Source tests/env-all or "
            "tests/env-opensearch (canonical value: "
            "http://opensearch0.app.vpc0.cloud-dog.net:1201) before "
            "running OpenSearch ST/IT tests. Local Docker spin-up is "
            "forbidden by RULES.md §3.2.3 / §5.6."
        )
    return url


def _request_kwargs(url: str) -> dict:
    """Build ``requests`` keyword arguments, including basic auth when present.

    Args:
        url: Full base URL, possibly carrying ``user:password@`` userinfo.

    Returns:
        Mapping suitable to splat into ``requests.<verb>(**kwargs)``.
    """
    kwargs: dict = {"timeout": 10}
    parsed = urlparse(url)
    if parsed.username:
        kwargs["auth"] = (parsed.username, parsed.password or "")
    return kwargs


def ensure_real_opensearch() -> str:
    """Ensure the deployed OpenSearch instance is reachable.

    Returns:
        The base URL provided by ``DB_MCP_TEST_OPENSEARCH_URL``.

    Raises:
        pytest.fail: If the cluster health endpoint does not respond
            with HTTP 200 within the connect/read timeout. Per RULES §5.6
            we fail loudly rather than skip.
    """
    base_url = _opensearch_url()
    health_url = f"{base_url.rstrip('/')}/_cluster/health"
    kwargs = _request_kwargs(base_url)
    try:
        response = requests.get(health_url, **kwargs)
    except requests.RequestException as exc:
        pytest.fail(
            f"OpenSearch shared instance unreachable at {base_url!r}: {exc}. "
            "Verify the dbmcpserver0 outboundPorts firewall and Vault "
            "dev.databases.providers.opensearch.port. "
            "Local Docker fallback is forbidden (RULES §3.2.3 / §5.6)."
        )
    if response.status_code != 200:
        pytest.fail(
            f"OpenSearch shared instance returned HTTP {response.status_code} "
            f"from {health_url!r}. Body: {response.text[:200]!r}"
        )
    return base_url


def cleanup_index(name: str) -> None:
    """Drop a test index from the shared OpenSearch instance.

    Args:
        name: Index name (e.g. ``dbmcp_it_widgets_<ts>``).
    """
    base_url = _opensearch_url()
    requests.delete(
        f"{base_url.rstrip('/')}/{name}",
        **_request_kwargs(base_url),
    )


def cleanup_template(name: str) -> None:
    """Drop a test index template from the shared OpenSearch instance.

    Args:
        name: Index template name.
    """
    base_url = _opensearch_url()
    requests.delete(
        f"{base_url.rstrip('/')}/_index_template/{name}",
        **_request_kwargs(base_url),
    )
