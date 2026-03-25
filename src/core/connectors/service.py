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
# Description: Connector dispatch and profile-scoped execution orchestration.
# Related requirements: CN-01, AC-01, AC-02, CO-01, CO-02
# Related tests: UT1.6, UT1.7, ST1.4, ST1.5, ST1.6, IT1.3, IT1.4, IT1.5

"""Connector dispatch helpers for db-mcp-server."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from fastapi import Request
from pymongo.errors import PyMongoError

from cloud_dog_api_kit.errors import InternalError, UnauthorisedError, ValidationError
from cloud_dog_logging import Actor

from src.core.connectors.mongodb import MongoDBConnector
from src.core.filters import MongoDBFilterTranslator


@dataclass(slots=True)
class ConnectorSession:
    """Resolved connector, translator, and profile context."""

    profile: dict[str, Any]
    connector: Any
    translator: Any


class ConnectorManager:
    """Resolve connectors and execute profile-scoped operations."""

    def __init__(self, runtime) -> None:
        self._runtime = runtime

    def for_profile(self, profile_id: str) -> ConnectorSession:
        profile = self._runtime.access_control.get_profile(profile_id)
        source_type = str(profile.get("source_type", "")).strip().lower()
        if source_type == "mongodb":
            return ConnectorSession(
                profile=profile,
                connector=self._build_mongodb_connector(profile),
                translator=MongoDBFilterTranslator(),
            )
        raise ValidationError(message=f"Unsupported source type: {source_type}")

    def execute(
        self,
        request: Request,
        *,
        profile_id: str,
        permission: str,
        audit_action: str,
        audit_target_id: str,
        callback: Callable[[ConnectorSession], Any],
    ) -> Any:
        principal = self._runtime.access_control.require_request_permission(
            request,
            permission=permission,
            profile_id=profile_id,
            audit_resource_type="profile",
            audit_resource_id=profile_id,
        )
        session = self.for_profile(profile_id)
        try:
            self._enforce_tool_scope(session.profile, audit_action)
            result = callback(session)
        except PyMongoError as exc:
            self._runtime.audit_logger.log_tool_call(
                actor=Actor(type="user", id=principal.user_id, roles=principal.roles),
                tool=audit_action,
                params={"profile_id": profile_id, "target": audit_target_id},
                outcome="failure",
                duration_ms=0,
                error=str(exc),
            )
            raise InternalError(message=f"Connector operation failed: {exc}") from exc
        finally:
            close = getattr(session.connector, "close", None)
            if callable(close):
                close()
        self._runtime.audit_logger.log_tool_call(
            actor=Actor(type="user", id=principal.user_id, roles=principal.roles),
            tool=audit_action,
            params={"profile_id": profile_id, "target": audit_target_id},
            outcome="success",
            duration_ms=0,
        )
        return result

    def mask_record(self, profile_id: str, record: dict[str, Any]) -> dict[str, Any]:
        """Apply profile field masking to a single record."""
        return self._runtime.access_control.apply_profile_mask(profile_id, record)

    def mask_records(self, profile_id: str, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Apply profile field masking to a list of records."""
        return [self.mask_record(profile_id, item) for item in records]

    def ensure_namespace_allowed(self, profile: dict[str, Any], namespace: str) -> None:
        allowed_namespaces = [str(item) for item in profile.get("namespaces", []) if str(item).strip()]
        if allowed_namespaces and namespace not in allowed_namespaces:
            raise UnauthorisedError(message=f"Namespace access denied: {namespace}")

    def ensure_entity_allowed(self, profile: dict[str, Any], namespace: str, entity: str) -> None:
        self.ensure_namespace_allowed(profile, namespace)
        allowed_entities = [str(item) for item in profile.get("entities", []) if str(item).strip()]
        if not allowed_entities:
            return
        canonical = {entity, f"{namespace}.{entity}"}
        if not canonical.intersection(set(allowed_entities)):
            raise UnauthorisedError(message=f"Entity access denied: {namespace}.{entity}")

    def filter_namespaces(self, profile: dict[str, Any], namespaces: list[dict[str, Any]]) -> list[dict[str, Any]]:
        allowed = [str(item) for item in profile.get("namespaces", []) if str(item).strip()]
        if not allowed:
            return namespaces
        return [item for item in namespaces if str(item.get("name")) in allowed]

    def filter_entities(self, profile: dict[str, Any], namespace: str, entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
        allowed_entities = [str(item) for item in profile.get("entities", []) if str(item).strip()]
        if not allowed_entities:
            return entities
        allowed = set(allowed_entities)
        return [
            item
            for item in entities
            if str(item.get("name")) in allowed or f"{namespace}.{item.get('name')}" in allowed
        ]

    def _build_mongodb_connector(self, profile: dict[str, Any]) -> MongoDBConnector:
        if not bool(self._runtime.config.get("connectors.mongodb.enabled", True)):
            raise ValidationError(message="MongoDB connector is disabled")
        source_connection = str(profile.get("source_connection", "") or "").strip()
        if source_connection and "://" in source_connection:
            uri = source_connection
        else:
            uri = str(self._runtime.config.get("connectors.mongodb.default_uri", "") or "").strip()
        if not uri:
            raise ValidationError(message="MongoDB connector URI is not configured")
        connector = MongoDBConnector(
            uri=uri,
            timeout_ms=int(self._runtime.config.get("connectors.mongodb.timeout_ms", 30000)),
        )
        connector.validate_profile()
        return connector

    @staticmethod
    def _enforce_tool_scope(profile: dict[str, Any], audit_action: str) -> None:
        enabled_tools = [str(item) for item in profile.get("enabled_tools", []) if str(item).strip()]
        if enabled_tools and audit_action not in enabled_tools:
            raise UnauthorisedError(message=f"Tool access denied by profile policy: {audit_action}")
