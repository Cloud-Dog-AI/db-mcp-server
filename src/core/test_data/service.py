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

import json
import os
import sqlite3
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from fastapi import Request

from cloud_dog_api_kit.errors import UnauthorisedError, ValidationError
from cloud_dog_logging import Actor, Target

_ALLOWED_RUNTIME_PROFILES = {"preprod", "local-docker"}

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
        if runtime_profile not in _ALLOWED_RUNTIME_PROFILES:
            raise UnauthorisedError(
                message=(
                    "Test data seed is only enabled when "
                    "RUNTIME_PROFILE=preprod or RUNTIME_PROFILE=local-docker"
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
            os.getenv("RUNTIME_PROFILE")
            or str(self._runtime.config.get("runtime.profile", "") or "")
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


def _sqlite_path(uri: str) -> str:
    parsed = urlparse(uri)
    if parsed.scheme not in {"sqlite", "sqlite+pysqlite"}:
        raise ValidationError(message=f"Unsupported SQLite URI: {parsed.scheme}")
    if parsed.path in {"", "/:memory:"}:
        return ":memory:"
    return parsed.path


def _seed_sqlite(uri: str) -> _SeedResult:
    path = _sqlite_path(uri)
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(
            """
            DROP TABLE IF EXISTS orders;
            DROP TABLE IF EXISTS users;
            CREATE TABLE users (
              id INTEGER PRIMARY KEY,
              email TEXT NOT NULL UNIQUE,
              display_name TEXT,
              created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX idx_users_email ON users(email);
            CREATE TABLE orders (
              id INTEGER PRIMARY KEY,
              user_id INTEGER NOT NULL REFERENCES users(id),
              amount NUMERIC NOT NULL,
              status TEXT NOT NULL,
              created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX idx_orders_user_id ON orders(user_id);
            CREATE INDEX idx_orders_status ON orders(status);
            """
        )
        connection.executemany(
            "INSERT INTO users (id, email, display_name) VALUES (?, ?, ?)",
            [(item["id"], item["email"], item["display_name"]) for item in _USERS],
        )
        connection.executemany(
            "INSERT INTO orders (id, user_id, amount, status) VALUES (?, ?, ?, ?)",
            [(item["id"], item["user_id"], item["amount"], item["status"]) for item in _ORDERS],
        )
        counts = _sqlite_counts(connection)
    return _SeedResult(target=path, counts=counts)


def _sqlite_counts(connection: sqlite3.Connection) -> dict[str, int]:
    return {
        "users": int(connection.execute("SELECT COUNT(*) FROM users").fetchone()[0]),
        "orders": int(connection.execute("SELECT COUNT(*) FROM orders").fetchone()[0]),
    }


def _seed_postgres(uri: str) -> _SeedResult:
    import psycopg

    with psycopg.connect(uri, connect_timeout=30) as connection:
        with connection.cursor() as cursor:
            cursor.execute("DROP SCHEMA IF EXISTS w28a871 CASCADE")
            cursor.execute("CREATE SCHEMA w28a871")
            cursor.execute("SET search_path TO w28a871")
            cursor.execute(
                """
                CREATE TABLE users (
                  id SERIAL PRIMARY KEY,
                  email VARCHAR(255) NOT NULL UNIQUE,
                  display_name VARCHAR(120),
                  created_at TIMESTAMPTZ DEFAULT NOW()
                )
                """
            )
            cursor.execute("CREATE INDEX idx_users_email ON users(email)")
            cursor.execute(
                """
                CREATE TABLE orders (
                  id SERIAL PRIMARY KEY,
                  user_id INTEGER NOT NULL REFERENCES users(id),
                  amount NUMERIC(10,2) NOT NULL,
                  status VARCHAR(20) NOT NULL,
                  created_at TIMESTAMPTZ DEFAULT NOW()
                )
                """
            )
            cursor.execute("CREATE INDEX idx_orders_user_id ON orders(user_id)")
            cursor.execute("CREATE INDEX idx_orders_status ON orders(status)")
            cursor.executemany(
                "INSERT INTO users (id, email, display_name) VALUES (%s, %s, %s)",
                [(item["id"], item["email"], item["display_name"]) for item in _USERS],
            )
            cursor.executemany(
                "INSERT INTO orders (id, user_id, amount, status) VALUES (%s, %s, %s, %s)",
                [(item["id"], item["user_id"], item["amount"], item["status"]) for item in _ORDERS],
            )
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = int(cursor.fetchone()[0])
            cursor.execute("SELECT COUNT(*) FROM orders")
            order_count = int(cursor.fetchone()[0])
        connection.commit()
    return _SeedResult(target="schema:w28a871", counts={"users": user_count, "orders": order_count})


def _mysql_connection_kwargs(uri: str) -> tuple[dict[str, Any], str]:
    parsed = urlparse(uri)
    if parsed.scheme not in {"mysql", "mariadb"}:
        raise ValidationError(message=f"Unsupported MySQL URI: {parsed.scheme}")
    database = parsed.path.strip("/") or "w28a871"
    return (
        {
            "host": parsed.hostname,
            "port": parsed.port or 3306,
            "user": parsed.username,
            "password": parsed.password,
            "connect_timeout": 30,
            "charset": "utf8mb4",
            "autocommit": False,
        },
        database,
    )


def _seed_mysql(uri: str) -> _SeedResult:
    import pymysql

    kwargs, database = _mysql_connection_kwargs(uri)
    if not database.replace("_", "").isalnum():
        raise ValidationError(message=f"Unsupported MySQL database name: {database}")
    connection = pymysql.connect(**kwargs)
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{database}`")
            cursor.execute(f"USE `{database}`")
            cursor.execute("DROP TABLE IF EXISTS `orders`")
            cursor.execute("DROP TABLE IF EXISTS `users`")
            cursor.execute(
                """
                CREATE TABLE users (
                  id INT AUTO_INCREMENT PRIMARY KEY,
                  email VARCHAR(255) NOT NULL UNIQUE,
                  display_name VARCHAR(120),
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )
            cursor.execute("CREATE INDEX idx_users_email ON users(email)")
            cursor.execute(
                """
                CREATE TABLE orders (
                  id INT AUTO_INCREMENT PRIMARY KEY,
                  user_id INT NOT NULL,
                  amount DECIMAL(10,2) NOT NULL,
                  status VARCHAR(20) NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  CONSTRAINT fk_orders_user_id FOREIGN KEY (user_id) REFERENCES users(id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )
            cursor.execute("CREATE INDEX idx_orders_user_id ON orders(user_id)")
            cursor.execute("CREATE INDEX idx_orders_status ON orders(status)")
            cursor.executemany(
                "INSERT INTO users (id, email, display_name) VALUES (%s, %s, %s)",
                [(item["id"], item["email"], item["display_name"]) for item in _USERS],
            )
            cursor.executemany(
                "INSERT INTO orders (id, user_id, amount, status) VALUES (%s, %s, %s, %s)",
                [(item["id"], item["user_id"], item["amount"], item["status"]) for item in _ORDERS],
            )
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = int(cursor.fetchone()[0])
            cursor.execute("SELECT COUNT(*) FROM orders")
            order_count = int(cursor.fetchone()[0])
        connection.commit()
    finally:
        connection.close()
    return _SeedResult(target=f"database:{database}", counts={"users": user_count, "orders": order_count})


def _mongodb_database(uri: str) -> str:
    parsed = urlparse(uri)
    return parsed.path.strip("/") or "w28a871"


def _seed_mongodb(uri: str) -> _SeedResult:
    from pymongo import MongoClient

    database = _mongodb_database(uri)
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    try:
        db = client[database]
        db.users.drop()
        db.orders.drop()
        db.users.insert_many(
            [
                {
                    "_id": item["id"],
                    "id": item["id"],
                    "email": item["email"],
                    "display_name": item["display_name"],
                }
                for item in _USERS
            ]
        )
        db.orders.insert_many(
            [
                {
                    "_id": item["id"],
                    "id": item["id"],
                    "user_id": item["user_id"],
                    "amount": item["amount"],
                    "status": item["status"],
                }
                for item in _ORDERS
            ]
        )
        db.users.create_index("email", name="idx_users_email", unique=True)
        db.orders.create_index("user_id", name="idx_orders_user_id")
        db.orders.create_index("status", name="idx_orders_status")
        counts = {
            "users": int(db.users.count_documents({})),
            "orders": int(db.orders.count_documents({})),
        }
    finally:
        client.close()
    return _SeedResult(target=f"database:{database}", counts=counts)


def _seed_elasticsearch(uri: str) -> _SeedResult:
    import requests

    base_url = uri.rstrip("/")
    session = requests.Session()
    try:
        users_index = "w28a871-users"
        orders_index = "w28a871-orders"
        for index in (users_index, orders_index):
            session.delete(f"{base_url}/{index}", timeout=30)
        session.put(
            f"{base_url}/{users_index}",
            json={
                "settings": {"number_of_replicas": 0},
                "mappings": {
                    "properties": {
                        "id": {"type": "integer"},
                        "email": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                        "display_name": {"type": "text"},
                        "created_at": {"type": "date", "format": "strict_date_optional_time"},
                    }
                },
            },
            timeout=30,
        ).raise_for_status()
        session.put(
            f"{base_url}/{orders_index}",
            json={
                "settings": {"number_of_replicas": 0},
                "mappings": {
                    "properties": {
                        "id": {"type": "integer"},
                        "user_id": {"type": "integer"},
                        "amount": {"type": "double"},
                        "status": {"type": "keyword"},
                        "created_at": {"type": "date", "format": "strict_date_optional_time"},
                    }
                },
            },
            timeout=30,
        ).raise_for_status()
        lines = []
        for item in _USERS:
            lines.append(json.dumps({"index": {"_index": users_index, "_id": item["id"]}}))
            lines.append(json.dumps(item))
        for item in _ORDERS:
            lines.append(json.dumps({"index": {"_index": orders_index, "_id": item["id"]}}))
            lines.append(json.dumps(item))
        session.post(
            f"{base_url}/_bulk",
            data="\n".join(lines) + "\n",
            headers={"Content-Type": "application/x-ndjson"},
            timeout=60,
        ).raise_for_status()
        session.post(f"{base_url}/_refresh", timeout=30).raise_for_status()
    finally:
        session.close()
    return _SeedResult(
        target="indices:w28a871-users,w28a871-orders",
        counts={"users": len(_USERS), "orders": len(_ORDERS)},
    )
