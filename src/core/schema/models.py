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
# Description: Canonical schema-change models for db-mcp-server.
# Related requirements: SC-01, SC-02, W28A-274-L deliverables 1, 4, 5
# Related tests: UT1.12, ST1.6, IT1.7

"""Canonical schema-change models for db-mcp-server."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

from src.core.access_control.models import coerce_datetime, serialise_datetime, utcnow


def new_schema_change_id() -> str:
    """Return a stable schema-change identifier."""
    return f"schg_{uuid4().hex[:24]}"


@dataclass(slots=True)
class SchemaChangeOperation:
    """Normalised schema-change operation payload."""

    op_type: str
    namespace: str
    entity: str
    parameters: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "SchemaChangeOperation":
        raw = dict(payload or {})
        op_type = str(raw.pop("op_type", raw.pop("operation", ""))).strip()
        namespace = str(raw.pop("namespace", "")).strip()
        entity = str(raw.pop("entity", "")).strip()
        parameters = dict(raw.pop("parameters", {}))
        parameters.update(raw)
        return cls(op_type=op_type, namespace=namespace, entity=entity, parameters=parameters)

    def to_payload(self) -> dict[str, Any]:
        """Return the connector-ready representation for this operation."""
        payload = {
            "operation": self.op_type,
            "namespace": self.namespace,
            "entity": self.entity,
        }
        payload.update(self.parameters)
        return payload

    def to_dict(self) -> dict[str, Any]:
        """Return a serialisable view for API responses and persistence."""
        return {
            "op_type": self.op_type,
            "namespace": self.namespace,
            "entity": self.entity,
            "parameters": dict(self.parameters),
        }


@dataclass(slots=True)
class SchemaChangePlan:
    """Persisted dry-run plan for one or more schema changes."""

    plan_id: str = field(default_factory=new_schema_change_id)
    profile_id: str = ""
    source_type: str = ""
    operations: list[SchemaChangeOperation] = field(default_factory=list)
    dry_run_result: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    requires_approval: bool = True
    approved: bool = False
    created_at: datetime = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Return a serialisable view for persistence and responses."""
        return {
            "plan_id": self.plan_id,
            "profile_id": self.profile_id,
            "source_type": self.source_type,
            "operations": [item.to_dict() for item in self.operations],
            "dry_run_result": dict(self.dry_run_result),
            "warnings": list(self.warnings),
            "requires_approval": self.requires_approval,
            "approved": self.approved,
            "created_at": serialise_datetime(self.created_at),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "SchemaChangePlan":
        """Rebuild a plan from persisted state."""
        raw = dict(payload or {})
        operations = [SchemaChangeOperation.from_payload(item) for item in raw.get("operations", [])]
        return cls(
            plan_id=str(raw.get("plan_id") or new_schema_change_id()),
            profile_id=str(raw.get("profile_id", "")),
            source_type=str(raw.get("source_type", "")),
            operations=operations,
            dry_run_result=dict(raw.get("dry_run_result") or {}),
            warnings=[str(item) for item in raw.get("warnings", [])],
            requires_approval=bool(raw.get("requires_approval", True)),
            approved=bool(raw.get("approved", False)),
            created_at=coerce_datetime(raw.get("created_at")) or utcnow(),
        )


@dataclass(slots=True)
class SchemaChangeResult:
    """Execution result for an approved schema-change plan."""

    success: bool
    operations_applied: int
    audit_event_id: str
    index_refresh_triggered: bool
    results: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    applied_at: datetime = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Return a serialisable view for persistence and responses."""
        return {
            "success": self.success,
            "operations_applied": self.operations_applied,
            "audit_event_id": self.audit_event_id,
            "index_refresh_triggered": self.index_refresh_triggered,
            "results": [dict(item) for item in self.results],
            "warnings": list(self.warnings),
            "applied_at": serialise_datetime(self.applied_at),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "SchemaChangeResult":
        """Rebuild a result from persisted state."""
        raw = dict(payload or {})
        return cls(
            success=bool(raw.get("success", False)),
            operations_applied=int(raw.get("operations_applied", 0)),
            audit_event_id=str(raw.get("audit_event_id", "")),
            index_refresh_triggered=bool(raw.get("index_refresh_triggered", False)),
            results=[dict(item) for item in raw.get("results", [])],
            warnings=[str(item) for item in raw.get("warnings", [])],
            applied_at=coerce_datetime(raw.get("applied_at")) or utcnow(),
        )


@dataclass(slots=True)
class SchemaChangeRecord:
    """Persisted schema-change lifecycle record."""

    plan: SchemaChangePlan
    status: str = "planned"
    planned_by: str | None = None
    approved_by: str | None = None
    approved_at: datetime | None = None
    applied_by: str | None = None
    applied_at: datetime | None = None
    audit_event_id: str | None = None
    audit_trail: list[dict[str, Any]] = field(default_factory=list)
    result: SchemaChangeResult | None = None
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)

    @property
    def plan_id(self) -> str:
        """Return the stable plan identifier."""
        return self.plan.plan_id

    @property
    def profile_id(self) -> str:
        """Return the owning profile id."""
        return self.plan.profile_id

    def to_payload(self) -> dict[str, Any]:
        """Return a persistence-ready payload."""
        payload = asdict(self)
        payload["plan"] = self.plan.to_dict()
        payload["result"] = self.result.to_dict() if self.result is not None else None
        payload["approved_at"] = serialise_datetime(self.approved_at)
        payload["applied_at"] = serialise_datetime(self.applied_at)
        payload["created_at"] = serialise_datetime(self.created_at)
        payload["updated_at"] = serialise_datetime(self.updated_at)
        return payload

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "SchemaChangeRecord":
        """Rebuild a schema-change record from persisted state."""
        raw = dict(payload or {})
        result_payload = raw.get("result")
        return cls(
            plan=SchemaChangePlan.from_dict(dict(raw.get("plan") or {})),
            status=str(raw.get("status", "planned")),
            planned_by=raw.get("planned_by"),
            approved_by=raw.get("approved_by"),
            approved_at=coerce_datetime(raw.get("approved_at")),
            applied_by=raw.get("applied_by"),
            applied_at=coerce_datetime(raw.get("applied_at")),
            audit_event_id=raw.get("audit_event_id"),
            audit_trail=[dict(item) for item in raw.get("audit_trail", [])],
            result=SchemaChangeResult.from_dict(dict(result_payload)) if result_payload else None,
            created_at=coerce_datetime(raw.get("created_at")) or utcnow(),
            updated_at=coerce_datetime(raw.get("updated_at")) or utcnow(),
        )

    def to_view(self) -> dict[str, Any]:
        """Return the external API/MCP response view."""
        view = self.plan.to_dict()
        view.update(
            {
                "status": self.status,
                "planned_by": self.planned_by,
                "approved_by": self.approved_by,
                "approved_at": serialise_datetime(self.approved_at),
                "applied_by": self.applied_by,
                "applied_at": serialise_datetime(self.applied_at),
                "audit_event_id": self.audit_event_id,
                "audit_trail": [dict(item) for item in self.audit_trail],
                "result": self.result.to_dict() if self.result is not None else None,
                "created_at": serialise_datetime(self.created_at),
                "updated_at": serialise_datetime(self.updated_at),
            }
        )
        if self.plan.operations:
            first = self.plan.operations[0]
            view.setdefault("operation", first.op_type)
            view.setdefault("namespace", first.namespace)
            view.setdefault("entity", first.entity)
            view.setdefault("parameters", dict(first.parameters))
        view["dry_run"] = True
        return view
