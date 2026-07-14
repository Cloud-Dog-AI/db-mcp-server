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
# Description: Runtime-profile-gated canonical test-data seeding.
# Related requirements: W28A-871 CW-TD2
# Related tests: UT1.22

"""Runtime-profile-gated test-data seeding."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from fastapi import Request

from cloud_dog_api_kit.errors import UnauthorisedError, ValidationError
from cloud_dog_db.connectors import build_source_connector
from cloud_dog_logging import Actor, Target

_BLOCKED_RUNTIME_PROFILES = {"production", "prod", "live"}

_USERS = (
    {"id": 1, "email": "alice@example.test", "display_name": "Alice"},
    {"id": 2, "email": "bob@example.test", "display_name": "Bob"},
    {"id": 3, "email": "carol@example.test", "display_name": "Carol"},
    {"id": 4, "email": "dave@example.test", "display_name": "Dave"},
    {"id": 5, "email": "eve@example.test", "display_name": "Eve"},
)

_ORDERS = (
    {"id": 1, "user_id": 1, "amount": 12.50, "status": "paid"},
    {"id": 2, "user_id": 1, "amount": 99.00, "status": "paid"},
    {"id": 3, "user_id": 2, "amount": 5.00, "status": "refunded"},
    {"id": 4, "user_id": 3, "amount": 250.00, "status": "paid"},
    {"id": 5, "user_id": 4, "amount": 7.25, "status": "pending"},
    {"id": 6, "user_id": 4, "amount": 18.50, "status": "failed"},
    {"id": 7, "user_id": 5, "amount": 20.00, "status": "paid"},
)


@dataclass(frozen=True, slots=True)
class _Dataset:
    dataset_id: str
    source_types: frozenset[str]


@dataclass(frozen=True, slots=True)
class _SeedResult:
    target: str
    counts: dict[str, int]


_DATASETS = {
    "w28a871_postgres": _Dataset(
        dataset_id="w28a871_postgres",
        source_types=frozenset({"postgres", "postgresql"}),
    ),
    "w28a871_mysql": _Dataset(
        dataset_id="w28a871_mysql",
        source_types=frozenset({"mysql", "mariadb"}),
    ),
    "w28a871_sqlite": _Dataset(
        dataset_id="w28a871_sqlite",
        source_types=frozenset({"sqlite"}),
    ),
    "w28a871_mongodb": _Dataset(
        dataset_id="w28a871_mongodb",
        source_types=frozenset({"mongodb"}),
    ),
    "w28a871_elasticsearch": _Dataset(
        dataset_id="w28a871_elasticsearch",
        source_types=frozenset({"elasticsearch"}),
    ),
}


class TestDataSeedService:
    """Seed canonical test data only in explicitly allowed runtime profiles."""

    def __init__(self, runtime: Any) -> None:
        self._runtime = runtime

    def seed(
        self,
        request: Request,
        *,
        dataset_id: str,
        connection_name: str,
    ) -> dict[str, Any]:
        principal = self._runtime.access_control.require_request_permission(
            request,
            permission="admin.write",
            audit_resource_type="test_data",
            audit_resource_id=dataset_id,
        )
        runtime_profile = self._runtime_profile()
        if not runtime_profile or runtime_profile in _BLOCKED_RUNTIME_PROFILES:
            raise UnauthorisedError(
                message=(
                    "Test data seed is disabled when no runtime profile is set "
                    "and in production runtime profiles"
                )
            )
        dataset = self._get_dataset(dataset_id)
        connection = self._runtime.access_control.get_source_connection(connection_name)
        source_type = str(connection.get("source_type") or "").strip().lower()
        if source_type not in dataset.source_types:
            raise ValidationError(
                message=(
                    f"Dataset {dataset_id} cannot be applied to source type "
                    f"{source_type!r}"
                )
            )
        uri = str(connection.get("uri_template") or "").strip()
        if not uri:
            raise ValidationError(message=f"Source connection has no URI: {connection_name}")
        result = self._seed_dataset(dataset_id=dataset.dataset_id, source_type=source_type, uri=uri)
        self._runtime.audit_logger.log_crud(
            actor=Actor(type="user", id=principal.user_id, roles=principal.roles),
            action="seed",
            target=Target(type="test_data", id="canonical"),
            outcome="success",
            runtime_profile=runtime_profile,
            dataset_id=dataset.dataset_id,
            connection_name=connection_name,
            source_type=source_type,
            counts=result.counts,
        )
        return {
            "ok": True,
            "runtime_profile": runtime_profile,
            "dataset_id": dataset.dataset_id,
            "connection_name": connection_name,
            "source_type": source_type,
            "target": result.target,
            "counts": result.counts,
        }

    def _runtime_profile(self) -> str:
        return (
            str(self._runtime.config.get("runtime.profile", "") or "")
            or str(self._runtime.config.get("runtime_profile", "") or "")
        ).strip()

    @staticmethod
    def _get_dataset(dataset_id: str) -> _Dataset:
        key = str(dataset_id or "").strip()
        try:
            return _DATASETS[key]
        except KeyError as exc:
            raise ValidationError(message=f"Unknown dataset_id: {dataset_id}") from exc

    def _seed_dataset(self, *, dataset_id: str, source_type: str, uri: str) -> _SeedResult:
        if dataset_id == "w28a871_postgres":
            return _seed_postgres(uri)
        if dataset_id == "w28a871_mysql":
            return _seed_mysql(uri)
        if dataset_id == "w28a871_sqlite":
            return _seed_sqlite(uri)
        if dataset_id == "w28a871_mongodb":
            return _seed_mongodb(uri)
        if dataset_id == "w28a871_elasticsearch":
            return _seed_elasticsearch(uri)
        raise ValidationError(message=f"Unknown dataset_id: {dataset_id}")


def _apply_schema_change(connector: Any, operation: str, namespace: str, entity: str = "", **parameters: Any) -> None:
    connector.schema_change_apply(
        {
            "operation": operation,
            "namespace": namespace,
            "entity": entity,
            "parameters": parameters,
        }
    )


def _replace_entity(connector: Any, namespace: str, entity: str, **parameters: Any) -> None:
    existing = {str(item.get("name")) for item in connector.list_entities(namespace)}
    if entity in existing:
        _apply_schema_change(connector, "drop_entity", namespace, entity)
    _apply_schema_change(connector, "create_entity", namespace, entity, **parameters)


def _seed_relational(uri: str, dialect: str, namespace: str, target: str) -> _SeedResult:
    connector = build_source_connector(dialect, uri=uri, timeout_seconds=30)
    try:
        if dialect == "postgresql":
            _apply_schema_change(connector, "drop_namespace", namespace)
            _apply_schema_change(connector, "create_namespace", namespace)
        else:
            for entity in ("orders", "users"):
                existing = {str(item.get("name")) for item in connector.list_entities(namespace)}
                if entity in existing:
                    _apply_schema_change(connector, "drop_entity", namespace, entity)
        _replace_entity(
            connector,
            namespace,
            "users",
            columns={"id": "integer", "email": "string", "display_name": "string"},
            primary_key="id",
        )
        _replace_entity(
            connector,
            namespace,
            "orders",
            columns={"id": "integer", "user_id": "integer", "amount": "float", "status": "string"},
            primary_key="id",
        )
        for item in _USERS:
            connector.create(namespace, "users", dict(item))
        for item in _ORDERS:
            connector.create(namespace, "orders", dict(item))
        counts = {
            "users": connector.count(namespace, "users"),
            "orders": connector.count(namespace, "orders"),
        }
    finally:
        connector.close()
    return _SeedResult(target=target, counts=counts)


def _seed_sqlite(uri: str) -> _SeedResult:
    parsed = urlparse(uri)
    if parsed.scheme not in {"sqlite", "sqlite+pysqlite"}:
        raise ValidationError(message=f"Unsupported SQLite URI: {parsed.scheme}")
    path = ":memory:" if parsed.path in {"", "/:memory:"} else parsed.path
    return _seed_relational(uri, "sqlite", "main", path)


def _seed_postgres(uri: str) -> _SeedResult:
    return _seed_relational(uri, "postgresql", "w28a871", "schema:w28a871")


def _seed_mysql(uri: str) -> _SeedResult:
    parsed = urlparse(uri)
    database = parsed.path.strip("/") or "w28a871"
    if parsed.scheme not in {"mysql", "mariadb"} or not database.replace("_", "").isalnum():
        raise ValidationError(message=f"Unsupported MySQL URI or database: {parsed.scheme}/{database}")
    return _seed_relational(uri, "mariadb", database, f"database:{database}")


def _mongodb_database(uri: str) -> str:
    parsed = urlparse(uri)
    return parsed.path.strip("/") or "w28a871"


def _seed_mongodb(uri: str) -> _SeedResult:
    database = _mongodb_database(uri)
    connector = build_source_connector("mongodb", uri=uri, timeout_ms=5000)
    try:
        _replace_entity(connector, database, "users")
        _replace_entity(connector, database, "orders")
        for item in _USERS:
            connector.create(database, "users", {"_id": item["id"], **item})
        for item in _ORDERS:
            connector.create(database, "orders", {"_id": item["id"], **item})
        _apply_schema_change(
            connector,
            "create_index",
            database,
            "users",
            keys=[{"field": "email", "direction": "asc"}],
            name="idx_users_email",
            unique=True,
        )
        counts = {
            "users": connector.count(database, "users"),
            "orders": connector.count(database, "orders"),
        }
    finally:
        connector.close()
    return _SeedResult(target=f"database:{database}", counts=counts)


def _seed_elasticsearch(uri: str) -> _SeedResult:
    connector = build_source_connector("elasticsearch", uri=uri, timeout_seconds=30)
    try:
        namespace = str(connector.list_namespaces()[0]["name"])
        users_index = "w28a871-users"
        orders_index = "w28a871-orders"
        _replace_entity(
            connector,
            namespace,
            users_index,
            settings={"number_of_replicas": 0},
            properties={"id": {"type": "integer"}, "email": {"type": "text"}, "display_name": {"type": "text"}},
        )
        _replace_entity(
            connector,
            namespace,
            orders_index,
            settings={"number_of_replicas": 0},
            properties={"id": {"type": "integer"}, "user_id": {"type": "integer"}, "amount": {"type": "double"}, "status": {"type": "keyword"}},
        )
        for item in _USERS:
            connector.create(namespace, users_index, {"_id": item["id"], **item})
        for item in _ORDERS:
            connector.create(namespace, orders_index, {"_id": item["id"], **item})
    finally:
        connector.close()
    return _SeedResult(
        target="indices:w28a871-users,w28a871-orders",
        counts={"users": len(_USERS), "orders": len(_ORDERS)},
    )
