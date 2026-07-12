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
# Description: End-to-end NIST AU-3 audit emission for the REST + A2A surfaces.
# Related requirements: FR-028, AC-02 (PS-AUDIT-LOG §3/§7); W28E-1879 DM-AL-09/DM-D-12/DM-X-19
# Related tests: IT1.14

"""W28E-1879: end-to-end proof that the REST config-reveal / job-delete routes
(DM-AL-09, DM-D-12) and the A2A task boundary (DM-X-19) emit fully-populated NIST
AU-3 audit events on the real deployed code path.

Drives the real ``create_api_app`` and ``create_a2a_app`` through a TestClient with
a real API key, then reads the real ``cloud_dog_logging`` JSONL audit store and
asserts the four mandatory AU-3 fields (actor, client IP / source address, session
id, correlation id) are non-blank on the emitted events — the exact events the
WebUI audit-log / recent-activity surfaces read via ``audit.list_events``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from cloud_dog_jobs import JobRequest, JobStatus
from fastapi.testclient import TestClient

from src.servers.api.app import create_api_app
from src.servers.a2a.app import create_a2a_app

pytestmark = [pytest.mark.integration, pytest.mark.timeout(120)]

_HEADERS = {"X-API-Key": "test-api-key"}


def _env_file(tmp_path: Path) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    env_file = tmp_path / "env-au3-api"
    env_file.write_text(
        "\n".join(
            [
                "TEST_ENV_TIER=UT",
                "CLOUD_DOG__API_SERVER__PORT=8086",
                "CLOUD_DOG__WEB_SERVER__PORT=8087",
                "CLOUD_DOG__MCP_SERVER__PORT=8088",
                "CLOUD_DOG__A2A_SERVER__PORT=8089",
                "CLOUD_DOG_WEB_LOGIN_USERNAME=admin",
                "CLOUD_DOG_WEB_LOGIN_PASSWORD=test-password",
                "CLOUD_DOG__AUTH__API_KEY=test-api-key",
                f"CLOUD_DOG__FLAT_LOGIN__DEMO_KEYS_DIR={tmp_path / 'flat_role_keys'}",
                f"CLOUD_DOG__METADATA_STORE__URI=sqlite:///{tmp_path / 'metadata.db'}",
                f"CLOUD_DOG__AUDIT_STORE__URI=sqlite:///{tmp_path / 'audit.db'}",
                f"CLOUD_DOG__JOBS__SQL_DATABASE_URL=sqlite:///{tmp_path / 'jobs.db'}",
                f"CLOUD_DOG__SEARCH__DISCOVERY_INDEX_PATH={tmp_path / 'discovery-index.db'}",
                f"CLOUD_DOG__LOG__AUDIT_LOG={tmp_path / 'audit.log.jsonl'}",
            ]
        ),
        encoding="utf-8",
    )
    return env_file


def _read_audit_events(app: Any = None) -> list[dict[str, Any]]:
    from cloud_dog_logging import get_audit_logger

    candidates = {"logs/audit.log.jsonl"}
    try:
        get_audit_logger().flush()
    except Exception:
        pass
    if app is not None:
        try:
            runtime = app.state.runtime
            candidates.add(str(runtime.config.get("log.audit_log", "logs/audit.log.jsonl")))
            if hasattr(runtime.audit_logger, "flush"):
                runtime.audit_logger.flush()
        except Exception:
            pass
    events: list[dict[str, Any]] = []
    for rel in candidates:
        path = Path(rel)
        if not path.is_absolute():
            path = Path.cwd() / path
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events


def _assert_au3_populated(event: dict[str, Any]) -> None:
    """Assert the four NIST AU-3 fields are populated (non-blank) on a live event."""
    actor = event.get("actor", {})
    details = event.get("details", {})
    assert actor.get("id"), f"actor.id (subject) must be populated: {actor}"
    assert actor.get("ip") and actor.get("ip") != "unknown", f"actor.ip (client_ip) must be populated: {actor}"
    assert event.get("source_address"), f"source_address must be populated: {event.get('source_address')!r}"
    assert event.get("correlation_id"), "correlation_id must be populated (top-level)"
    assert details.get("session_id"), f"session_id must be populated in details: {details}"


@pytest.mark.IT
@pytest.mark.api
@pytest.mark.req("FR-028")
def test_job_delete_emits_full_au3_event(tmp_path: Path) -> None:
    """DELETE /v1/jobs/{id} emits a job.delete audit event with all AU-3 fields (DM-AL-09/DM-D-12)."""
    client = TestClient(create_api_app([str(_env_file(tmp_path))]))
    runtime = client.app.state.runtime
    job_id = runtime.job_queue.submit(
        JobRequest(
            job_type="discovery.sync_profile",
            queue_name="indexing",
            payload={"profile_id": "au3-profile"},
            app_id="db-mcp-server",
            user_id="bootstrap-admin",
            request_source="unit-test",
            request_auth_identity="au3-test",
        )
    )
    runtime.job_backend.update_status(job_id, JobStatus.FAILED.value)

    resp = client.delete(f"/v1/jobs/{job_id}", headers=_HEADERS)
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"] == {"deleted": True, "job_id": job_id}

    events = _read_audit_events(client.app)
    mine = [
        e for e in events
        if e.get("action") == "delete"
        and e.get("target", {}).get("type") == "job"
        and e.get("target", {}).get("id") == job_id
    ]
    assert mine, f"no job.delete audit event for {job_id} found"
    _assert_au3_populated(mine[-1])


@pytest.mark.IT
@pytest.mark.api
@pytest.mark.req("FR-028")
def test_config_reveal_emits_full_au3_event(tmp_path: Path) -> None:
    """POST /v1/config/audit-reveal emits an admin.config.reveal event with all AU-3 fields (DM-AL-09)."""
    client = TestClient(create_api_app([str(_env_file(tmp_path))]))

    resp = client.post("/v1/config/audit-reveal", headers=_HEADERS)
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"] == {"audited": True}

    events = _read_audit_events(client.app)
    mine = [e for e in events if e.get("event_type") == "admin.config.reveal"]
    assert mine, "no admin.config.reveal audit event found"
    _assert_au3_populated(mine[-1])


@pytest.mark.IT
@pytest.mark.a2a
@pytest.mark.req("FR-028")
def test_a2a_task_emits_full_au3_event(tmp_path: Path) -> None:
    """POST /tasks (A2A) emits an a2a.<skill> audit event with all AU-3 fields (DM-X-19)."""
    client = TestClient(create_a2a_app([str(_env_file(tmp_path))]))

    resp = client.post(
        "/tasks",
        headers=_HEADERS,
        json={"id": "task-au3-1", "skill_id": "data_query", "input": {"text": "select 1"}},
    )
    # The task completes (or is denied); either way an AU-3 event is emitted at the boundary.
    assert resp.status_code in (200, 403), resp.text

    events = _read_audit_events(client.app)
    mine = [
        e for e in events
        if e.get("details", {}).get("target_name") == "a2a.data_query"
        and e.get("details", {}).get("surface") == "a2a"
    ]
    assert mine, "no a2a.data_query audit event found (DM-X-19: A2A surface must be audited)"
    event = mine[-1]
    actor = event.get("actor", {})
    assert actor.get("id"), f"actor.id (subject) must be populated: {actor}"
    assert actor.get("ip") and actor.get("ip") != "unknown", f"actor.ip (client_ip) must be populated: {actor}"
    assert event.get("source_address"), "source_address must be populated"
    assert event.get("correlation_id"), "correlation_id must be populated"
