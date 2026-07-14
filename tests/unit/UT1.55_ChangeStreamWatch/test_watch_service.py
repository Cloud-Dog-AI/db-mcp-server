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
# Description: UT1.55 — database change-watch adapter lifecycle / RBAC / durability.
# Related requirements: CSTREAM-DB-001, CSTREAM-DB-002
# Related tests: UT1.55

"""UT1.55 — WatchService adapter over the common change-stream foundation.

Uses a disposable SQLite engine (no live DB container — §5.9) to prove the
durable ``SqlJournal`` path: create/list/status/pause/resume/delete, RBAC/tenant
isolation, backpressure (max_inflight), cursor recovery, redaction, and journal
survival across a service-object restart.
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine

from cloud_dog_api_kit.change_stream.errors import (
    InvalidCriteria,
    RateLimited,
    WatchNotFound,
)
from src.core.change_stream import WatchService



@pytest.fixture()
def engine(tmp_path):
    # Disposable file-backed SQLite so the journal survives a WatchService restart
    # within the test (shared file, fresh service object).
    eng = create_engine(f"sqlite:///{tmp_path/'watch-journal.db'}", future=True)
    yield eng
    eng.dispose()


@pytest.fixture()
def service(engine):
    return WatchService(engine=engine)


def _create(service, *, tenant="t1", profile="p1", **kw):
    return service.create_watch(profile_id=profile, tenant_id=tenant, actor="alice", **kw)


@pytest.mark.req("CSTREAM-DB-001")
@pytest.mark.unit
@pytest.mark.UT
@pytest.mark.internal
def test_lifecycle_create_list_status_pause_resume_delete(service) -> None:
    watch = _create(service)
    wid = watch["watch_id"]
    assert watch["status"]["state"] == "live"
    assert [w["watch_id"] for w in service.list_watches(tenant_id="t1")] == [wid]
    assert service.pause(wid, tenant_id="t1")["state"] == "paused"
    assert service.resume(wid, tenant_id="t1")["state"] == "live"
    assert service.delete(wid, tenant_id="t1") == {"watch_id": wid, "deleted": True}
    assert service.list_watches(tenant_id="t1") == []


@pytest.mark.req("CSTREAM-DB-001")
@pytest.mark.unit
@pytest.mark.UT
@pytest.mark.internal
def test_tenant_isolation_is_hard_not_found(service) -> None:
    wid = _create(service, tenant="t1")["watch_id"]
    # a different tenant cannot see or act on the watch — existence not leaked.
    assert service.list_watches(tenant_id="t2") == []
    with pytest.raises(WatchNotFound):
        service.get_status(wid, tenant_id="t2")
    with pytest.raises(WatchNotFound):
        service.delete(wid, tenant_id="t2")


@pytest.mark.req("CSTREAM-DB-002")
@pytest.mark.unit
@pytest.mark.UT
@pytest.mark.internal
def test_invalid_criteria_rejected_at_create(service) -> None:
    with pytest.raises(InvalidCriteria):
        _create(service, criteria={"unsupported": 1})


@pytest.mark.req("CSTREAM-DB-001")
@pytest.mark.unit
@pytest.mark.UT
@pytest.mark.internal
def test_server_mediated_capture_and_batch_and_ack(service) -> None:
    wid = _create(service, criteria={"namespace": "public", "entity": "orders", "action": ["created"]})["watch_id"]
    emitted = service.observe_change(
        tenant_id="t1",
        profile_id="p1",
        source_type="postgresql",
        namespace="public",
        entity="orders",
        action="created",
        object_ref="42",
        values={"status": "new", "password": "hunter2"},
        actor="alice",
    )
    assert emitted == [wid]
    # a non-matching change (wrong entity) is not delivered.
    assert service.observe_change(
        tenant_id="t1", profile_id="p1", source_type="postgresql",
        namespace="public", entity="users", action="created", object_ref="1",
    ) == []

    batch = service.get_batch(wid, tenant_id="t1")
    assert len(batch["events"]) == 1
    event = batch["events"][0]
    assert event["action"] == "created"
    assert event["object_ref"] == "42"
    assert event["metadata"]["source_type"] == "postgresql"
    assert event["criteria_match"]["entity"] == "orders"
    # redaction: a secret-looking value never rests in cleartext (CSTREAM-004/010).
    assert event["metadata"]["values"]["password"] == "<redacted>"
    assert event["metadata"]["values"]["status"] == "new"

    status = service.ack(wid, tenant_id="t1", ack_cursor=batch["next_cursor"])
    assert status["inflight"] == 0


@pytest.mark.req("CSTREAM-DB-001")
@pytest.mark.unit
@pytest.mark.UT
@pytest.mark.internal
def test_paused_watch_receives_no_new_events(service) -> None:
    wid = _create(service)["watch_id"]
    service.pause(wid, tenant_id="t1")
    assert service.observe_change(
        tenant_id="t1", profile_id="p1", source_type="mongodb",
        namespace="db", entity="c", action="created", object_ref="x",
    ) == []


@pytest.mark.req("CSTREAM-DB-001")
@pytest.mark.unit
@pytest.mark.UT
@pytest.mark.internal
def test_backpressure_blocks_unacked_batches(service) -> None:
    wid = _create(service, max_inflight=1)["watch_id"]
    for i in range(3):
        service.observe_change(
            tenant_id="t1", profile_id="p1", source_type="postgresql",
            namespace="public", entity="orders", action="created", object_ref=str(i),
        )
    service.get_batch(wid, tenant_id="t1")  # 1 in-flight
    with pytest.raises(RateLimited):
        service.get_batch(wid, tenant_id="t1")


@pytest.mark.req("CSTREAM-DB-001")
@pytest.mark.unit
@pytest.mark.UT
@pytest.mark.internal
def test_recover_returns_resumable_cursor(service) -> None:
    wid = _create(service)["watch_id"]
    service.observe_change(
        tenant_id="t1", profile_id="p1", source_type="postgresql",
        namespace="public", entity="orders", action="created", object_ref="1",
    )
    out = service.recover(wid, tenant_id="t1")
    assert out["watch_id"] == wid
    assert isinstance(out["resume_cursor"], str) and out["resume_cursor"]


@pytest.mark.req("CSTREAM-DB-001")
@pytest.mark.unit
@pytest.mark.UT
@pytest.mark.internal
def test_test_event_injects_synthetic_event(service) -> None:
    wid = _create(service)["watch_id"]
    out = service.test_event(wid, tenant_id="t1", action="created", object_ref="probe")
    assert out["emitted_seq"] >= 1
    batch = service.get_batch(wid, tenant_id="t1")
    assert any(e["object_ref"] == "probe" for e in batch["events"])


@pytest.mark.req("CSTREAM-DB-001")
@pytest.mark.unit
@pytest.mark.UT
@pytest.mark.internal
def test_durable_journal_survives_service_restart(engine) -> None:
    # first service object writes; a fresh service object over the SAME engine
    # still reads the journalled backlog (CSTREAM-007 durability).
    first = WatchService(engine=engine)
    wid = first.create_watch(profile_id="p1", tenant_id="t1", actor="alice")["watch_id"]
    first.observe_change(
        tenant_id="t1", profile_id="p1", source_type="postgresql",
        namespace="public", entity="orders", action="created", object_ref="99",
    )

    second = WatchService(engine=engine)
    # the coordinator's in-memory watch registry is per-process, so re-register
    # the watch with the same id, then read the durable journal backlog.
    second.create_watch(profile_id="p1", tenant_id="t1", actor="alice", watch_id=wid)
    batch = second.get_batch(wid, tenant_id="t1")
    assert [e["object_ref"] for e in batch["events"]] == ["99"]


@pytest.mark.req("CSTREAM-DB-003")
@pytest.mark.unit
@pytest.mark.UT
@pytest.mark.internal
def test_native_cdc_support_is_honest(service) -> None:
    support = service.native_cdc_support()
    assert set(support) >= {"postgresql", "mariadb", "mongodb", "couchdb", "opensearch", "elasticsearch", "cassandra"}
    for row in support.values():
        assert row["server_mediated"] is True
        # honest: native out-of-band CDC is NOT available via cloud_dog_db today.
        assert row["native_available_via_cloud_dog_db"] is False


@pytest.mark.req("CSTREAM-DB-001")
@pytest.mark.unit
@pytest.mark.UT
@pytest.mark.internal
def test_in_memory_fallback_without_engine() -> None:
    # No engine -> bounded in-memory journal; the adapter still functions.
    svc = WatchService(engine=None)
    wid = svc.create_watch(profile_id="p1", tenant_id="t1", actor="alice")["watch_id"]
    svc.observe_change(
        tenant_id="t1", profile_id="p1", source_type="mongodb",
        namespace="db", entity="c", action="created", object_ref="m1",
    )
    assert len(svc.get_batch(wid, tenant_id="t1")["events"]) == 1
