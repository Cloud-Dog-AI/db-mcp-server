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
# Description: Profile-scoped discovery service with metadata-store cache.
# Related requirements: W28A-871 DM-P-09, DM-CAT-04, DM-S-01, CW-DA2, CW-DA3
# Related tests: UT1.20

"""Discovery service backed by the metadata-store discovery cache."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from fastapi import Request

from cloud_dog_api_kit.errors import ValidationError
from cloud_dog_logging import Actor, Target


class DiscoveryService:
    """Discover connector metadata and cache profile-scoped option lists."""

    def __init__(self, runtime: Any) -> None:
        self._runtime = runtime

    def namespaces(
        self,
        request: Request,
        *,
        profile_id: str | None = None,
        connection_name: str | None = None,
        refresh: bool = False,
        ttl_seconds: int = 600,
    ) -> dict[str, Any]:
        """Discover namespaces by profile or draft source connection."""
        if bool(profile_id) == bool(connection_name):
            raise ValidationError(message="Provide exactly one of profile_id or connection_name")
        if connection_name:
            return self._discover_connection_namespaces(
                request,
                connection_name=connection_name,
            )
        assert profile_id is not None
        return self._cached_profile_discovery(
            request,
            profile_id=profile_id,
            cache_key="namespaces",
            permission="catalog.read",
            audit_action="catalog.list_namespaces",
            audit_target_id=profile_id,
            refresh=refresh,
            ttl_seconds=ttl_seconds,
            loader=lambda session: self._runtime.connectors.filter_namespaces(
                session.profile,
                session.connector.list_namespaces(),
            ),
        )

    def entities(
        self,
        request: Request,
        *,
        profile_id: str,
        namespace: str,
        refresh: bool = False,
        ttl_seconds: int = 600,
    ) -> dict[str, Any]:
        """Discover entities visible to a profile in a namespace."""
        namespace = self._require_value(namespace, "namespace")
        return self._cached_profile_discovery(
            request,
            profile_id=self._require_value(profile_id, "profile_id"),
            cache_key=f"entities:{namespace}",
            permission="catalog.read",
            audit_action="catalog.list_entities",
            audit_target_id=f"{profile_id}:{namespace}",
            refresh=refresh,
            ttl_seconds=ttl_seconds,
            loader=lambda session: self._discover_entities(session, namespace),
        )

    def fields(
        self,
        request: Request,
        *,
        profile_id: str,
        namespace: str,
        entity: str,
        refresh: bool = False,
        ttl_seconds: int = 600,
    ) -> dict[str, Any]:
        """Discover fields visible to a profile for an entity."""
        namespace = self._require_value(namespace, "namespace")
        entity = self._require_value(entity, "entity")
        return self._cached_profile_discovery(
            request,
            profile_id=self._require_value(profile_id, "profile_id"),
            cache_key=f"fields:{namespace}:{entity}",
            permission="schema.read",
            audit_action="schema.describe_fields",
            audit_target_id=f"{profile_id}:{namespace}.{entity}",
            refresh=refresh,
            ttl_seconds=ttl_seconds,
            loader=lambda session: self._discover_fields(session, namespace, entity),
        )

    def _cached_profile_discovery(
        self,
        request: Request,
        *,
        profile_id: str,
        cache_key: str,
        permission: str,
        audit_action: str,
        audit_target_id: str,
        refresh: bool,
        ttl_seconds: int,
        loader: Callable[[Any], list[dict[str, Any]]],
    ) -> dict[str, Any]:
        ttl = self._ttl(ttl_seconds)
        cached = self._runtime.access_control.get_discovery_cache(
            profile_id=profile_id,
            cache_key=cache_key,
        )
        if cached and not refresh and self._is_fresh(cached):
            return self._payload(
                items=cached["payload"],
                cache_key=cache_key,
                status="hit",
                stale=False,
                refreshed_at=cached["refreshed_at"],
                ttl_seconds=int(cached["ttl_seconds"]),
            )

        items = self._runtime.connectors.execute(
            request,
            profile_id=profile_id,
            permission=permission,
            audit_action=audit_action,
            audit_target_id=audit_target_id,
            callback=loader,
        )
        saved = self._runtime.access_control.upsert_discovery_cache(
            profile_id=profile_id,
            cache_key=cache_key,
            payload=items,
            ttl_seconds=ttl,
        )
        return self._payload(
            items=items,
            cache_key=cache_key,
            status="refreshed",
            stale=False,
            refreshed_at=saved["refreshed_at"],
            ttl_seconds=ttl,
        )

    def _discover_connection_namespaces(self, request: Request, *, connection_name: str) -> dict[str, Any]:
        connection = self._runtime.access_control.get_source_connection(connection_name)
        uri_template = str(connection.get("uri_template") or "")
        if "${" in uri_template:
            raise ValidationError(
                message="Cannot discover source connection with unresolved template placeholders"
            )
        principal = self._runtime.access_control.require_request_permission(
            request,
            permission="catalog.read",
            audit_resource_type="source_connection",
            audit_resource_id=connection_name,
        )
        session = self._runtime.connectors.for_profile_payload(
            {
                "profile_id": f"connection:{connection_name}",
                "source_type": connection["source_type"],
                "source_connection": uri_template,
                "namespaces": [],
                "entities": [],
                "enabled_tools": [],
                "allowed_permissions": ["*"],
            }
        )
        try:
            items = session.connector.list_namespaces()
        finally:
            close = getattr(session.connector, "close", None)
            if callable(close):
                close()
        self._runtime.audit_logger.log_tool_call(
            actor=Actor(type="user", id=principal.user_id, roles=principal.roles),
            tool="catalog.list_namespaces",
            params={"connection_name": connection_name},
            outcome="success",
            duration_ms=0,
            target=Target(type="source_connection", id=connection_name),
        )
        return {
            "items": items,
            "cache": {
                "cache_key": None,
                "status": "uncached",
                "stale": False,
                "refreshed_at": None,
                "ttl_seconds": None,
            },
        }

    def _discover_entities(self, session: Any, namespace: str) -> list[dict[str, Any]]:
        self._runtime.connectors.ensure_namespace_allowed(session.profile, namespace)
        return self._runtime.connectors.filter_entities(
            session.profile,
            namespace,
            session.connector.list_entities(namespace),
        )

    def _discover_fields(self, session: Any, namespace: str, entity: str) -> list[dict[str, Any]]:
        self._runtime.connectors.ensure_entity_allowed(session.profile, namespace, entity)
        return list(session.connector.describe_fields(namespace, entity).get("fields", []))

    @staticmethod
    def _payload(
        *,
        items: list[dict[str, Any]],
        cache_key: str,
        status: str,
        stale: bool,
        refreshed_at: datetime,
        ttl_seconds: int,
    ) -> dict[str, Any]:
        return {
            "items": items,
            "cache": {
                "cache_key": cache_key,
                "status": status,
                "stale": stale,
                "refreshed_at": refreshed_at.isoformat(),
                "ttl_seconds": ttl_seconds,
            },
        }

    @staticmethod
    def _is_fresh(cached: dict[str, Any]) -> bool:
        refreshed_at = cached["refreshed_at"]
        if refreshed_at.tzinfo is None:
            refreshed_at = refreshed_at.replace(tzinfo=timezone.utc)
        age = datetime.now(timezone.utc) - refreshed_at
        return age.total_seconds() <= int(cached["ttl_seconds"])

    @staticmethod
    def _ttl(ttl_seconds: int) -> int:
        return max(1, min(int(ttl_seconds or 600), 86_400))

    @staticmethod
    def _require_value(value: str, field_name: str) -> str:
        result = str(value or "").strip()
        if not result:
            raise ValidationError(message=f"{field_name} is required")
        return result
