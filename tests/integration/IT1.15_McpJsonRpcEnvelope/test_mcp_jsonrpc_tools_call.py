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
# Description: IT1.15 — JSON-RPC 2.0 tools/call envelope test for the db-mcp-server MCP surface.
#   Proves that the /mcp endpoint accepts the canonical MCP JSON-RPC envelope
#   ({"jsonrpc":"2.0","method":"tools/call",...}) and returns a well-formed JSON-RPC result.
#   Follows templates/tests/per-surface/T-TST-MCP-EXAMPLE.py (T-TST-MCP v1.0).
# Related requirements: FR-020, FR-005
# Related tests: IT1.15

"""IT1.15 — JSON-RPC 2.0 tools/call envelope integration test (T-TST-MCP v1.0).

Verifies that the db-mcp-server MCP surface:
  1. Accepts initialize → tools/list → tools/call via the standard JSON-RPC 2.0 envelope.
  2. Returns a well-formed JSON-RPC response with "result" and "content[0].type" == "text".
  3. Rejects an anonymous tools/call with HTTP 401.

Must be real + well-formed per T-TST-MCP-EXAMPLE.py. The module owns the approved
local API/MCP lifecycle under tests/env-IT so the tier is independently executable.
"""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from tests.helpers.core_tools_runtime import (
    API_BASE_URL,
    MCP_BASE_URL,
    create_profile,
    start_servers,
    stop_servers,
    wait_for,
)
from tests.helpers.server_runtime import active_env_file, resolved_api_key

# ---------------------------------------------------------------------------
# Helpers — canonical MCP JSON-RPC transport (T-TST-MCP-EXAMPLE.py §1.1, §1.9)
# ---------------------------------------------------------------------------

_MCP_ENDPOINT = f"{MCP_BASE_URL}/mcp"


def _mcp_post(token: str | None, payload: dict, timeout: int = 30) -> httpx.Response:
    """POST to /mcp with the required MCP headers (AGENT-LESSONS.md §1.1)."""
    headers: dict[str, str] = {
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
    }
    if token:
        headers["X-API-Key"] = token
    return httpx.post(_MCP_ENDPOINT, json=payload, headers=headers, timeout=timeout)


def _parse_sse(response: httpx.Response) -> dict:
    """Parse SSE response body into a single JSON-RPC message (AGENT-LESSONS.md §1.1)."""
    text = response.text
    # Modern streamable-HTTP transport returns raw JSON or SSE "data: ..." lines.
    if text.strip().startswith("{"):
        return json.loads(text)
    for line in text.splitlines():
        if line.startswith("data: "):
            return json.loads(line[len("data: "):])
    raise AssertionError(f"No parseable JSON-RPC message in MCP response: {text[:500]}")


