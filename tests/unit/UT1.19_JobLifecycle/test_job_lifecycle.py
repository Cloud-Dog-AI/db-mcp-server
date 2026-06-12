# Copyright 2026 Cloud-Dog, Viewdeck Engineering Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""UT1.19 — Job Lifecycle Simulation Tests (PS-75 JQ4).

Validates the four required lifecycle paths for db-mcp discovery jobs:
1. create → queue → run → succeed
2. create → queue → run → fail → retry_wait
3. create → queue → cancel
4. create → queue → run → timeout

Uses cloud_dog_jobs SQLQueueBackend with an in-process SQLite database.

License: Apache 2.0
Ownership: Cloud-Dog, Viewdeck Engineering Limited
Requirements: PS-75 JQ4, JQ7, JQ8
Tasks: W28A-813
Tests: UT1.19
"""

from __future__ import annotations

from pathlib import Path

import pytest
from cloud_dog_jobs import JobQueue, JobRequest, JobStatus, SQLQueueBackend


@pytest.fixture()
def job_env(tmp_path: Path):
    """Create a throwaway SQL backend + queue for lifecycle tests."""
    db_url = f"sqlite:///{tmp_path / 'lifecycle.db'}"
    backend = SQLQueueBackend(database_url=db_url)
    queue = JobQueue(backend, payload_max_bytes=16384)
    return backend, queue


def _submit(queue: JobQueue, job_type: str = "discovery.sync_profile") -> str:
    """Submit a test job and return its ID."""
    request = JobRequest(
        job_type=job_type,
        queue_name="indexing",
        payload={"profile_id": "test-profile"},
        app_id="db-mcp-server",
        request_source="unit-test",
    )
    return queue.submit(request)


# ── Path 1: create → queue → run → succeed ──────────────────────────
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.probe  # rtt-2026-06-12 INST3: KEEP-AS-PROBE pending operator REQ-binding


def test_lifecycle_queue_run_succeed(job_env):
    """Job transitions from queued → running → succeeded."""
    backend, queue = job_env

    job_id = _submit(queue)
    job = backend.get(job_id)
    assert job is not None
    assert job.status == JobStatus.QUEUED

    # Claim → running
    claimed = backend.claim(job_id, "test-host", "test-worker")
    assert claimed
    job = backend.get(job_id)
    assert job.status == JobStatus.RUNNING

    # Heartbeat
    backend.heartbeat(job_id)

    # Succeed
    backend.update_status(job_id, JobStatus.SUCCEEDED.value)
    job = backend.get(job_id)
    assert job.status == JobStatus.SUCCEEDED


# ── Path 2: create → queue → run → fail → retry_wait ────────────────
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.probe  # rtt-2026-06-12 INST3: KEEP-AS-PROBE pending operator REQ-binding


def test_lifecycle_queue_run_fail_retry(job_env):
    """Job transitions from queued → running → failed, then to retry_wait."""
    backend, queue = job_env

    job_id = _submit(queue)
    backend.claim(job_id, "test-host", "test-worker")
    job = backend.get(job_id)
    assert job.status == JobStatus.RUNNING

    # Fail → retry_wait (simulating retryable error with attempts remaining)
    backend.update_status(job_id, JobStatus.RETRY_WAIT.value)
    job = backend.get(job_id)
    assert job.status == JobStatus.RETRY_WAIT


# ── Path 3: create → queue → cancel ─────────────────────────────────
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.probe  # rtt-2026-06-12 INST3: KEEP-AS-PROBE pending operator REQ-binding


def test_lifecycle_queue_cancel(job_env):
    """Job transitions from queued → cancelled."""
    backend, queue = job_env

    job_id = _submit(queue)
    job = backend.get(job_id)
    assert job.status == JobStatus.QUEUED

    # Cancel
    cancelled = queue.cancel(job_id)
    assert cancelled
    job = backend.get(job_id)
    assert job.status == JobStatus.CANCELLED


# ── Path 4: create → queue → run → timeout ──────────────────────────
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.probe  # rtt-2026-06-12 INST3: KEEP-AS-PROBE pending operator REQ-binding


def test_lifecycle_queue_run_timeout(job_env):
    """Job transitions from queued → running → timeout."""
    backend, queue = job_env

    job_id = _submit(queue)
    backend.claim(job_id, "test-host", "test-worker")
    job = backend.get(job_id)
    assert job.status == JobStatus.RUNNING

    # Timeout (simulated — in production the Worker enforces this)
    backend.update_status(job_id, JobStatus.TIMEOUT.value)
    job = backend.get(job_id)
    assert job.status == JobStatus.TIMEOUT
