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
# Description: Shared relational connector helpers for SQL backends.
# Related requirements: CN-01, CO-01, CO-02

"""Shared relational connector helpers for SQL backends."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any
from urllib.parse import quote_plus, urlparse, urlunparse

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    Integer,
    LargeBinary,
    MetaData,
    String,
    Table,
    Text,
    and_,
    create_engine,
    delete,
    func,
    inspect,
    not_,
    or_,
    select,
    text,
    update as sql_update,
)
from sqlalchemy.engine import Engine
from sqlalchemy.exc import NoSuchTableError
from sqlalchemy.sql.elements import ColumnElement

from src.core.filters import FilterCondition, FilterGroup, FilterNode, parse_filter


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalise_uri(uri: str, *, scheme: str) -> str:
    parsed = urlparse(uri)
    if "://" not in uri:
        raise ValueError("Connection URI must include a scheme")
    if parsed.scheme == scheme:
        return uri
    if scheme == "postgresql+psycopg" and parsed.scheme == "postgresql":
        return urlunparse(parsed._replace(scheme=scheme))
    if scheme == "mysql+pymysql" and parsed.scheme in {"mysql", "mariadb"}:
        return urlunparse(parsed._replace(scheme=scheme))
    return uri


def _build_uri(
    *,
    scheme: str,
    host: str,
    port: int,
    username: str = "",
    password: str = "",
    database: str = "",
) -> str:
    if not host:
        return ""
    auth = ""
    if username:
        auth = quote_plus(username)
        if password:
            auth = f"{auth}:{quote_plus(password)}"
        auth = f"{auth}@"
    path = f"/{database}" if database else ""
    return f"{scheme}://{auth}{host}:{port}{path}"


class RelationalConnector:
    """Shared relational connector implementation for SQL backends."""

    source_type = "sql"
    namespace_type = "schema"
    system_namespaces: set[str] = set()
    driver_scheme = ""
    regex_operator = "REGEXP"

    def __init__(self, *, uri: str, timeout_seconds: int = 30) -> None:
        self._uri = _normalise_uri(uri, scheme=self.driver_scheme)
        self._timeout_seconds = timeout_seconds
        self._engine = create_engine(
            self._uri,
            future=True,
            pool_pre_ping=True,
            connect_args=self._connect_args(),
        )

    @property
    def uri(self) -> str:
        return self._uri

    def _connect_args(self) -> dict[str, Any]:
        return {"connect_timeout": self._timeout_seconds}

    def close(self) -> None:
        self._engine.dispose()

    def capability_report(self) -> dict[str, Any]:
        return {
            "source_type": self.source_type,
            "supports": {
                "namespace_listing": True,
                "entity_listing": True,
                "entity_description": True,
                "field_inference": False,
                "mapping_schema": True,
                "structured_read": True,
                "create": True,
                "update": True,
                "delete": True,
                "count": True,
                "sample_shapes": True,
                "list_indexes": True,
                "schema_change_plan": True,
                "schema_change_apply": True,
                "relationship_inference": True,
            },
            "schema_change_operations": [
                "create_entity",
                "drop_entity",
                "create_index",
                "drop_index",
            ],
            "timestamp": _utcnow(),
        }

    def validate_profile(self) -> dict[str, Any]:
        with self._engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"ok": True, "source_type": self.source_type, "timestamp": _utcnow()}

    def list_namespaces(self) -> list[dict[str, Any]]:
        inspector = inspect(self._engine)
        return [
            {"name": name, "type": self.namespace_type}
            for name in sorted(inspector.get_schema_names())
            if name not in self.system_namespaces
        ]

    def list_entities(self, namespace: str) -> list[dict[str, Any]]:
        inspector = inspect(self._engine)
        return [
            {"name": name, "type": "table"}
            for name in sorted(inspector.get_table_names(schema=namespace))
        ]

    def describe_entity(self, namespace: str, entity: str) -> dict[str, Any]:
        inspector = inspect(self._engine)
        return {
            "namespace": namespace,
            "entity": entity,
            "entity_type": "table",
            "document_count": self.count(namespace, entity),
            "indexes": self.list_indexes(namespace, entity),
            "primary_key": inspector.get_pk_constraint(entity, schema=namespace),
            "foreign_keys": inspector.get_foreign_keys(entity, schema=namespace),
        }

    def describe_fields(self, namespace: str, entity: str) -> dict[str, Any]:
        inspector = inspect(self._engine)
        pk_columns = set((inspector.get_pk_constraint(entity, schema=namespace) or {}).get("constrained_columns") or [])
        fields = []
        for column in inspector.get_columns(entity, schema=namespace):
            fields.append(
                {
                    "name": column["name"],
                    "types": [str(column.get("type"))],
                    "nullable": bool(column.get("nullable", True)),
                    "default": self._normalise_value(column.get("default")),
                    "kind": "primary_key" if column["name"] in pk_columns else "regular",
                }
            )
        if not fields:
            fields = self._describe_fields_via_information_schema(namespace, entity, pk_columns)
        return {
            "namespace": namespace,
            "entity": entity,
            "fields": fields,
            "sample_count": 0,
            "source": "information_schema",
        }

    def read(
        self,
        namespace: str,
        entity: str,
        filter: Any = None,
        projection: dict[str, Any] | None = None,
        sort: list[dict[str, Any]] | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        table = self._reflect_table(namespace, entity)
        columns = self._projection_columns(table, projection)
        statement = select(*columns)
        clause = self._build_where_clause(table, filter)
        if clause is not None:
            statement = statement.where(clause)
        for item in sort or []:
            column = table.c.get(str(item.get("field", "")))
            if column is None:
                continue
            if str(item.get("direction", "asc")).lower() == "desc":
                statement = statement.order_by(column.desc())
            else:
                statement = statement.order_by(column.asc())
        if limit:
            statement = statement.limit(int(limit))
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [self._normalise_record(dict(row)) for row in rows]

    def create(self, namespace: str, entity: str, document: dict[str, Any]) -> dict[str, Any]:
        table = self._reflect_table(namespace, entity)
        payload = dict(document or {})
        with self._engine.begin() as connection:
            result = connection.execute(table.insert().values(**payload))
            created = self._reload_inserted_row(connection, table, payload, result.inserted_primary_key)
        return {
            "inserted_id": self._inserted_id(table, payload, result.inserted_primary_key),
            "document": self._normalise_record(created or payload),
        }

    def update(self, namespace: str, entity: str, filter: Any, update: dict[str, Any]) -> dict[str, Any]:
        table = self._reflect_table(namespace, entity)
        payload = dict(update or {})
        set_values = dict(payload.get("$set") or {})
        if payload and not set_values and not any(str(key).startswith("$") for key in payload):
            set_values = payload
        unset_fields = list(payload.get("$unset") or [])
        values = dict(set_values)
        for field in unset_fields:
            values[str(field)] = None
        statement = sql_update(table).values(**values)
        clause = self._build_where_clause(table, filter)
        if clause is not None:
            statement = statement.where(clause)
        with self._engine.begin() as connection:
            result = connection.execute(statement)
        return {"matched_count": int(result.rowcount or 0), "modified_count": int(result.rowcount or 0)}

    def delete(self, namespace: str, entity: str, filter: Any) -> dict[str, Any]:
        table = self._reflect_table(namespace, entity)
        statement = delete(table)
        clause = self._build_where_clause(table, filter)
        if clause is not None:
            statement = statement.where(clause)
        with self._engine.begin() as connection:
            result = connection.execute(statement)
        return {"deleted_count": int(result.rowcount or 0)}

    def count(self, namespace: str, entity: str, filter: Any = None) -> int:
        table = self._reflect_table(namespace, entity)
        statement = select(func.count()).select_from(table)
        clause = self._build_where_clause(table, filter)
        if clause is not None:
            statement = statement.where(clause)
        with self._engine.connect() as connection:
            return int(connection.execute(statement).scalar_one())

    def sample_shapes(self, namespace: str, entity: str, n: int = 10) -> list[dict[str, Any]]:
        table = self._reflect_table(namespace, entity)
        statement = select(table).limit(max(1, int(n)))
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [self._normalise_record(dict(row)) for row in rows]

    def list_indexes(self, namespace: str, entity: str) -> list[dict[str, Any]]:
        inspector = inspect(self._engine)
        indexes = []
        for item in inspector.get_indexes(entity, schema=namespace):
            indexes.append(
                {
                    "name": item.get("name"),
                    "columns": item.get("column_names") or [],
                    "unique": bool(item.get("unique", False)),
                }
            )
        pk = inspector.get_pk_constraint(entity, schema=namespace) or {}
        if pk.get("name"):
            indexes.append(
                {
                    "name": pk.get("name"),
                    "columns": pk.get("constrained_columns") or [],
                    "unique": True,
                    "primary_key": True,
                }
            )
        return indexes

    def schema_change_plan(self, operation: dict[str, Any]) -> dict[str, Any]:
        raw = dict(operation or {})
        op_type = str(raw.get("operation") or raw.get("op_type") or "").strip()
        namespace = str(raw.get("namespace") or "").strip()
        entity = str(raw.get("entity") or "").strip()
        parameters = dict(raw.get("parameters") or {})
        for key, value in raw.items():
            if key not in {"operation", "op_type", "namespace", "entity", "parameters"}:
                parameters[key] = value
        return {
            "dry_run": True,
            "source_type": self.source_type,
            "operation": op_type,
            "namespace": namespace,
            "entity": entity,
            "parameters": parameters,
            "timestamp": _utcnow(),
        }

    def schema_change_apply(self, plan: dict[str, Any]) -> dict[str, Any]:
        raw = dict(plan or {})
        op_type = str(raw.get("operation") or raw.get("op_type") or "").strip()
        namespace = str(raw.get("namespace") or "").strip()
        entity = str(raw.get("entity") or "").strip()
        parameters = dict(raw.get("parameters") or {})
        for key, value in raw.items():
            if key not in {"operation", "op_type", "namespace", "entity", "parameters"}:
                parameters[key] = value
        with self._engine.begin() as connection:
            if op_type == "create_entity":
                self._create_entity(connection, namespace, entity, parameters)
                return {"applied": True, "success": True, "operation": op_type, "namespace": namespace, "entity": entity}
            if op_type == "drop_entity":
                self._drop_entity(connection, namespace, entity)
                return {"applied": True, "success": True, "operation": op_type, "namespace": namespace, "entity": entity}
            if op_type == "create_index":
                index_name = self._create_index(connection, namespace, entity, parameters)
                return {
                    "applied": True,
                    "success": True,
                    "operation": op_type,
                    "namespace": namespace,
                    "entity": entity,
                    "index_name": index_name,
                }
            if op_type == "drop_index":
                self._drop_index(connection, namespace, entity, parameters)
                return {"applied": True, "success": True, "operation": op_type, "namespace": namespace, "entity": entity}
        raise ValueError(f"Unsupported schema change operation: {op_type}")

    def extract_relationships(self, namespace: str, entity: str) -> list[dict[str, Any]]:
        inspector = inspect(self._engine)
        results = []
        for fk in inspector.get_foreign_keys(entity, schema=namespace):
            for column in fk.get("constrained_columns") or []:
                results.append(
                    {
                        "field": column,
                        "target_namespace": fk.get("referred_schema") or namespace,
                        "target_entity": fk.get("referred_table"),
                        "target_field": (fk.get("referred_columns") or [None])[0],
                        "constraint_name": fk.get("name"),
                    }
                )
        return results

    def _reflect_table(self, namespace: str, entity: str) -> Table:
        metadata = MetaData()
        try:
            return Table(entity, metadata, autoload_with=self._engine, schema=namespace)
        except NoSuchTableError as exc:
            raise ValueError(f"Entity not found: {namespace}.{entity}") from exc

    def _projection_columns(self, table: Table, projection: dict[str, Any] | None) -> list[Column[Any]]:
        if not projection:
            return list(table.c)
        include = [name for name, enabled in projection.items() if bool(enabled) and name in table.c]
        if include:
            return [table.c[name] for name in include]
        excluded = {name for name, enabled in projection.items() if not bool(enabled)}
        return [column for column in table.c if column.name not in excluded]

    def _normalise_filter_node(self, filter: Any) -> FilterNode | None:
        if filter in (None, {}, []):
            return None
        if isinstance(filter, (FilterCondition, FilterGroup)):
            return filter
        if isinstance(filter, dict):
            return parse_filter(filter)
        raise ValueError(f"Unsupported filter payload: {type(filter)!r}")

    def _build_where_clause(self, table: Table, filter: Any) -> ColumnElement[bool] | None:
        node = self._normalise_filter_node(filter)
        if node is None:
            return None
        if isinstance(node, FilterCondition):
            return self._build_condition(table, node)
        clauses = [self._build_where_clause(table, item) for item in node.conditions]
        clauses = [item for item in clauses if item is not None]
        if not clauses:
            return None
        if node.op == "and":
            return and_(*clauses)
        if node.op == "or":
            return or_(*clauses)
        if node.op == "not":
            return not_(clauses[0])
        raise ValueError(f"Unsupported filter group operator: {node.op}")

    def _build_condition(self, table: Table, condition: FilterCondition) -> ColumnElement[bool]:
        column = table.c.get(condition.field)
        if column is None:
            raise ValueError(f"Unknown column in filter: {condition.field}")
        value = condition.value
        operator = condition.operator
        if operator == "eq":
            return column == value
        if operator == "neq":
            return column != value
        if operator == "gt":
            return column > value
        if operator == "gte":
            return column >= value
        if operator == "lt":
            return column < value
        if operator == "lte":
            return column <= value
        if operator == "in":
            return column.in_(list(value or []))
        if operator == "not_in":
            return not_(column.in_(list(value or [])))
        if operator == "contains":
            return column.like(f"%{value or ''}%")
        if operator == "starts_with":
            return column.like(f"{value or ''}%")
        if operator == "ends_with":
            return column.like(f"%{value or ''}")
        if operator == "exists":
            return column.is_not(None) if bool(value) else column.is_(None)
        if operator == "not_exists":
            return column.is_(None)
        if operator == "regex":
            return column.op(self.regex_operator)(str(value or ""))
        if operator == "is_null":
            return column.is_(None)
        if operator == "is_not_null":
            return column.is_not(None)
        raise ValueError(f"Unsupported filter operator: {operator}")

    def _reload_inserted_row(
        self,
        connection,
        table: Table,
        payload: dict[str, Any],
        inserted_primary_key: Any,
    ) -> dict[str, Any] | None:
        predicate = self._primary_key_predicate(table, payload, inserted_primary_key)
        if predicate is None:
            return None
        row = connection.execute(select(table).where(predicate).limit(1)).mappings().first()
        return dict(row) if row is not None else None

    def _primary_key_predicate(self, table: Table, payload: dict[str, Any], inserted_primary_key: Any) -> ColumnElement[bool] | None:
        pk_columns = list(table.primary_key.columns)
        if not pk_columns:
            return None
        values = list(inserted_primary_key or [])
        if values and len(values) == len(pk_columns):
            return and_(*[column == value for column, value in zip(pk_columns, values)])
        if all(column.name in payload for column in pk_columns):
            return and_(*[column == payload[column.name] for column in pk_columns])
        return None

    def _inserted_id(self, table: Table, payload: dict[str, Any], inserted_primary_key: Any) -> str:
        pk_columns = list(table.primary_key.columns)
        values = list(inserted_primary_key or [])
        if values:
            return ":".join(str(value) for value in values)
        if pk_columns and all(column.name in payload for column in pk_columns):
            return ":".join(str(payload[column.name]) for column in pk_columns)
        return ""

    def _create_entity(self, connection, namespace: str, entity: str, parameters: dict[str, Any]) -> None:
        columns = dict(parameters.get("columns") or {})
        primary_key = parameters.get("primary_key")
        if isinstance(primary_key, str):
            primary_key_names = {primary_key}
        else:
            primary_key_names = {str(item) for item in list(primary_key or [])}
        table = Table(
            entity,
            MetaData(),
            *[
                Column(
                    name,
                    self._sqlalchemy_type(type_name),
                    primary_key=(name in primary_key_names),
                )
                for name, type_name in columns.items()
            ],
            schema=namespace,
        )
        table.create(bind=connection, checkfirst=True)

    def _drop_entity(self, connection, namespace: str, entity: str) -> None:
        table = self._reflect_table(namespace, entity)
        table.drop(bind=connection, checkfirst=True)

    def _create_index(self, connection, namespace: str, entity: str, parameters: dict[str, Any]) -> str:
        table = self._reflect_table(namespace, entity)
        keys = parameters.get("keys") or []
        if not keys and parameters.get("column"):
            keys = [{"field": parameters["column"], "direction": "asc"}]
        if not keys:
            raise ValueError("create_index requires at least one key")
        column_names = [str(item.get("field", "")) for item in keys]
        if not all(name in table.c for name in column_names):
            raise ValueError("create_index references unknown columns")
        index_name = str(parameters.get("name") or f"{entity}_{'_'.join(column_names)}_idx")
        unique = bool(parameters.get("unique", False))
        schema_prefix = f"{self._quote_identifier(namespace)}." if namespace else ""
        quoted_columns = ", ".join(self._quote_identifier(name) for name in column_names)
        unique_sql = "UNIQUE " if unique else ""
        connection.execute(text(f"CREATE {unique_sql}INDEX {self._quote_identifier(index_name)} ON {schema_prefix}{self._quote_identifier(entity)} ({quoted_columns})"))
        return index_name

    def _drop_index(self, connection, namespace: str, entity: str, parameters: dict[str, Any]) -> None:
        raise NotImplementedError

    def _quote_identifier(self, value: str) -> str:
        return f'"{value}"'

    def _sqlalchemy_type(self, type_name: Any):
        raw = str(type_name or "text").strip().lower()
        mapping = {
            "int": Integer,
            "integer": Integer,
            "bigint": Integer,
            "float": Float,
            "double": Float,
            "number": Float,
            "bool": Boolean,
            "boolean": Boolean,
            "date": Date,
            "datetime": DateTime,
            "timestamp": DateTime,
            "json": JSON,
            "blob": LargeBinary,
            "binary": LargeBinary,
            "bytes": LargeBinary,
            "text": Text,
            "string": String(255),
            "varchar": String(255),
        }
        return mapping.get(raw, String(255))

    def _normalise_record(self, record: dict[str, Any]) -> dict[str, Any]:
        return {key: self._normalise_value(value) for key, value in record.items()}

    def _describe_fields_via_information_schema(
        self,
        namespace: str,
        entity: str,
        pk_columns: set[str],
    ) -> list[dict[str, Any]]:
        statement = text(
            """
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema = :namespace AND table_name = :entity
            ORDER BY ordinal_position
            """
        )
        with self._engine.connect() as connection:
            rows = connection.execute(statement, {"namespace": namespace, "entity": entity}).mappings().all()
        return [
            {
                "name": str(row["column_name"]),
                "types": [str(row["data_type"])],
                "nullable": str(row["is_nullable"]).upper() == "YES",
                "default": self._normalise_value(row["column_default"]),
                "kind": "primary_key" if str(row["column_name"]) in pk_columns else "regular",
            }
            for row in rows
        ]

    def _normalise_value(self, value: Any) -> Any:
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, date):
            return value.isoformat()
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, bytes):
            return value.hex()
        if isinstance(value, dict):
            return {key: self._normalise_value(item) for key, item in value.items()}
        if isinstance(value, list):
            return [self._normalise_value(item) for item in value]
        return value


class PostgreSQLConnectorBase(RelationalConnector):
    """PostgreSQL-oriented relational connector base."""

    source_type = "postgresql"
    namespace_type = "schema"
    system_namespaces = {"information_schema", "pg_catalog", "pg_toast"}
    driver_scheme = "postgresql+psycopg"
    regex_operator = "~"

    def _drop_index(self, connection, namespace: str, entity: str, parameters: dict[str, Any]) -> None:
        _ = entity
        name = str(parameters.get("name") or "").strip()
        if not name:
            raise ValueError("drop_index requires an index name")
        schema_prefix = f"{self._quote_identifier(namespace)}." if namespace else ""
        connection.execute(text(f"DROP INDEX IF EXISTS {schema_prefix}{self._quote_identifier(name)}"))


class MariaDBConnectorBase(RelationalConnector):
    """MariaDB-oriented relational connector base."""

    source_type = "mariadb"
    namespace_type = "database"
    system_namespaces = {"information_schema", "mysql", "performance_schema", "sys"}
    driver_scheme = "mysql+pymysql"
    regex_operator = "REGEXP"

    def _quote_identifier(self, value: str) -> str:
        return f"`{value}`"

    def _drop_index(self, connection, namespace: str, entity: str, parameters: dict[str, Any]) -> None:
        name = str(parameters.get("name") or "").strip()
        if not name:
            raise ValueError("drop_index requires an index name")
        schema_prefix = f"{self._quote_identifier(namespace)}." if namespace else ""
        connection.execute(text(f"DROP INDEX {self._quote_identifier(name)} ON {schema_prefix}{self._quote_identifier(entity)}"))