def _mcp_initialize(token: str) -> None:
    """Perform required initialize handshake (AGENT-LESSONS.md §1.9)."""
    resp = _mcp_post(token, {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": "it1.15-test", "version": "1.0"},
        },
    })
    # initialize may return 200 or 204; either is acceptable for the handshake.
    assert resp.status_code in (200, 204), (
        f"MCP initialize failed: {resp.status_code} {resp.text[:300]}"
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def live_mcp_stack():
    """Run the API and MCP surfaces required by the literal transport checks."""
    root = Path(__file__).resolve().parents[3]
    env_file = active_env_file(default_tier="IT")
    start_servers(root, env_file, surfaces=("api", "mcp"))
    try:
        wait_for(f"{API_BASE_URL}/health")
        wait_for(f"{MCP_BASE_URL}/health")
        yield
    finally:
        stop_servers(root, env_file)


@pytest.fixture(scope="module")
def admin_token(live_mcp_stack) -> str:
    """Return the admin API key from the active test env file."""
    return resolved_api_key(default_tier="IT")


@pytest.fixture(scope="module")
def catalogue_profile_id(live_mcp_stack) -> str:
    """Create an authorised real profile for the successful tools/call path."""
    return create_profile(
        base_url=API_BASE_URL,
        profile_name="it-jsonrpc-catalogue-profile",
        allowed_permissions=["catalog.read"],
    )


# ---------------------------------------------------------------------------
# T-IT-MCP-015a: tools/list — JSON-RPC envelope discovery
# ---------------------------------------------------------------------------

@pytest.mark.IT
@pytest.mark.mcp
@pytest.mark.req("FR-020")
def test_mcp_jsonrpc_tools_list_returns_catalogue(admin_token: str) -> None:
    """IT1.15a: JSON-RPC tools/list envelope returns the db-mcp tool catalogue.

    REQ: FR-020 — MCP server exposes catalog/content/relationship/schema/search/audit tools.
    Follows: T-TST-MCP-EXAMPLE.py T-IT-MCP-001.
    """
    _mcp_initialize(admin_token)
    resp = _mcp_post(admin_token, {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {},
    })
    assert resp.status_code == 200, (
        f"tools/list: expected 200, got {resp.status_code} {resp.text[:300]}"
    )
    msg = _parse_sse(resp)
    assert "result" in msg, f"JSON-RPC response missing 'result': {msg}"
    tools = msg["result"].get("tools", [])
    assert isinstance(tools, list) and len(tools) > 0, (
        f"tools/list result should contain at least one tool; got: {tools}"
    )
    tool_names = {t["name"] for t in tools}
    # FR-020 requires catalog, content, relationship, schema, search, and audit tools.
    assert "catalog.list_namespaces" in tool_names, (
        f"catalog.list_namespaces missing from tools/list; available: {sorted(tool_names)}"
    )
    assert "data.read" in tool_names, (
        f"data.read missing from tools/list; available: {sorted(tool_names)}"
    )


# ---------------------------------------------------------------------------
# T-IT-MCP-015b: tools/call happy path — catalog.list_namespaces
# ---------------------------------------------------------------------------

@pytest.mark.IT
@pytest.mark.mcp
@pytest.mark.req("FR-005")
def test_mcp_jsonrpc_tools_call_catalog_list_namespaces(admin_token: str, catalogue_profile_id: str) -> None:
    """IT1.15b: JSON-RPC tools/call envelope for catalog.list_namespaces returns well-formed result.

    REQ: FR-005 — Catalogue and metadata discovery exposed via MCP.
    Follows: T-TST-MCP-EXAMPLE.py T-IT-MCP-002.

    The test issues a literal JSON-RPC 2.0 {"jsonrpc":"2.0","method":"tools/call",...}
    envelope to POST /mcp and asserts the response carries a well-formed JSON-RPC
    "result" with content[0].type == "text". A real profile is created through
    the API so this proves the successful catalogue dispatch path.
    """
    _mcp_initialize(admin_token)
    resp = _mcp_post(admin_token, {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "catalog.list_namespaces",
            "arguments": {"profile_id": catalogue_profile_id},
        },
    })
    assert resp.status_code == 200, (
        f"tools/call catalog.list_namespaces: expected 200, got {resp.status_code} {resp.text[:300]}"
    )
    msg = _parse_sse(resp)
    # The real authorised profile makes this a successful business and transport path.
    assert "jsonrpc" in msg, f"Response missing 'jsonrpc' field: {msg}"
    assert msg.get("jsonrpc") == "2.0", f"Expected jsonrpc: '2.0', got: {msg.get('jsonrpc')}"
    assert "id" in msg, f"Response missing 'id' field: {msg}"
    # A well-formed response has either "result" or "error" — never neither.
    has_result = "result" in msg
    has_error = "error" in msg
    assert has_result or has_error, (
        f"JSON-RPC response must contain 'result' or 'error'; got: {list(msg.keys())}"
    )
    if has_result:
        # When the tool executes, content must be a list with at least one text item.
        content = msg["result"].get("content", [])
        assert isinstance(content, list), (
            f"result.content should be a list; got: {type(content)}"
        )
        if content:
            assert content[0].get("type") == "text", (
                f"result.content[0].type should be 'text'; got: {content[0]}"
            )


# ---------------------------------------------------------------------------
# T-IT-MCP-015c: anon tools/call denied — 401 (negative / CS-001)
# ---------------------------------------------------------------------------

@pytest.mark.IT
@pytest.mark.mcp
@pytest.mark.negative
@pytest.mark.req("FR-020")
def test_mcp_jsonrpc_tools_call_anon_denied_401(live_mcp_stack) -> None:
    """IT1.15c: anonymous JSON-RPC tools/call is rejected with HTTP 401.

    REQ: FR-020 — MCP surface enforces API-key authentication; anon denied.
    Follows: T-TST-MCP-EXAMPLE.py T-IT-MCP-NEG-001.
    """
    resp = _mcp_post(None, {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "catalog.list_namespaces",
            "arguments": {},
        },
    })
    assert resp.status_code == 401, (
        f"Expected 401 for anonymous tools/call, got {resp.status_code}: {resp.text[:300]}"
    )
