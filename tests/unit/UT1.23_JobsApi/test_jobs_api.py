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

"""Unit coverage for Jobs WebUI administrative API actions."""

from __future__ import annotations

import json
from pathlib import Path

from cloud_dog_jobs import JobRequest, JobStatus
from fastapi.testclient import TestClient
import pytest

from src.servers.api.app import create_api_app

pytestmark = pytest.mark.unit


def _env_file(tmp_path: Path) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    env_file = tmp_path / "env-jobs-api"
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
            ]
        ),
        encoding="utf-8",
    )
    return env_file


def _client(tmp_path: Path) -> TestClient:
    return TestClient(create_api_app([str(_env_file(tmp_path))]))


def _submit_job(client: TestClient, *, actor: str, user_id: str, status: JobStatus) -> str:
    runtime = client.app.state.runtime
    job_id = runtime.job_queue.submit(
        JobRequest(
            job_type="discovery.sync_profile",
            queue_name="indexing",
            payload={"profile_id": f"unit-profile-{actor}"},
            app_id="db-mcp-server",
            user_id=user_id,
            request_source="unit-test",
            request_auth_identity=actor,
        )
    )
    runtime.job_backend.update_status(job_id, status.value)
    return job_id


@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-024")
def test_jobs_api_retries_and_deletes_job_records(tmp_path: Path) -> None:
    client = _client(tmp_path)
    job_id = _submit_job(client, actor="jobs-api-test", user_id="bootstrap-admin", status=JobStatus.FAILED)
    headers = {"X-API-Key": "test-api-key"}

    retry_response = client.post(f"/v1/jobs/{job_id}/retry", headers=headers)
    assert retry_response.status_code == 200, retry_response.text
    assert retry_response.json()["data"] == {"retried": True, "job_id": job_id}
    assert client.app.state.runtime.job_backend.get(job_id).status == JobStatus.QUEUED

    delete_response = client.delete(f"/v1/jobs/{job_id}", headers=headers)
    assert delete_response.status_code == 200, delete_response.text
    assert delete_response.json()["data"] == {"deleted": True, "job_id": job_id}
    assert client.app.state.runtime.job_backend.get(job_id) is None
    audit_logger = client.app.state.runtime.audit_logger
    if hasattr(audit_logger, "flush"):
        audit_logger.flush()
    audit_path = Path(str(client.app.state.runtime.config.get("log.audit_log", "logs/audit.log.jsonl")))
    audit_events = [
        json.loads(line)
        for line in audit_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert any(
        event.get("action") == "delete"
        and event.get("target", {}).get("type") == "job"
        and event.get("target", {}).get("id") == job_id
        for event in audit_events
    )

    list_response = client.get("/v1/jobs", headers=headers)
    assert list_response.status_code == 200, list_response.text
    listed_ids = {item["id"] for item in list_response.json()["data"]["items"]}
    assert job_id not in listed_ids


@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-024")
def test_jobs_api_non_admin_is_limited_to_own_jobs(tmp_path: Path) -> None:
    client = _client(tmp_path)
    admin_headers = {"X-API-Key": "test-api-key"}
    non_admin_key = (tmp_path / "flat_role_keys" / "read-write.key").read_text(encoding="utf-8").strip()
    non_admin_headers = {"X-API-Key": non_admin_key}
    principal = client.get("/v1/auth/me", headers=non_admin_headers).json()["data"]
    own_job_id = _submit_job(
        client,
        actor=principal["username"],
        user_id=principal["user_id"],
        status=JobStatus.RUNNING,
    )
    admin_job_id = _submit_job(
        client,
        actor="admin",
        user_id="bootstrap-admin",
        status=JobStatus.RUNNING,
    )

    non_admin_list = client.get("/v1/jobs", headers=non_admin_headers)
    assert non_admin_list.status_code == 200, non_admin_list.text
    non_admin_ids = {item["id"] for item in non_admin_list.json()["data"]["items"]}
    assert own_job_id in non_admin_ids
    assert admin_job_id not in non_admin_ids

    own_cancel = client.post(f"/v1/jobs/{own_job_id}/cancel", headers=non_admin_headers)
    assert own_cancel.status_code == 200, own_cancel.text
    assert own_cancel.json()["data"]["cancelled"] is True

    admin_get = client.get(f"/v1/jobs/{admin_job_id}", headers=non_admin_headers)
    assert admin_get.status_code == 403, admin_get.text
    assert "own jobs" in admin_get.json()["error"]["message"]

    admin_cancel = client.post(f"/v1/jobs/{admin_job_id}/cancel", headers=non_admin_headers)
    assert admin_cancel.status_code == 403, admin_cancel.text
    assert "own jobs" in admin_cancel.json()["error"]["message"]

    own_delete = client.delete(f"/v1/jobs/{own_job_id}", headers=non_admin_headers)
    assert own_delete.status_code == 403, own_delete.text
    assert "delete requires admin" in own_delete.json()["error"]["message"]

    admin_list = client.get("/v1/jobs", headers=admin_headers)
    assert admin_list.status_code == 200, admin_list.text
    admin_ids = {item["id"] for item in admin_list.json()["data"]["items"]}
    assert {own_job_id, admin_job_id}.issubset(admin_ids)
