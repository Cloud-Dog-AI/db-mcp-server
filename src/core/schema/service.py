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
# Description: Schema-change orchestration service with history, audit, and index refresh.
# Related requirements: SC-01, SC-02, W28A-274-L deliverables 1, 2, 4, 5
# Covers: SC-03, SC-04
# Related tests: UT1.12, ST1.6, IT1.7

"""Schema-change orchestration service."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterable

from fastapi import Request

from cloud_dog_api_kit.errors import InternalError, NotFoundError, ValidationError
from cloud_dog_logging import Actor, Target
from cloud_dog_logging.correlation import get_correlation_id, set_correlation_id

from src.core.access_control.models import serialise_datetime, utcnow
from src.core.schema.models import (
    SchemaChangeOperation,
    SchemaChangePlan,
    SchemaChangeRecord,
    SchemaChangeResult,
)
from src.core.schema.repository import SchemaChangeRepository

_DESTRUCTIVE_OPERATIONS = {"drop_entity", "drop_index", "alter_field"}
_SUPPORTED_OPERATIONS = {
    "create_entity",
    "drop_entity",
    "add_field",
    "alter_field",
    "create_index",
    "drop_index",
    "create_alias",
}


class SchemaChangeService:
    """Validate, plan, apply, audit, and list schema changes."""

    def __init__(self, runtime) -> None:
        self._runtime = runtime
        self._repository = SchemaChangeRepository(runtime.metadata_engine)

    def plan_change(self, request: Request, *, profile_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        principal = self._runtime.access_control.require_request_permission(
            request,
            permission="schema.change",
            profile_id=profile_id,
            audit_resource_type="profile",
            audit_resource_id=profile_id,
        )
        session = self._runtime.connectors.for_profile(profile_id)
        try:
            operations = self._parse_operations(payload)
            connector_plans: list[dict[str, Any]] = []
            warnings: list[str] = []
            requires_approval = False
            for operation in operations:
                self._validate_operation_shape(operation)
                self._runtime.connectors.ensure_namespace_allowed(session.profile, operation.namespace)
                self._runtime.connectors.ensure_entity_allowed(session.profile, operation.namespace, operation.entity)
                connector_plan = session.connector.schema_change_plan(operation.to_payload())
                connector_plans.append(dict(connector_plan))
                warnings.extend([str(item) for item in connector_plan.get("warnings", [])])
                requires_approval = requires_approval or bool(connector_plan.get("requires_approval", False))
                requires_approval = requires_approval or operation.op_type in _DESTRUCTIVE_OPERATIONS

            plan = SchemaChangePlan(
                profile_id=profile_id,
                source_type=str(session.profile.get("source_type", "")),
                operations=operations,
                dry_run_result={
                    "operations": connector_plans,
                    "summary": {
                        "operation_count": len(connector_plans),
                        "destructive_operations": [item.op_type for item in operations if item.op_type in _DESTRUCTIVE_OPERATIONS],
                    },
                },
                warnings=sorted(set(warnings)),
                requires_approval=True if connector_plans else requires_approval,
            )
            record = SchemaChangeRecord(
                plan=plan,
                status="planned",
                planned_by=principal.user_id,
            )
            plan_event_id = f"{plan.plan_id}:plan"
            record.audit_trail.append(
                {
                    "audit_event_id": plan_event_id,
                    "event_type": "tool.call",
                    "action": "schema.change.plan",
                    "outcome": "success",
                    "timestamp": serialise_datetime(utcnow()),
                    "approval_status": "pending" if plan.requires_approval else "not-required",
                }
            )
            self._emit_tool_audit(
                principal,
                audit_event_id=plan_event_id,
                tool_name="schema.change.plan",
                outcome="success",
                profile_id=profile_id,
                target_id=plan.plan_id,
                operation_types=[item.op_type for item in operations],
                requires_approval=plan.requires_approval,
            )
            self._repository.upsert(record)
            return record.to_view()
        finally:
            self._close_session(session)

    def apply_change(self, request: Request, *, profile_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        principal = self._runtime.access_control.require_request_permission(
            request,
            permission="schema.change",
            profile_id=profile_id,
            audit_resource_type="profile",
            audit_resource_id=profile_id,
        )
        record = self._resolve_record(profile_id, payload)
        approved = bool(payload.get("approved") or payload.get("approval", {}).get("approved") or record.plan.approved)
        if record.plan.requires_approval and not approved:
            raise ValidationError(message="Schema change approval is required before apply")
        if approved:
            record.plan.approved = True
            record.approved_by = principal.user_id
            record.approved_at = record.approved_at or utcnow()

        session = self._runtime.connectors.for_profile(record.profile_id)
        operation_results: list[dict[str, Any]] = []
        warnings = list(record.plan.warnings)
        try:
            for operation in record.plan.operations:
                self._runtime.connectors.ensure_namespace_allowed(session.profile, operation.namespace)
                self._runtime.connectors.ensure_entity_allowed(session.profile, operation.namespace, operation.entity)
                before_plan = session.connector.schema_change_plan(operation.to_payload())
                applied = session.connector.schema_change_apply(operation.to_payload())
                after_state = self._capture_after_state(session.connector, operation)
                operation_results.append(
                    {
                        "operation": operation.op_type,
                        "namespace": operation.namespace,
                        "entity": operation.entity,
                        "before_state": before_plan.get("before_state"),
                        "after_state": after_state,
                        "result": dict(applied),
                    }
                )
                warnings.extend([str(item) for item in applied.get("warnings", [])])

            refresh_result = self._refresh_indexes(record, principal)
            apply_event_id = f"{record.plan_id}:apply"
            state_event_id = f"{record.plan_id}:apply-state"
            self._emit_tool_audit(
                principal,
                audit_event_id=apply_event_id,
                tool_name="schema.change.apply",
                outcome="success",
                profile_id=record.profile_id,
                target_id=record.plan_id,
                operation_types=[item.op_type for item in record.plan.operations],
                approved=record.plan.approved,
            )
            self._emit_state_audit(
                principal,
                audit_event_id=state_event_id,
                record=record,
                outcome="success",
                operation_results=operation_results,
            )
            result = SchemaChangeResult(
                success=True,
                operations_applied=len(operation_results),
                audit_event_id=state_event_id,
                index_refresh_triggered=bool(refresh_result.get("triggered", False)),
                results=operation_results,
                warnings=sorted(set(warnings)),
            )
            record.status = "applied"
            record.applied_by = principal.user_id
            record.applied_at = result.applied_at
            record.audit_event_id = result.audit_event_id
            record.result = result
            record.updated_at = utcnow()
            record.audit_trail.extend(
                [
                    {
                        "audit_event_id": apply_event_id,
                        "event_type": "tool.call",
                        "action": "schema.change.apply",
                        "outcome": "success",
                        "timestamp": serialise_datetime(result.applied_at),
                        "approval_status": "approved" if record.plan.approved else "not-required",
                    },
                    {
                        "audit_event_id": state_event_id,
                        "event_type": "admin.schema.change",
                        "action": "schema.change",
                        "outcome": "success",
                        "timestamp": serialise_datetime(result.applied_at),
                        "approval_status": "approved" if record.plan.approved else "not-required",
                    },
                ]
            )
            self._repository.upsert(record)
            response = result.to_dict()
            response.update({"applied": True, "plan_id": record.plan_id, "status": record.status})
            if len(record.plan.operations) == 1:
                first_result = operation_results[0]["result"]
                response.setdefault("operation", record.plan.operations[0].op_type)
                response.update({key: value for key, value in first_result.items() if key not in response})
            return response
        except Exception as exc:
            apply_event_id = f"{record.plan_id}:apply"
            state_event_id = f"{record.plan_id}:apply-state"
            self._emit_tool_audit(
                principal,
                audit_event_id=apply_event_id,
                tool_name="schema.change.apply",
                outcome="failure",
                profile_id=record.profile_id,
                target_id=record.plan_id,
                error=str(exc),
            )
            self._emit_state_audit(
                principal,
                audit_event_id=state_event_id,
                record=record,
                outcome="failure",
                operation_results=operation_results,
                error=str(exc),
            )
            record.status = "failed"
            record.audit_event_id = state_event_id
            record.applied_by = principal.user_id
            record.applied_at = utcnow()
            record.updated_at = record.applied_at
            record.audit_trail.extend(
                [
                    {
                        "audit_event_id": apply_event_id,
                        "event_type": "tool.call",
                        "action": "schema.change.apply",
                        "outcome": "failure",
                        "timestamp": serialise_datetime(record.applied_at),
                        "approval_status": "approved" if record.plan.approved else "not-required",
                        "error": str(exc),
                    },
                    {
                        "audit_event_id": state_event_id,
                        "event_type": "admin.schema.change",
                        "action": "schema.change",
                        "outcome": "failure",
                        "timestamp": serialise_datetime(record.applied_at),
                        "approval_status": "approved" if record.plan.approved else "not-required",
                        "error": str(exc),
                    },
                ]
            )
            record.result = SchemaChangeResult(
                success=False,
                operations_applied=len(operation_results),
                audit_event_id=state_event_id,
                index_refresh_triggered=False,
                results=operation_results,
                warnings=sorted(set(warnings + [str(exc)])),
                applied_at=record.applied_at,
            )
            self._repository.upsert(record)
            if isinstance(exc, (ValidationError, NotFoundError, InternalError)):
                raise
            raise InternalError(message=f"Schema change apply failed: {exc}") from exc
        finally:
            self._close_session(session)

    def history(self, request: Request, *, profile_id: str | None = None, limit: int = 20, status: str | None = None) -> dict[str, Any]:
        permission = "schema.read" if profile_id else "audit.read"
        self._runtime.access_control.require_request_permission(
            request,
            permission=permission,
            profile_id=profile_id,
            audit_resource_type="schema_change",
            audit_resource_id=profile_id or "history",
        )
        items = [record.to_view() for record in self._repository.list(profile_id=profile_id, status=status, limit=limit)]
        return {"items": items}

    def _parse_operations(self, payload: dict[str, Any]) -> list[SchemaChangeOperation]:
        operations_payload = payload.get("operations")
        if operations_payload:
            return [SchemaChangeOperation.from_payload(dict(item)) for item in operations_payload]
        if payload.get("operation"):
            return [SchemaChangeOperation.from_payload(dict(payload.get("operation") or {}))]
        if payload.get("plan"):
            return [SchemaChangeOperation.from_payload(dict(item)) for item in payload["plan"].get("operations", [])]
        return [SchemaChangeOperation.from_payload(dict(payload))]

    @staticmethod
    def _validate_operation_shape(operation: SchemaChangeOperation) -> None:
        if operation.op_type not in _SUPPORTED_OPERATIONS:
            raise ValidationError(message=f"Unsupported schema change operation: {operation.op_type}")
        if not operation.namespace:
            raise ValidationError(message="Schema change namespace is required")
        if not operation.entity:
            raise ValidationError(message="Schema change entity is required")

    def _resolve_record(self, profile_id: str, payload: dict[str, Any]) -> SchemaChangeRecord:
        plan_payload = dict(payload.get("plan") or payload)
        plan_id = str(plan_payload.get("plan_id") or "").strip()
        if plan_id:
            record = self._repository.get(plan_id)
            if record is None:
                raise NotFoundError(message=f"Schema change plan not found: {plan_id}")
            if record.profile_id != profile_id:
                raise ValidationError(message="Schema change plan does not belong to the requested profile")
            return record

        operations = [SchemaChangeOperation.from_payload(dict(item)) for item in plan_payload.get("operations", [])]
        if not operations:
            operation = SchemaChangeOperation.from_payload(plan_payload)
            operations = [operation]
        dry_run_result = dict(plan_payload.get("dry_run_result") or {})
        plan = SchemaChangePlan(
            profile_id=profile_id,
            source_type=str(plan_payload.get("source_type", "mongodb")),
            operations=operations,
            dry_run_result=dry_run_result,
            warnings=[str(item) for item in plan_payload.get("warnings", [])],
            requires_approval=bool(plan_payload.get("requires_approval", True)),
            approved=bool(plan_payload.get("approved", False)),
        )
        return SchemaChangeRecord(plan=plan, status="planned")

    def _refresh_indexes(self, record: SchemaChangeRecord, principal: Any) -> dict[str, Any]:
        triggered = False
        for operation in record.plan.operations:
            if operation.op_type == "drop_entity":
                self._runtime.search.sync_profile(profile_id=record.profile_id, principal=principal)
            else:
                self._runtime.search.sync_entity(
                    profile_id=record.profile_id,
                    namespace=operation.namespace,
                    entity=operation.entity,
                    principal=principal,
                )
            triggered = True
        return {"triggered": triggered}

    def _capture_after_state(self, connector: Any, operation: SchemaChangeOperation) -> dict[str, Any]:
        namespace = operation.namespace
        entity = operation.entity
        if operation.op_type in {"create_index", "drop_index"}:
            return {"indexes": connector.list_indexes(namespace, entity)}
        if operation.op_type == "create_entity":
            entities = connector.list_entities(namespace)
            return {
                "entity_exists": any(str(item.get("name")) == entity for item in entities),
                "entities": entities,
            }
        if operation.op_type == "drop_entity":
            entities = connector.list_entities(namespace)
            return {
                "entity_exists": any(str(item.get("name")) == entity for item in entities),
                "entities": entities,
            }
        return {"entity": connector.describe_entity(namespace, entity)}

    def _emit_tool_audit(
        self,
        principal: Any,
        *,
        audit_event_id: str,
        tool_name: str,
        outcome: str,
        profile_id: str,
        target_id: str,
        **details: Any,
    ) -> None:
        with self._correlation(audit_event_id):
            self._runtime.audit_logger.log_tool_call(
                actor=Actor(type="user", id=principal.user_id, roles=principal.roles),
                tool=tool_name,
                params={"profile_id": profile_id, "target": target_id},
                outcome=outcome,
                duration_ms=0,
                target=Target(type="schema", id=target_id or profile_id),
                **details,
            )

    def _emit_state_audit(
        self,
        principal: Any,
        *,
        audit_event_id: str,
        record: SchemaChangeRecord,
        outcome: str,
        operation_results: Iterable[dict[str, Any]],
        error: str | None = None,
    ) -> None:
        prior_value = [dict(item.get("before_state") or {}) for item in operation_results]
        new_value = [dict(item.get("after_state") or {}) for item in operation_results]
        details: dict[str, Any] = {
            "plan_id": record.plan_id,
            "profile_id": record.profile_id,
            "approval_status": "approved" if record.plan.approved else "not-required",
            "operations": [item.to_dict() for item in record.plan.operations],
        }
        if error:
            details["error"] = error
        with self._correlation(audit_event_id):
            self._runtime.audit_logger.log_privileged(
                actor=Actor(type="user", id=principal.user_id, roles=principal.roles),
                action="schema.change",
                target=Target(type="schema_change", id=record.plan_id),
                outcome=outcome,
                command_text="; ".join(
                    f"{item.op_type} {item.namespace}.{item.entity}" for item in record.plan.operations
                ),
                prior_value=prior_value,
                new_value=new_value,
                **details,
            )

    @staticmethod
    @contextmanager
    def _correlation(audit_event_id: str):
        previous = get_correlation_id()
        set_correlation_id(audit_event_id)
        try:
            yield
        finally:
            set_correlation_id(previous or "")

    @staticmethod
    def _close_session(session: Any) -> None:
        close = getattr(session.connector, "close", None)
        if callable(close):
            close()
