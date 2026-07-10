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
# Description: UT1.55 — server-mediated change capture through the content tools.
# Related requirements: CSTREAM-DB-001
# Related tests: UT1.55

"""UT1.55 — real insert/update/delete through ``data.*`` tools emit change events.

Proves the server-mediated capture path (PS-102 §6): a create/update/delete
performed through the content MCP tools produces a matching :class:`ChangeEvent`
in a live watch, with per-db-type coverage exercised via the ``source_type`` on
the profile — no live DB container required (the connector is a fake mirroring
the real connector contract, so the capture wiring is what is under test).
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.core.change_stream import WatchService
from src.core.filters import MongoDBFilterTranslator, RelationalFilterTranslator
from src.servers.mcp.content_tools import build_content_tool_registry

pytestmark = [pytest.mark.unit, pytest.mark.UT, pytest.mark.mcp, pytest.mark.asyncio]


class _FakeConnector:
    def create(self, namespace, entity, document):
        return {"inserted_id": document.get("id", "row-1"), "document": dict(document)}

    def update(self, namespace, entity, filter, update):
        return {"matched_count": 2, "modified_count": 2}

    def delete(self, namespace, entity, filter):
        return {"deleted_count": 3}


class _FakeConnectors:
    def __init__(self, profile) -> None:
        self.connector = _FakeConnector()
        self._profile = profile
        translator = (
            MongoDBFilterTranslator()
            if profile["source_type"] in {"mongodb", "couchdb"}
            else RelationalFilterTranslator()
        )
        self._translator = translator

    def execute(self, _request, *, callback, **_kwargs):
        session = SimpleNamespace(profile=self._profile, connector=self.connector, translator=self._translator)
        return callback(session)

    def ensure_entity_allowed(self, *_a, **_k):
        return None

    def mask_record(self, _pid, record):
        return dict(record)

    def mask_records(self, _pid, records):
        return [dict(r) for r in records]


def _runtime(source_type: str) -> SimpleNamespace:
    profile = {"profile_id": "p1", "source_type": source_type}
    return SimpleNamespace(
        watch_service=WatchService(engine=None),
        connectors=_FakeConnectors(profile),
    )


def _request(tenant="t1", user="alice"):
    state = SimpleNamespace(tenant_id=tenant, username=user, user=user, correlation_id="corr-1")
    return SimpleNamespace(state=state)


@pytest.mark.parametrize("source_type", ["postgresql", "mariadb", "mongodb", "couchdb", "opensearch", "elasticsearch", "cassandra"])
@pytest.mark.req("CSTREAM-DB-001")
async def test_insert_update_delete_emit_events_per_source_type(source_type) -> None:
    runtime = _runtime(source_type)
    tools = build_content_tool_registry(runtime)
    ws = runtime.watch_service
    wid = ws.create_watch(profile_id="p1", tenant_id="t1", actor="alice")["watch_id"]

    await tools["data.create"].handler(
        {"profile_id": "p1", "namespace": "public", "entity": "orders", "document": {"id": "row-1", "status": "new"}},
        _request(),
    )
    await tools["data.update"].handler(
        {"profile_id": "p1", "namespace": "public", "entity": "orders", "filter": {"status": "new"}, "update": {"status": "shipped"}},
        _request(),
    )
    await tools["data.delete"].handler(
        {"profile_id": "p1", "namespace": "public", "entity": "orders", "filter": {"status": "shipped"}},
        _request(),
    )

    events = ws.get_batch(wid, tenant_id="t1", max_batch=100)["events"]
    actions = [e["action"] for e in events]
    assert actions == ["created", "updated", "deleted"]
    # per-source-type provenance is carried truthfully on every event.
    assert all(e["metadata"]["source_type"] == source_type for e in events)
    assert all(e["metadata"]["capture"] == "server_mediated" for e in events)
    # bulk update/delete carry the affected row count (no per-row snapshot).
    updated = next(e for e in events if e["action"] == "updated")
    assert updated["metadata"]["row_count"] == 2
    deleted = next(e for e in events if e["action"] == "deleted")
    assert deleted["metadata"]["row_count"] == 3


@pytest.mark.req("CSTREAM-DB-001")
async def test_capture_is_noop_without_matching_watch() -> None:
    runtime = _runtime("postgresql")
    tools = build_content_tool_registry(runtime)
    ws = runtime.watch_service
    # a watch scoped to a DIFFERENT profile must not receive the change.
    other = ws.create_watch(profile_id="other", tenant_id="t1", actor="alice")["watch_id"]
    out = await tools["data.create"].handler(
        {"profile_id": "p1", "namespace": "public", "entity": "orders", "document": {"id": "row-1"}},
        _request(),
    )
    assert out["inserted_id"] == "row-1"  # the mutation still returns normally
    assert ws.get_batch(other, tenant_id="t1")["events"] == []


@pytest.mark.req("CSTREAM-DB-001")
async def test_capture_never_breaks_a_successful_mutation() -> None:
    # A broken watch service must not fail the data mutation (capture is best-effort).
    class _Boom:
        def observe_change(self, **_kw):
            raise RuntimeError("watch backend down")

    runtime = SimpleNamespace(watch_service=_Boom(), connectors=_FakeConnectors({"profile_id": "p1", "source_type": "postgresql"}))
    tools = build_content_tool_registry(runtime)
    out = await tools["data.create"].handler(
        {"profile_id": "p1", "namespace": "public", "entity": "orders", "document": {"id": "row-1"}},
        _request(),
    )
    assert out["inserted_id"] == "row-1"
