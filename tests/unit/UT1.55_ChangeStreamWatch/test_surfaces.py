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
# Description: UT1.55 — change-watch surface registration (MCP / REST / A2A).
# Related requirements: CSTREAM-DB-001
# Related tests: UT1.55

"""UT1.55 — MCP tools, REST routes, A2A skills + streaming advertisement."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.core.change_stream import WatchService
from src.servers.api.watches import create_watches_router
from src.servers.mcp.tool_rbac_audit import TOOL_RBAC_MAP
from src.servers.mcp.watch_tools import build_watch_tool_registry


_WATCH_TOOLS = {
    "db_watch_create",
    "db_watch_list",
    "db_watch_status",
    "db_watch_get_batch",
    "db_watch_ack",
    "db_watch_recover",
    "db_watch_pause",
    "db_watch_resume",
    "db_watch_delete",
    "db_watch_test_event",
    "db_watch_capabilities",
}


def _runtime():
    return SimpleNamespace(
        watch_service=WatchService(engine=None),
        access_control=SimpleNamespace(),
    )


@pytest.mark.req("CSTREAM-DB-001")
@pytest.mark.unit
@pytest.mark.UT
@pytest.mark.internal
def test_mcp_watch_tool_family_registered() -> None:
    tools = build_watch_tool_registry(_runtime())
    assert _WATCH_TOOLS.issubset(set(tools))
    for name in _WATCH_TOOLS:
        assert tools[name].description  # every tool advertises a description


@pytest.mark.req("CSTREAM-DB-001")
@pytest.mark.unit
@pytest.mark.UT
@pytest.mark.internal
def test_mcp_watch_tools_have_rbac_map_entries() -> None:
    for name in _WATCH_TOOLS:
        assert name in TOOL_RBAC_MAP
    # read verbs vs mutating verbs bind to the correct permission family.
    assert TOOL_RBAC_MAP["db_watch_list"] == "db:data:read"
    assert TOOL_RBAC_MAP["db_watch_create"] == "db:data:write"


@pytest.mark.req("CSTREAM-DB-001")
@pytest.mark.unit
@pytest.mark.UT
@pytest.mark.internal
def test_rest_router_registers_all_watch_routes() -> None:
    router = create_watches_router(_runtime(), "/v1")
    paths = {(route.path, tuple(sorted(route.methods))) for route in router.routes}
    flat = {p for p, _ in paths}
    assert "/v1/watches" in flat
    assert "/v1/watches/{watch_id}" in flat
    assert "/v1/watches/{watch_id}/status" in flat
    assert "/v1/watches/{watch_id}/events" in flat
    assert "/v1/watches/{watch_id}/stream" in flat  # SSE streaming feed
    assert "/v1/watches/{watch_id}/ack" in flat
    assert "/v1/watches/{watch_id}/recover" in flat
    assert "/v1/watches/{watch_id}/pause" in flat
    assert "/v1/watches/{watch_id}/resume" in flat
    assert "/v1/watches/{watch_id}/test-event" in flat
    assert "/v1/watches/capabilities" in flat


@pytest.mark.req("CSTREAM-DB-001")
@pytest.mark.unit
@pytest.mark.UT
@pytest.mark.internal
def test_a2a_card_advertises_streaming_true_and_watch_skills() -> None:
    # The A2A card literal lives in the app factory; assert on the source contract
    # so we prove the advertisement flip without booting the full runtime.
    import inspect

    from src.servers.a2a import app as a2a_app

    source = inspect.getsource(a2a_app.create_a2a_app)
    assert '"streaming": True' in source
    assert '"streaming": False' not in source
    for skill in ("db_watch_create", "db_watch_list", "db_watch_status", "db_watch_get_batch"):
        assert skill in source
