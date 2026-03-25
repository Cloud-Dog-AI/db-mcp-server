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
# Description: Relationship service for inferred and curated source links.
# Related requirements: RL-01, RL-02, RL-03, AC-02
# Related tests: UT1.8, IT1.5

"""Relationship metadata service."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import Request

from cloud_dog_api_kit.errors import NotFoundError
from cloud_dog_logging import Actor, Target

from src.core.relationships.models import RelationshipRecord, utcnow
from src.core.relationships.repository import RelationshipRepository


class RelationshipService:
    """Manage relationship metadata and source inference."""

    def __init__(self, runtime) -> None:
        self._runtime = runtime
        self._repository = RelationshipRepository(runtime.metadata_engine)

    def list(self, request: Request, *, profile_id: str, namespace: str, entity: str) -> list[dict[str, Any]]:
        self._runtime.access_control.require_request_permission(
            request,
            permission="relationship.read",
            profile_id=profile_id,
            audit_resource_type="relationship",
            audit_resource_id=f"{profile_id}:{namespace}.{entity}",
        )
        return [self._view(item) for item in self._repository.list_for_entity(profile_id, namespace, entity)]

    def get(self, request: Request, *, relationship_id: str) -> dict[str, Any]:
        record = self._repository.get(relationship_id)
        if record is None:
            raise NotFoundError(message=f"Relationship not found: {relationship_id}")
        self._runtime.access_control.require_request_permission(
            request,
            permission="relationship.read",
            profile_id=record.profile_id,
            audit_resource_type="relationship",
            audit_resource_id=relationship_id,
        )
        return self._view(record)

    def infer(self, request: Request, *, profile_id: str, namespace: str, entity: str) -> list[dict[str, Any]]:
        def callback(session):
            self._runtime.connectors.ensure_entity_allowed(session.profile, namespace, entity)
            inferred = session.connector.extract_relationships(namespace, entity)
            records = []
            for item in inferred:
                record = RelationshipRecord(
                    profile_id=profile_id,
                    namespace=namespace,
                    entity=entity,
                    field=str(item.get("field", "")),
                    target_namespace=str(item.get("target_namespace") or namespace),
                    target_entity=str(item.get("target_entity") or item.get("target_entity_hint") or ""),
                    relationship_type=str(item.get("relationship_type") or "reference_candidate"),
                    provenance="inferred",
                    confidence=float(item.get("confidence")) if item.get("confidence") is not None else None,
                    metadata={k: v for k, v in item.items() if k not in {"field", "target_namespace", "target_entity", "target_entity_hint", "relationship_type", "confidence"}},
                )
                self._repository.upsert(record)
                records.append(record)
            return [self._view(item) for item in records]

        return self._runtime.connectors.execute(
            request,
            profile_id=profile_id,
            permission="relationship.change",
            audit_action="relationship.infer",
            audit_target_id=f"{profile_id}:{namespace}.{entity}",
            callback=callback,
        )

    def create(self, request: Request, payload: dict[str, Any]) -> dict[str, Any]:
        profile_id = str(payload.get("profile_id", ""))
        namespace = str(payload.get("namespace", ""))
        entity = str(payload.get("entity", ""))
        principal = self._runtime.access_control.require_request_permission(
            request,
            permission="relationship.change",
            profile_id=profile_id,
            audit_resource_type="relationship",
            audit_resource_id=f"{profile_id}:{namespace}.{entity}",
        )
        record = RelationshipRecord(
            profile_id=profile_id,
            namespace=namespace,
            entity=entity,
            field=str(payload.get("field", "")),
            target_namespace=str(payload.get("target_namespace") or namespace),
            target_entity=str(payload.get("target_entity", "")),
            relationship_type=str(payload.get("relationship_type") or "curated"),
            provenance="curated",
            confidence=float(payload.get("confidence")) if payload.get("confidence") is not None else None,
            description=str(payload.get("description") or ""),
            metadata=dict(payload.get("metadata") or {}),
        )
        self._repository.upsert(record)
        self._runtime.audit_logger.log_crud(
            actor=Actor(type="user", id=principal.user_id, roles=principal.roles),
            action="create",
            target=Target(type="relationship", id=record.relationship_id),
            outcome="success",
            profile_id=profile_id,
        )
        return self._view(record)

    def update(self, request: Request, relationship_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        current = self._repository.get(relationship_id)
        if current is None:
            raise NotFoundError(message=f"Relationship not found: {relationship_id}")
        principal = self._runtime.access_control.require_request_permission(
            request,
            permission="relationship.change",
            profile_id=current.profile_id,
            audit_resource_type="relationship",
            audit_resource_id=relationship_id,
        )
        updated = RelationshipRecord(
            relationship_id=current.relationship_id,
            profile_id=current.profile_id,
            namespace=str(payload.get("namespace") or current.namespace),
            entity=str(payload.get("entity") or current.entity),
            field=str(payload.get("field") or current.field),
            target_namespace=str(payload.get("target_namespace") or current.target_namespace),
            target_entity=str(payload.get("target_entity") or current.target_entity),
            relationship_type=str(payload.get("relationship_type") or current.relationship_type),
            provenance=str(payload.get("provenance") or current.provenance),
            confidence=float(payload.get("confidence")) if payload.get("confidence") is not None else current.confidence,
            description=str(payload.get("description") or current.description),
            metadata=dict(payload.get("metadata") or current.metadata),
            created_at=current.created_at,
            updated_at=utcnow(),
        )
        self._repository.upsert(updated)
        self._runtime.audit_logger.log_crud(
            actor=Actor(type="user", id=principal.user_id, roles=principal.roles),
            action="update",
            target=Target(type="relationship", id=relationship_id),
            outcome="success",
        )
        return self._view(updated)

    def delete(self, request: Request, relationship_id: str) -> dict[str, Any]:
        current = self._repository.get(relationship_id)
        if current is None:
            raise NotFoundError(message=f"Relationship not found: {relationship_id}")
        principal = self._runtime.access_control.require_request_permission(
            request,
            permission="relationship.change",
            profile_id=current.profile_id,
            audit_resource_type="relationship",
            audit_resource_id=relationship_id,
        )
        self._repository.delete(relationship_id)
        self._runtime.audit_logger.log_crud(
            actor=Actor(type="user", id=principal.user_id, roles=principal.roles),
            action="delete",
            target=Target(type="relationship", id=relationship_id),
            outcome="success",
        )
        return {"deleted": True, "relationship_id": relationship_id}

    @staticmethod
    def _view(record: RelationshipRecord) -> dict[str, Any]:
        payload = asdict(record)
        payload["created_at"] = record.created_at.isoformat()
        payload["updated_at"] = record.updated_at.isoformat()
        return payload
