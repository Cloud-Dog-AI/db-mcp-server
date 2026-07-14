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
# Covers: CO-03, CO-04
# Related tests: UT1.6, UT1.7, ST1.4, ST1.5, ST1.6, IT1.3, IT1.4, IT1.5

"""Connector dispatch helpers for db-mcp-server."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from fastapi import Request

from cloud_dog_api_kit.errors import InternalError, UnauthorisedError, ValidationError
from cloud_dog_db.connectors import database_driver_exceptions
from cloud_dog_logging import Actor, Target

from src.core.connectors.cassandra import CassandraConnector
from src.core.connectors.couchdb import CouchDBConnector
from src.core.connectors.elasticsearch import ElasticsearchConnector
from src.core.connectors.mariadb import MariaDBConnector
from src.core.connectors.mongodb import MongoDBConnector
from src.core.connectors.opensearch import OpenSearchConnector
from src.core.connectors.postgresql import PostgreSQLConnector
from src.core.connectors.relational import _build_uri
from src.core.filters import CassandraFilterTranslator, CouchDBFilterTranslator, ElasticsearchFilterTranslator, MongoDBFilterTranslator, OpenSearchFilterTranslator, RelationalFilterTranslator

_CONNECTOR_ERRORS = database_driver_exceptions()


@dataclass(slots=True)
class ConnectorSession:
    """Resolved connector, translator, and profile context."""

    profile: dict[str, Any]
    connector: Any
    translator: Any


class ConnectorManager:
    """Resolve connectors and execute profile-scoped operations."""

    _SOURCE_TYPE_ALIASES = {
        "postgres": "postgresql",
        "mysql": "mariadb",
    }

    def __init__(self, runtime) -> None:
        self._runtime = runtime

    def for_profile(self, profile_id: str) -> ConnectorSession:
        profile = self._runtime.access_control.get_profile_internal(profile_id)
        return self.for_profile_payload(profile)

    def for_profile_payload(self, profile: dict[str, Any]) -> ConnectorSession:
        """Resolve a connector from a profile-shaped payload."""
        source_type = str(profile.get("source_type", "")).strip().lower()
        source_type = self._SOURCE_TYPE_ALIASES.get(source_type, source_type)
        if source_type == "mongodb":
            return ConnectorSession(
                profile=profile,
                connector=self._build_mongodb_connector(profile),
                translator=MongoDBFilterTranslator(),
            )
        if source_type == "couchdb":
            return ConnectorSession(
                profile=profile,
                connector=self._build_couchdb_connector(profile),
                translator=CouchDBFilterTranslator(),
            )
        if source_type == "opensearch":
            return ConnectorSession(
                profile=profile,
                connector=self._build_opensearch_connector(profile),
                translator=OpenSearchFilterTranslator(),
            )
        if source_type == "elasticsearch":
            return ConnectorSession(
                profile=profile,
                connector=self._build_elasticsearch_connector(profile),
                translator=ElasticsearchFilterTranslator(),
            )
        if source_type == "cassandra":
            return ConnectorSession(
                profile=profile,
                connector=self._build_cassandra_connector(profile),
                translator=CassandraFilterTranslator(),
            )
        if source_type == "postgresql":
            return ConnectorSession(
                profile=profile,
                connector=self._build_postgresql_connector(profile),
                translator=RelationalFilterTranslator(),
            )
        if source_type == "mariadb":
            return ConnectorSession(
                profile=profile,
                connector=self._build_mariadb_connector(profile),
                translator=RelationalFilterTranslator(),
            )
        raise ValidationError(message=f"Unsupported source type: {source_type}")

    def test_source_connection(self, source_type: str, source_connection: str) -> dict[str, Any]:
        """Build a connector from a source-connection URI and return capabilities."""
        session = self.for_profile_payload(
            {
                "profile_id": "__source_connection_test__",
                "source_type": source_type,
                "source_connection": source_connection,
                "namespaces": [],
                "entities": [],
                "enabled_tools": [],
                "allowed_permissions": ["*"],
            }
        )
        try:
            capability_report = getattr(session.connector, "capability_report", None)
            if callable(capability_report):
                return dict(capability_report())
            return {"source_type": source_type, "capabilities": []}
        finally:
            close = getattr(session.connector, "close", None)
            if callable(close):
                close()

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
        except _CONNECTOR_ERRORS as exc:
            self._runtime.audit_logger.log_tool_call(
                actor=Actor(type="user", id=principal.user_id, roles=principal.roles),
                tool=audit_action,
                params={"profile_id": profile_id, "target": audit_target_id},
                outcome="failure",
                duration_ms=0,
                target=Target(type="connector", id=audit_target_id or profile_id),
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
            target=Target(type="connector", id=audit_target_id or profile_id),
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
        source_connection = self._resolve_source_connection(profile)
        if source_connection and "://" in source_connection:
            uri = source_connection
        else:
            uri = str(self._runtime.config.get("connectors.mongodb.default_uri", "") or "").strip()
        if not uri:
            raise ValidationError(message="MongoDB connector URI is not configured")
        connector = MongoDBConnector(
            uri=uri,
            timeout_ms=int(self._runtime.config.get("connectors.mongodb.timeout_ms", 60000)),
        )
        connector.validate_profile()
        return connector

    def _build_couchdb_connector(self, profile: dict[str, Any]) -> CouchDBConnector:
        if not bool(self._runtime.config.get("connectors.couchdb.enabled", True)):
            raise ValidationError(message="CouchDB connector is disabled")
        source_connection = self._resolve_source_connection(profile)
        if source_connection and "://" in source_connection:
            uri = source_connection
        else:
            uri = str(self._runtime.config.get("connectors.couchdb.default_uri", "") or "").strip()
        if not uri:
            raise ValidationError(message="CouchDB connector URI is not configured")
        connector = CouchDBConnector(
            uri=uri,
            timeout_seconds=int(self._runtime.config.get("connectors.couchdb.timeout_seconds", 30)),
        )
        connector.validate_profile()
        return connector

    def _build_cassandra_connector(self, profile: dict[str, Any]) -> CassandraConnector:
        if not bool(self._runtime.config.get("connectors.cassandra.enabled", True)):
            raise ValidationError(message="Cassandra connector is disabled")
        source_connection = self._resolve_source_connection(profile)
        if source_connection and "://" in source_connection:
            connector = CassandraConnector.from_uri(
                source_connection,
                timeout_seconds=int(self._runtime.config.get("connectors.cassandra.timeout_seconds", 30)),
            )
        else:
            host = str(self._runtime.config.get("connectors.cassandra.default_host", "") or "").strip()
            port = int(self._runtime.config.get("connectors.cassandra.default_port", 9042))
            if not host:
                raise ValidationError(message="Cassandra connector host is not configured")
            connector = CassandraConnector(
                host=host,
                port=port,
                timeout_seconds=int(self._runtime.config.get("connectors.cassandra.timeout_seconds", 30)),
            )
        connector.validate_profile()
        return connector

    def _build_elasticsearch_connector(self, profile: dict[str, Any]) -> ElasticsearchConnector:
        if not bool(self._runtime.config.get("connectors.elasticsearch.enabled", True)):
            raise ValidationError(message="Elasticsearch connector is disabled")
        source_connection = self._resolve_source_connection(profile)
        if source_connection and "://" in source_connection:
            uri = source_connection
        else:
            uri = str(self._runtime.config.get("connectors.elasticsearch.default_uri", "") or "").strip()
        if not uri:
            raise ValidationError(message="Elasticsearch connector URI is not configured")
        connector = ElasticsearchConnector(
            uri=uri,
            timeout_seconds=int(self._runtime.config.get("connectors.elasticsearch.timeout_seconds", 30)),
        )
        connector.validate_profile()
        return connector

    def _build_opensearch_connector(self, profile: dict[str, Any]) -> OpenSearchConnector:
        if not bool(self._runtime.config.get("connectors.opensearch.enabled", True)):
            raise ValidationError(message="OpenSearch connector is disabled")
        source_connection = self._resolve_source_connection(profile)
        if source_connection and "://" in source_connection:
            uri = source_connection
        else:
            uri = str(self._runtime.config.get("connectors.opensearch.default_uri", "") or "").strip()
        if not uri:
            raise ValidationError(message="OpenSearch connector URI is not configured")
        connector = OpenSearchConnector(
            uri=uri,
            timeout_seconds=int(self._runtime.config.get("connectors.opensearch.timeout_seconds", 30)),
        )
        connector.validate_profile()
        return connector

    def _build_postgresql_connector(self, profile: dict[str, Any]) -> PostgreSQLConnector:
        if not bool(self._runtime.config.get("connectors.postgresql.enabled", True)):
            raise ValidationError(message="PostgreSQL connector is disabled")
        uri = self._resolve_relational_uri(
            profile=profile,
            source_type="postgresql",
            default_uri_path="connectors.postgresql.default_uri",
            host_path="connectors.postgresql.default_host",
            port_path="connectors.postgresql.default_port",
            username_path="connectors.postgresql.default_username",
            password_path="connectors.postgresql.default_password",
            database_path="connectors.postgresql.default_database",
            scheme="postgresql",
        )
        connector = PostgreSQLConnector(
            uri=uri,
            timeout_seconds=int(self._runtime.config.get("connectors.postgresql.timeout_seconds", 30)),
        )
        connector.validate_profile()
        return connector

    def _build_mariadb_connector(self, profile: dict[str, Any]) -> MariaDBConnector:
        if not bool(self._runtime.config.get("connectors.mariadb.enabled", True)):
            raise ValidationError(message="MariaDB connector is disabled")
        uri = self._resolve_relational_uri(
            profile=profile,
            source_type="mariadb",
            default_uri_path="connectors.mariadb.default_uri",
            host_path="connectors.mariadb.default_host",
            port_path="connectors.mariadb.default_port",
            username_path="connectors.mariadb.default_username",
            password_path="connectors.mariadb.default_password",
            database_path="connectors.mariadb.default_database",
            scheme="mariadb",
        )
        connector = MariaDBConnector(
            uri=uri,
            timeout_seconds=int(self._runtime.config.get("connectors.mariadb.timeout_seconds", 30)),
        )
        connector.validate_profile()
        return connector

    def _resolve_relational_uri(
        self,
        *,
        profile: dict[str, Any],
        source_type: str,
        default_uri_path: str,
        host_path: str,
        port_path: str,
        username_path: str,
        password_path: str,
        database_path: str,
        scheme: str,
    ) -> str:
        source_connection = self._resolve_source_connection(profile)
        if source_connection and "://" in source_connection:
            return source_connection
        default_uri = str(self._runtime.config.get(default_uri_path, "") or "").strip()
        if default_uri:
            return default_uri
        uri = _build_uri(
            scheme=scheme,
            host=str(self._runtime.config.get(host_path, "") or "").strip(),
            port=int(self._runtime.config.get(port_path, 0) or 0),
            username=str(self._runtime.config.get(username_path, "") or "").strip(),
            password=str(self._runtime.config.get(password_path, "") or "").strip(),
            database=str(self._runtime.config.get(database_path, "") or "").strip(),
        )
        if uri:
            return uri
        raise ValidationError(message=f"{source_type.title()} connector URI is not configured")

    def _resolve_source_connection(self, profile: dict[str, Any]) -> str:
        value = str(profile.get("source_connection", "") or "").strip()
        if not value or "://" in value:
            return value
        try:
            connection = self._runtime.access_control.get_source_connection(value)
        except Exception:
            return value
        return str(connection.get("uri_template") or "").strip()

    @staticmethod
    def _enforce_tool_scope(profile: dict[str, Any], audit_action: str) -> None:
        enabled_tools = [str(item) for item in profile.get("enabled_tools", []) if str(item).strip()]
        if enabled_tools and audit_action not in enabled_tools:
            raise UnauthorisedError(message=f"Tool access denied by profile policy: {audit_action}")
