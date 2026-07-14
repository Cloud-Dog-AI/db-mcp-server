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
# Description: Audit browse service must surface recent domain events across
#   rotated logs and de-noise the high-volume http.read request trail.
# Related requirements: AC-02, NF-01
# Related tests: UT1.56

"""W28E-1882: the audit browse surface (``audit.list_events`` / WebUI Audit page)
must return actionable domain events even when the ``http.read`` request trail has
flooded and rotated the tip file.

Regression proof for the observed preprod defect: a job delete / secret reveal is
emitted to the audit log, then a burst of ``http.read`` request-audit events fills
the 10 MB tip and rotates it, so ``AuditEventService.list_events`` (which read only
the tip) returned nothing but ``http.read`` noise and the WebUI Audit page / the
w28a-691 + w28a-803 §3.4 E2E specs could not find the event. The fix reads across
rotated siblings and suppresses the read-request noise by default (the log file
still retains every event for compliance).
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path
from typing import Any

import pytest

from src.core.audit.service import AuditEventService

pytestmark = pytest.mark.unit


class _FakeAccessControl:
    def require_request_permission(self, *_a: Any, **_k: Any) -> None:
        return None


class _FakeConfig:
    def __init__(self, audit_log: str) -> None:
        self._audit_log = audit_log

    def get(self, key: str, default: Any = None) -> Any:
        return self._audit_log if key == "log.audit_log" else default


class _FakeRuntime:
    def __init__(self, audit_log: str) -> None:
        self.config = _FakeConfig(audit_log)
        self.access_control = _FakeAccessControl()


def _event(seq: int, event_type: str = "http.read", action: str = "read", **extra: Any) -> str:
    payload: dict[str, Any] = {
        "event_type": event_type,
        "action": action,
        "correlation_id": f"c{seq}",
        "seq": seq,
    }
    payload.update(extra)
    return json.dumps(payload)


def _write(path: Path, seqs: range, **kw: Any) -> None:
    path.write_text("\n".join(_event(i, **kw) for i in seqs) + "\n", encoding="utf-8")


def _service(tmp_path: Path) -> tuple[AuditEventService, Path]:
    tip = tmp_path / "audit.log.jsonl"
    return AuditEventService(_FakeRuntime(str(tip))), tip


@pytest.mark.UT
@pytest.mark.webui
@pytest.mark.req("AC-02")
def test_domain_event_surfaced_across_rotation_despite_http_read_flood(tmp_path: Path) -> None:
    """A delete/reveal in a rotated sibling is returned even when the tip is all noise."""
    tip = tmp_path / "audit.log.jsonl"
    # Oldest → newer rotations; the domain events live in .2, buried under read noise.
    _write(tmp_path / "audit.log.jsonl.3", range(0, 200))
    (tmp_path / "audit.log.jsonl.2").write_text(
        "\n".join(
            [
                *[_event(i) for i in range(200, 260)],
                _event(9001, "job.delete", "delete", target={"type": "job", "id": "job-xyz"}),
                _event(9002, "admin.config.reveal", "config.reveal", command_text="settings reveal secrets"),
                *[_event(i) for i in range(260, 320)],
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    _write(tmp_path / "audit.log.jsonl.1", range(400, 600))
    _write(tip, range(600, 629))  # tip = 29 http.read events (post-rotation)

    service = AuditEventService(_FakeRuntime(str(tip)))

    # WebUI Audit page / §3.4 reveal spec: limit 25, no filter.
    events = service.list_events(request=None, limit=25)
    types = {e["event_type"] for e in events}
    assert "job.delete" in types, f"job.delete must surface, got {types}"
    assert "admin.config.reveal" in types, f"admin.config.reveal must surface, got {types}"
    assert "http.read" not in types, "read-request noise must be suppressed by default"

    # jobs spec: limit 500, filters action == delete.
    deletes = [e for e in service.list_events(request=None, limit=500) if e.get("action") == "delete"]
    assert len(deletes) == 1 and deletes[0]["target"]["id"] == "job-xyz"


@pytest.mark.UT
@pytest.mark.webui
@pytest.mark.req("AC-02")
def test_http_read_trail_still_available_on_explicit_request(tmp_path: Path) -> None:
    """Explicit event_type='http.read' opts back into the request trail (nothing lost)."""
    service, tip = _service(tmp_path)
    _write(tip, range(0, 40))  # all http.read
    events = service.list_events(request=None, limit=25, event_type="http.read")
    assert len(events) == 25
    assert all(e["event_type"] == "http.read" for e in events)


@pytest.mark.UT
@pytest.mark.webui
@pytest.mark.req("AC-02")
def test_explicit_event_filter_scans_past_nonmatching_full_rotation(tmp_path: Path) -> None:
    """A filtered lookup reaches .2 even when .1 alone exceeds the requested limit."""
    service, tip = _service(tmp_path)
    _write(tip, range(800, 820), event_type="tool.call", action="call")
    _write(tmp_path / "audit.log.jsonl.1", range(200, 800), event_type="tool.call", action="call")
    (tmp_path / "audit.log.jsonl.2").write_text(
        _event(9002, "admin.config.reveal", "config.reveal", command_text="settings reveal secrets") + "\n",
        encoding="utf-8",
    )

    events = service.list_events(request=None, limit=25, event_type="admin.config.reveal")

    assert [event["seq"] for event in events] == [9002]


@pytest.mark.UT
@pytest.mark.webui
@pytest.mark.req("AC-02")
def test_newest_last_ordering_preserved_and_reversed_output(tmp_path: Path) -> None:
    """Result is newest-first (list_events reverses the newest-last internal stream)."""
    service, tip = _service(tmp_path)
    (tmp_path / "audit.log.jsonl.1").write_text(
        "\n".join(_event(i, "job.delete", "delete") for i in range(0, 5)) + "\n", encoding="utf-8"
    )
    _write(tip, range(5, 10), event_type="job.delete", action="delete")
    events = service.list_events(request=None, limit=50)
    seqs = [e["seq"] for e in events]
    assert seqs == sorted(seqs, reverse=True), f"newest-first expected, got {seqs}"
    assert seqs[0] == 9 and seqs[-1] == 0


@pytest.mark.UT
@pytest.mark.webui
@pytest.mark.req("AC-02")
def test_gzip_rotation_is_read(tmp_path: Path) -> None:
    """A compressed .gz rotation is decoded and its domain events surfaced."""
    tip = tmp_path / "audit.log.jsonl"
    with gzip.open(tmp_path / "audit.log.jsonl.1.gz", "wt", encoding="utf-8") as fh:
        fh.write(_event(1, "user.update", "update", target={"type": "user", "id": "u1"}) + "\n")
    _write(tip, range(10, 20))  # http.read noise at tip
    service = AuditEventService(_FakeRuntime(str(tip)))
    events = service.list_events(request=None, limit=25)
    assert any(e["event_type"] == "user.update" for e in events)


@pytest.mark.UT
@pytest.mark.webui
@pytest.mark.req("AC-02")
def test_plain_and_gzip_siblings_do_not_consume_separate_generation_slots(tmp_path: Path) -> None:
    """A ``.1.gz`` sibling must not exclude an in-window event in ``.3``."""
    service, tip = _service(tmp_path)
    _write(tip, range(900, 910), event_type="tool.call", action="call")
    _write(tmp_path / "audit.log.jsonl.1", range(800, 810), event_type="tool.call", action="call")
    with gzip.open(tmp_path / "audit.log.jsonl.1.gz", "wt", encoding="utf-8") as fh:
        fh.write(_event(799, "tool.call", "call") + "\n")
    _write(tmp_path / "audit.log.jsonl.2", range(700, 710), event_type="tool.call", action="call")
    (tmp_path / "audit.log.jsonl.3").write_text(
        _event(9003, "admin.config.reveal", "config.reveal", command_text="settings reveal secrets") + "\n",
        encoding="utf-8",
    )

    events = service.list_events(request=None, limit=500, event_type="admin.config.reveal")

    assert [event["seq"] for event in events] == [9003]


@pytest.mark.UT
@pytest.mark.webui
@pytest.mark.req("AC-02")
def test_missing_and_single_file_behaviour(tmp_path: Path) -> None:
    """Absent log → empty; single (unrotated) file still parses (integration-test shape)."""
    service, tip = _service(tmp_path)
    assert service.list_events(request=None, limit=50) == []
    tip.write_text(_event(1) + "\n" + _event(2, "job.delete", "delete") + "\n", encoding="utf-8")
    events = service.list_events(request=None, limit=50)
    assert any(e["event_type"] == "job.delete" for e in events)


@pytest.mark.UT
@pytest.mark.webui
@pytest.mark.req("AC-02")
def test_get_event_finds_event_across_rotation(tmp_path: Path) -> None:
    """get_event resolves a correlation id that has rotated off the tip."""
    tip = tmp_path / "audit.log.jsonl"
    (tmp_path / "audit.log.jsonl.2").write_text(_event(4242, "job.delete", "delete") + "\n", encoding="utf-8")
    _write(tip, range(0, 30))
    service = AuditEventService(_FakeRuntime(str(tip)))
    found = service.get_event(request=None, event_id="c4242")
    assert found["event_type"] == "job.delete"
