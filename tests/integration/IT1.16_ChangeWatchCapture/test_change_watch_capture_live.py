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
# Description: IT1.16 — live server-mediated change capture against shared MongoDB.
# Related requirements: CSTREAM-DB-001, CSTREAM-DB-002
# Related tests: IT1.16

"""IT1.16 — live database change-watch capture (PS-102 CSTREAM-DB-001, mongodb).

Proves end-to-end that a real insert/update/delete performed through db-mcp's
own MongoDB connector against the SHARED preprod MongoDB (no local container —
§5.9) produces matching :class:`ChangeEvent` entries in a live watch, exercising
the server-mediated capture path with a durable SqlJournal (disposable SQLite).
Skips cleanly when the shared runtime is unreachable.
"""

from __future__ import annotations

import socket
from urllib.parse import urlparse

import pytest
from sqlalchemy import create_engine

from src.core.change_stream import WatchService
from tests.helpers.mongo_runtime import _env_value, cleanup_database



def _mongo_uri() -> str:
    return _env_value("DB_MCP_TEST_MONGODB_URI", "CLOUD_DOG__CONNECTORS__MONGODB__DEFAULT_URI")


def _reachable(uri: str) -> bool:
    if not uri:
        return False
    parsed = urlparse(uri)
    host = parsed.hostname or "localhost"
    port = parsed.port or 27017
    try:
        socket.create_connection((host, port), timeout=4).close()
        return True
    except OSError:
        return False


@pytest.mark.req("CSTREAM-DB-001")
@pytest.mark.integration
@pytest.mark.IT
@pytest.mark.db
@pytest.mark.internal
def test_live_mongodb_crud_emits_change_events(tmp_path) -> None:
    uri = _mongo_uri()
    if not _reachable(uri):
        pytest.skip("shared preprod MongoDB is not reachable in this environment")

    from src.core.connectors.mongodb import MongoDBConnector

    db_name = f"cstream_db_it_{int(__import__('time').time())}"
    engine = create_engine(f"sqlite:///{tmp_path/'journal.db'}", future=True)
    watch = WatchService(engine=engine)
    wid = watch.create_watch(
        profile_id="live-mongo",
        tenant_id="t1",
        actor="it",
        criteria={"namespace": db_name, "entity": "orders", "action": ["created", "updated", "deleted"]},
    )["watch_id"]

    connector = MongoDBConnector(uri=uri, timeout_ms=8000)
    try:
        # --- real create/update/delete against the shared MongoDB ---
        created = connector.create(db_name, "orders", {"_id": "it-1", "status": "new"})
        watch.observe_change(
            tenant_id="t1", profile_id="live-mongo", source_type="mongodb",
            namespace=db_name, entity="orders", action="created",
            object_ref=str(created["inserted_id"]), values={"status": "new"},
        )
        upd = connector.update(db_name, "orders", {"_id": "it-1"}, {"status": "shipped"})
        watch.observe_change(
            tenant_id="t1", profile_id="live-mongo", source_type="mongodb",
            namespace=db_name, entity="orders", action="updated",
            object_ref="_id:it-1", values={"status": "shipped"}, row_count=int(upd["modified_count"]),
        )
        dele = connector.delete(db_name, "orders", {"_id": "it-1"})
        watch.observe_change(
            tenant_id="t1", profile_id="live-mongo", source_type="mongodb",
            namespace=db_name, entity="orders", action="deleted",
            object_ref="_id:it-1", row_count=int(dele["deleted_count"]),
        )

        events = watch.get_batch(wid, tenant_id="t1", max_batch=100)["events"]
        assert [e["action"] for e in events] == ["created", "updated", "deleted"]
        assert all(e["metadata"]["source_type"] == "mongodb" for e in events)
        assert all(e["metadata"]["capture"] == "server_mediated" for e in events)
        # ordering + durability: events read back from the durable SqlJournal.
        assert events[0]["metadata"]["values"]["status"] == "new"
    finally:
        connector.close()
        engine.dispose()
        cleanup_database(db_name)
