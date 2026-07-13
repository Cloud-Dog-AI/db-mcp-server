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
# Description: Field-level NIST AU-3 audit emission for the MCP surface (TD-001).
# Related requirements: FR-028, AC-02 (PS-AUDIT-LOG §3/§7)
# Related tests: IT1.13

"""TD-001 (W28E-1808B): every MCP tool call emits a fully-populated NIST AU-3
audit event through the platform AuditLogger.

Proves PS-AUDIT-LOG §3 mandatory field population on the MCP surface (which was
previously un-audited: ``wrap_tool_with_audit`` was imported but never applied).
Uses the real runtime, the real ``cloud_dog_logging`` AuditLogger, the real JSONL
audit store, and a real Starlette ``Request`` — no mocks.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from starlette.requests import Request

from src.common.runtime import RuntimeFactory
from src.servers.mcp.audit_tools import build_audit_tool_registry
from src.servers.mcp.tool_rbac_audit import wrap_tool_contract
from tests.helpers.server_runtime import resolved_api_key

pytestmark = [pytest.mark.integration, pytest.mark.timeout(120)]


def _audit_log_path(runtime) -> Path:
    rel = str(runtime.config.get("log.audit_log", "logs/audit.log.jsonl"))
    path = Path(rel)
    if not path.is_absolute():
        path = Path.cwd() / path
    return path


def _make_request(*, user: str, roles: list[str], correlation_id: str, api_key_id: str, ip: str, principal=None) -> Request:
    """Build a real Starlette Request carrying the authenticated principal on state."""
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/mcp/tools/audit.list_events",
        "headers": [],
        "query_string": b"",
        "client": (ip, 54321),
        "state": {
            "user": user,
            "username": user,
            "roles": roles,
            "api_key_id": api_key_id,
            "correlation_id": correlation_id,
            "principal": principal,
        },
    }
    return Request(scope)


@pytest.mark.IT
@pytest.mark.mcp
@pytest.mark.req("FR-028")
@pytest.mark.asyncio
async def test_mcp_tool_call_emits_full_au3_audit_event() -> None:
    """A wrapped MCP tool call emits a tool.call event with every AU-3 field populated."""
    runtime = RuntimeFactory.create(["tests/env-UT"])
    registry = build_audit_tool_registry(runtime)
    assert "audit.list_events" in registry, "audit.list_events tool must be registered"

    wrapped = wrap_tool_contract(runtime, registry["audit.list_events"])
    assert wrapped.handler is not registry["audit.list_events"].handler, "handler must be wrapped"

    # Real authenticated principal (so the call may also exercise the success path).
    try:
        principal = runtime.access_control.verify_api_key(resolved_api_key("tests/env-UT", default_tier="UT"))
    except Exception:
        principal = None

    audit_path = _audit_log_path(runtime)
    audit_path.parent.mkdir(parents=True, exist_ok=True)

    request = _make_request(
        user="u-admin",
        roles=["admin"],
        correlation_id="corr-td001-1808b",
        api_key_id="key-admin-1",
        ip="203.0.113.7",
        principal=principal,
    )

    # Invoke the wrapped tool. The AU-3 audit event MUST be emitted whether the
    # tool succeeds or fails (PS-AUDIT-LOG §4: failed/denied ops audited too), so
    # a tool-level exception is expected-tolerated here — the assertion is on the event.
    try:
        result = wrapped.handler({"limit": 5}, request)
        if hasattr(result, "__await__"):
            await result
    except Exception:
        pass

    if hasattr(runtime.audit_logger, "flush"):
        runtime.audit_logger.flush()
    assert audit_path.exists(), f"audit store not written at {audit_path}"
    events = [json.loads(line) for line in audit_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    # find THIS test's emitted MCP tool.call event (robust against pre-existing events).
    mine = [
        e for e in events
        if str(e.get("event_type")) == "tool.call"
        and isinstance(e.get("actor"), dict) and e["actor"].get("id") == "u-admin"
        and "corr-td001-1808b" in json.dumps(e)
    ]
    assert mine, f"no TD-001 MCP tool.call audit event for actor u-admin found in {audit_path}"
    event = mine[-1]
    actor = event.get("actor", {})
    details = event.get("details", {})

    # PS-AUDIT-LOG §3 mandatory NIST AU-3 fields must be populated (not blank).
    assert actor.get("id") == "u-admin", f"actor.id must be populated: {actor}"
    assert actor.get("roles") == ["admin"], f"actor.roles must be populated: {actor}"
    assert actor.get("ip") == "203.0.113.7", f"actor.ip (client_ip) must be populated: {actor}"
    # cloud-dog-logging carries the canonical source address in Actor.ip
    # and details.client_ip. A legacy top-level source_address is intentionally
    # absent; detail keys ending in "address" are redacted by the package.
    assert details.get("client_ip") == "203.0.113.7", "details.client_ip must be populated"
    assert event.get("correlation_id"), "correlation_id must be populated"
    assert details.get("session_id") == "key-admin-1", "session_id must be populated"
    assert details.get("target_name") == "audit.list_events", "target (tool) must be populated"
    assert str(event.get("outcome")) in {"success", "failure", "denied"}, "outcome must be a valid AU-3 value"
    assert event.get("duration_ms") is not None, "duration_ms must be present"
