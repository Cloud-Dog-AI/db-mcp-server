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
# Description: NIST AU-3 field population for the REST + A2A audit emit paths.
# Related requirements: FR-028, AC-02 (PS-AUDIT-LOG §3/§7); W28E-1879 DM-AL-09/DM-D-12/DM-X-19
# Related tests: UT1.30

"""W28E-1879: deterministic NIST AU-3 field-population proof for the shared audit
context helpers used by the REST config-reveal / job-delete routes (DM-AL-09,
DM-D-12) and the A2A task boundary (DM-X-19).

Every event is emitted through the real platform ``cloud_dog_logging.AuditLogger``
(a thin, package-consuming path — no bespoke audit code). The four mandatory AU-3
fields (actor, client IP / source address, session id, correlation id) are asserted
non-blank on the emitted ``AuditEvent.to_dict()`` output — the raw event the audit
JSONL and the WebUI audit-log / recent-activity surfaces read.
"""

from __future__ import annotations

from typing import Any

import pytest
from starlette.requests import Request

from cloud_dog_logging import Actor, Target, set_correlation_id, clear_correlation_id
from cloud_dog_logging.audit_logger import AuditLogger

from src.servers.mcp.tool_rbac_audit import (
    actor_from_principal,
    au3_request_fields,
    emit_a2a_audit,
)

pytestmark = pytest.mark.unit


class _CapturingSink:
    """Real AuditSink capturing emitted events as dicts (deterministic raw output)."""

    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def emit(self, event: Any) -> None:
        self.events.append(event.to_dict())

    def flush(self) -> None:  # pragma: no cover - trivial
        pass

    def close(self) -> None:  # pragma: no cover - trivial
        pass


def _request(*, user: str | None, roles: list[str], api_key_id: str, correlation_id: str, ip: str) -> Request:
    """Build a real Starlette Request carrying the authenticated principal on state."""
    state: dict[str, Any] = {
        "roles": roles,
        "api_key_id": api_key_id,
        "correlation_id": correlation_id,
    }
    if user is not None:
        state["user"] = user
        state["username"] = user
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/v1/jobs/j-1",
            "headers": [],
            "query_string": b"",
            "client": (ip, 54321),
            "state": state,
        }
    )


class _Principal:
    """Minimal access-control principal object (as returned by principal_from_request)."""

    def __init__(self, user_id: str, roles: list[str]) -> None:
        self.user_id = user_id
        self.roles = roles


def _assert_au3(event: dict[str, Any], *, actor_id: str, ip: str, session_id: str) -> None:
    """Assert the four NIST AU-3 fields are populated (not blank) on a raw event."""
    actor = event.get("actor", {})
    details = event.get("details", {})
    assert actor.get("id") == actor_id, f"actor must name the subject: {actor}"
    assert actor.get("ip") == ip, f"actor.ip (client_ip) must be populated: {actor}"
    assert event.get("source_address") == ip, f"source_address must be populated: {event.get('source_address')!r}"
    assert event.get("correlation_id"), "correlation_id must be populated (top-level)"
    assert details.get("session_id") == session_id, f"session_id must be populated: {details}"


@pytest.mark.UT
@pytest.mark.req("FR-028")
@pytest.mark.api
def test_au3_request_fields_extracts_all_context() -> None:
    """au3_request_fields returns client_ip, source_address, session_id, correlation_id."""
    request = _request(user="u-admin", roles=["admin"], api_key_id="key-9", correlation_id="corr-1", ip="198.51.100.10")
    fields = au3_request_fields(request)
    assert fields["client_ip"] == "198.51.100.10"
    assert fields["source_address"] == "198.51.100.10"
    assert fields["session_id"] == "key-9"
    assert fields["correlation_id"] == "corr-1"


