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
# Description: Unit tests for schema-change planning, apply, and history orchestration.
# Related requirements: SC-01, SC-02, W28A-274-L deliverables 1, 2, 4, 5
# Tests: SC-03, SC-04
# Related tests: UT1.12

from __future__ import annotations

from dataclasses import dataclass

import pytest
from sqlalchemy import create_engine

from cloud_dog_api_kit.errors import ValidationError

from src.core.schema.service import SchemaChangeService

pytestmark = pytest.mark.unit


@dataclass
class FakePrincipal:
    user_id: str = "tester"
    roles: list[str] = None

    def __post_init__(self) -> None:
        if self.roles is None:
            self.roles = ["admin"]


class FakeAccessControl:
    def require_request_permission(self, *_args, **_kwargs):
        return FakePrincipal()


class FakeConnector:
    def __init__(self) -> None:
        self.indexes = [{"name": "_id_", "keys": [["_id", 1]], "unique": True, "sparse": False}]
        self.entities = [{"name": "orders", "type": "collection"}]

    def schema_change_plan(self, operation):
        op_type = operation["operation"]
        entity = operation["entity"]
        namespace = operation["namespace"]
        if op_type == "create_index":
            return {
                "operation": op_type,
                "namespace": namespace,
                "entity": entity,
                "parameters": {"name": operation.get("name", "orders_status_idx")},
                "dry_run": True,
                "requires_approval": True,
                "before_state": {"indexes": list(self.indexes)},
                "after_state": {"indexes": list(self.indexes) + [{"name": operation.get("name", "orders_status_idx")}]},
                "warnings": [],
            }
        raise ValueError(op_type)

    def schema_change_apply(self, operation):
        name = operation.get("name", "orders_status_idx")
        self.indexes.append({"name": name, "keys": [["status", 1]], "unique": False, "sparse": False})
        return {"applied": True, "success": True, "operation": "create_index", "index_name": name}

    def list_indexes(self, _namespace, _entity):
        return list(self.indexes)

    def describe_entity(self, namespace, entity):
        return {"namespace": namespace, "entity": entity}

    def list_entities(self, _namespace):
        return list(self.entities)

    def close(self):
        return None


class FakeConnectors:
    def __init__(self) -> None:
        self.connector = FakeConnector()
        self.profile = {"profile_id": "profile-1", "source_type": "mongodb", "namespaces": ["db1"], "entities": ["db1.orders"]}

    def for_profile(self, _profile_id):
        class Session:
            profile = {"profile_id": "profile-1", "source_type": "mongodb", "namespaces": ["db1"], "entities": ["db1.orders"]}
            connector = FakeConnector()
        return Session()

    def ensure_namespace_allowed(self, profile, namespace):
        assert namespace in profile["namespaces"]

    def ensure_entity_allowed(self, profile, namespace, entity):
        assert f"{namespace}.{entity}" in profile["entities"]


class FakeSearch:
    def __init__(self) -> None:
        self.calls = []

    def sync_entity(self, *, profile_id, namespace, entity, principal):
        self.calls.append((profile_id, namespace, entity, principal.user_id))
        return {"job_status": "succeeded"}

    def sync_profile(self, *, profile_id, principal):
        self.calls.append((profile_id, "*", "*", principal.user_id))
        return {"job_status": "succeeded"}


class FakeAuditLogger:
    def __init__(self) -> None:
        self.events = []

    def log_tool_call(self, **kwargs):
        self.events.append(("tool", kwargs))

    def log_privileged(self, **kwargs):
        self.events.append(("privileged", kwargs))


class FakeRuntime:
    def __init__(self) -> None:
        self.metadata_engine = create_engine("sqlite:///:memory:")
        self.access_control = FakeAccessControl()
        self.connectors = FakeConnectors()
        self.search = FakeSearch()
        self.audit_logger = FakeAuditLogger()
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.probe  # rtt-2026-06-12 INST3: KEEP-AS-PROBE pending operator REQ-binding


def test_schema_change_service_requires_approval_and_tracks_history() -> None:
    runtime = FakeRuntime()
    service = SchemaChangeService(runtime)

    plan = service.plan_change(
        object(),
        profile_id="profile-1",
        payload={
            "operation": {
                "operation": "create_index",
                "namespace": "db1",
                "entity": "orders",
                "name": "orders_status_idx",
                "keys": [{"field": "status", "direction": "asc"}],
            }
        },
    )
    assert plan["requires_approval"] is True
    assert plan["status"] == "planned"

    history = service.history(object(), profile_id="profile-1")
    assert history["items"][0]["plan_id"] == plan["plan_id"]
    assert history["items"][0]["audit_trail"][0]["action"] == "schema.change.plan"
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.probe  # rtt-2026-06-12 INST3: KEEP-AS-PROBE pending operator REQ-binding


def test_schema_change_service_applies_plan_and_refreshes_index() -> None:
    runtime = FakeRuntime()
    service = SchemaChangeService(runtime)
    plan = service.plan_change(
        object(),
        profile_id="profile-1",
        payload={
            "operation": {
                "operation": "create_index",
                "namespace": "db1",
                "entity": "orders",
                "name": "orders_status_idx",
                "keys": [{"field": "status", "direction": "asc"}],
            }
        },
    )

    with pytest.raises(ValidationError):
        service.apply_change(object(), profile_id="profile-1", payload={"plan": plan})

    applied = service.apply_change(
        object(),
        profile_id="profile-1",
        payload={"plan": plan, "approved": True},
    )
    assert applied["applied"] is True
    assert applied["operations_applied"] == 1
    assert applied["index_refresh_triggered"] is True
    assert runtime.search.calls == [("profile-1", "db1", "orders", "tester")]

    history = service.history(object(), profile_id="profile-1")
    assert history["items"][0]["status"] == "applied"
    assert history["items"][0]["audit_event_id"].endswith(":apply-state")