@pytest.mark.UT
@pytest.mark.req("FR-028")
@pytest.mark.api
def test_api_job_delete_style_emit_populates_au3() -> None:
    """The REST job-delete (log_crud) emit path (DM-AL-09/DM-D-12) populates every AU-3 field."""
    sink = _CapturingSink()
    audit = AuditLogger(sink=sink, service_name="db-mcp-server")
    request = _request(user="u-admin", roles=["admin"], api_key_id="key-del-1", correlation_id="corr-del", ip="198.51.100.20")

    # Exactly the pattern the fixed route uses.
    _au3 = au3_request_fields(request)
    _client_ip = _au3.pop("client_ip", None)
    audit.log_crud(
        actor=Actor(type="user", id="u-admin", roles=["admin"], ip=_client_ip),
        action="delete",
        target=Target(type="job", id="job-xyz"),
        outcome="success",
        **_au3,
        job_type="discovery.sync_profile",
    )

    assert len(sink.events) == 1
    event = sink.events[0]
    assert event.get("action") == "delete" and event.get("target", {}).get("id") == "job-xyz"
    _assert_au3(event, actor_id="u-admin", ip="198.51.100.20", session_id="key-del-1")


@pytest.mark.UT
@pytest.mark.req("FR-028")
@pytest.mark.api
def test_api_config_reveal_style_emit_populates_au3() -> None:
    """The REST config-reveal (log_privileged) emit path (DM-AL-09) populates every AU-3 field."""
    sink = _CapturingSink()
    audit = AuditLogger(sink=sink, service_name="db-mcp-server")
    request = _request(user="u-admin", roles=["admin"], api_key_id="key-rev-1", correlation_id="corr-rev", ip="198.51.100.30")

    _au3 = au3_request_fields(request)
    _client_ip = _au3.pop("client_ip", None)
    audit.log_privileged(
        actor=Actor(type="user", id="u-admin", roles=["admin"], ip=_client_ip),
        action="config.reveal",
        target=Target(type="config", id="effective-runtime"),
        outcome="success",
        command_text="settings reveal secrets",
        **_au3,
        secret_paths=["db.password"],
    )

    assert len(sink.events) == 1
    event = sink.events[0]
    assert event.get("event_type") == "admin.config.reveal"
    _assert_au3(event, actor_id="u-admin", ip="198.51.100.30", session_id="key-rev-1")


@pytest.mark.UT
@pytest.mark.a2a
@pytest.mark.req("FR-028")
def test_a2a_task_emit_populates_au3() -> None:
    """emit_a2a_audit (DM-X-19) populates every AU-3 field from request + principal."""
    sink = _CapturingSink()
    audit = AuditLogger(sink=sink, service_name="db-mcp-server")
    # Real inbound A2A request (carries client IP + session on state); actor from principal.
    request = _request(user=None, roles=[], api_key_id="key-a2a-1", correlation_id="corr-a2a", ip="198.51.100.40")
    principal = _Principal(user_id="agent-alpha", roles=["data-reader"])

    emit_a2a_audit(
        audit,
        request=request,
        principal=principal,
        skill_id="data_query",
        input_text="select 1",
        success=True,
        duration_ms=12.0,
    )

    assert len(sink.events) == 1
    event = sink.events[0]
    assert event.get("details", {}).get("target_name") == "a2a.data_query"
    assert event.get("details", {}).get("surface") == "a2a"
    assert event.get("actor", {}).get("roles") == ["data-reader"]
    _assert_au3(event, actor_id="agent-alpha", ip="198.51.100.40", session_id="key-a2a-1")


@pytest.mark.UT
@pytest.mark.req("FR-028")
@pytest.mark.a2a
def test_actor_from_principal_anonymous_when_unresolved() -> None:
    """actor_from_principal degrades safely to anonymous, still carrying client IP."""
    actor = actor_from_principal(object(), ip="198.51.100.50")
    assert actor.id == "anonymous"
    assert actor.type == "system", "platform Actor type must be user/service/system"
    assert actor.ip == "198.51.100.50"


@pytest.mark.UT
@pytest.mark.req("FR-028")
@pytest.mark.api
def test_correlation_contextvar_flows_to_top_level() -> None:
    """When the request correlation contextvar is set, it flows to the event top-level."""
    clear_correlation_id()
    set_correlation_id("corr-ctx-777")
    try:
        sink = _CapturingSink()
        audit = AuditLogger(sink=sink, service_name="db-mcp-server")
        audit.log_crud(
            actor=Actor(type="user", id="u-admin", roles=["admin"], ip="198.51.100.60"),
            action="delete",
            target=Target(type="job", id="job-ctx"),
            outcome="success",
            source_address="198.51.100.60",
            session_id="key-ctx",
        )
        assert sink.events[0].get("correlation_id") == "corr-ctx-777"
    finally:
        clear_correlation_id()
