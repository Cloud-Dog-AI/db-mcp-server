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
# Description: MariaDB / MySQL seed module for the canonical connector test dataset.
# Related requirements: W28A-274-K deliverables 5, 8 (parity with cassandra/postgresql)
# Related instruction: W28A-#A63 — Stage 2c.7b seed-fixture parity for mariadb
# Recent changes:
#   2026-05-05 (#A63) — Initial implementation modelled on cassandra_seed.py +
#                       postgresql_seed.py; creates ISOLATED dbmcp_ecommerce
#                       database (RULES §5b) and populates the canonical
#                       5-entity e-commerce dataset.

"""MariaDB / MySQL seed utilities for the canonical connector dataset.

The fixture creates an isolated database named ``dbmcp_ecommerce`` on the
configured MariaDB / MySQL server and populates it with the canonical
e-commerce dataset shared with the other ``*_seed.py`` fixtures.

Per RULES §5b (Infrastructure Reuse — separate namespaces per test) the
database is created brand-new and never overlaps with any of the existing
~36 platform-service databases on db1 (chatclient, expertagent, filemcp,
gitmcp, imapmcp, indexretrievermcp, notificationagent, sqlagent, etc.).
Existing databases on the shared server are NEVER modified.

Tags are stored as a JSON array column because MariaDB does not provide a
native list/array type; the canonical dataset's ``tags`` field is a list of
strings. JSON serialisation preserves round-trip via ``json.dumps`` /
``JSON_EXTRACT``.

Usage::

    cd /opt/iac/Development/cloud-dog-ai/db-mcp-server
    set -a && source tests/env-mariadb && set +a
    python -m tests.fixtures.mariadb_seed
"""

from __future__ import annotations

import json
import os
from typing import Any
from urllib.parse import urlparse

from tests.fixtures.canonical_data import clone_canonical_dataset

DEFAULT_MARIADB_URI = os.getenv(
    "DB_MCP_TEST_MARIADB_URI",
    "mysql://root:root@127.0.0.1:3306/dbmcp_ecommerce",
)
DEFAULT_MARIADB_DATABASE = os.getenv(
    "DB_MCP_TEST_MARIADB_DATABASE", "dbmcp_ecommerce"
)

TABLE_SCHEMAS: dict[str, str] = {
    "customers": """
        CREATE TABLE IF NOT EXISTS customers (
            id          VARCHAR(64) PRIMARY KEY,
            name        VARCHAR(255),
            email       VARCHAR(255),
            country     VARCHAR(64),
            industry    VARCHAR(64),
            status      VARCHAR(32),
            tier        VARCHAR(32),
            created_at  DATE,
            updated_at  DATE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    "orders": """
        CREATE TABLE IF NOT EXISTS orders (
            id           VARCHAR(64) PRIMARY KEY,
            customer_id  VARCHAR(64),
            product_id   VARCHAR(64),
            quantity     INT,
            unit_price   DOUBLE,
            total        DOUBLE,
            status       VARCHAR(32),
            order_date   DATE,
            ship_date    DATE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    "products": """
        CREATE TABLE IF NOT EXISTS products (
            id           VARCHAR(64) PRIMARY KEY,
            name         VARCHAR(255),
            category     VARCHAR(64),
            subcategory  VARCHAR(64),
            price        DOUBLE,
            stock        INT,
            supplier_id  VARCHAR(64),
            description  TEXT,
            tags         JSON
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    "suppliers": """
        CREATE TABLE IF NOT EXISTS suppliers (
            id             VARCHAR(64) PRIMARY KEY,
            name           VARCHAR(255),
            country        VARCHAR(64),
            rating         DOUBLE,
            contact_email  VARCHAR(255),
            active         TINYINT(1)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    "invoices": """
        CREATE TABLE IF NOT EXISTS invoices (
            id           VARCHAR(64) PRIMARY KEY,
            order_id     VARCHAR(64),
            customer_id  VARCHAR(64),
            amount       DOUBLE,
            tax          DOUBLE,
            total        DOUBLE,
            status       VARCHAR(32),
            issued_date  DATE,
            due_date     DATE,
            paid_date    DATE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
}

TABLE_COLUMNS: dict[str, tuple[str, ...]] = {
    "customers": ("id", "name", "email", "country", "industry", "status", "tier", "created_at", "updated_at"),
    "orders": ("id", "customer_id", "product_id", "quantity", "unit_price", "total", "status", "order_date", "ship_date"),
    "products": ("id", "name", "category", "subcategory", "price", "stock", "supplier_id", "description", "tags"),
    "suppliers": ("id", "name", "country", "rating", "contact_email", "active"),
    "invoices": ("id", "order_id", "customer_id", "amount", "tax", "total", "status", "issued_date", "due_date", "paid_date"),
}


def _parse_uri(uri: str) -> dict[str, Any]:
    """Parse a ``mysql://...`` DSN into pymysql kwargs.

    Returns dict suitable for ``pymysql.connect(**kwargs)``.
    """
    parsed = urlparse(uri)
    if parsed.scheme not in {"mysql", "mariadb"}:
        raise ValueError(f"Unsupported scheme {parsed.scheme!r} for mariadb seed")
    return {
        "host": parsed.hostname,
        "port": parsed.port or 3306,
        "user": parsed.username,
        "password": parsed.password,
        "connect_timeout": 30,
        "charset": "utf8mb4",
    }


def _row_values(table: str, row: dict[str, Any]) -> tuple[Any, ...]:
    mapped = {("id" if k == "_id" else k): v for k, v in row.items()}
    out: list[Any] = []
    for col in TABLE_COLUMNS[table]:
        value = mapped[col]
        # MariaDB JSON column wants a JSON-encoded string; lists from
        # canonical_data.py become JSON arrays.
        if isinstance(value, list):
            value = json.dumps(value)
        out.append(value)
    return tuple(out)


def seed_mariadb(
    *, uri: str = DEFAULT_MARIADB_URI, db_name: str = DEFAULT_MARIADB_DATABASE
) -> str:
    """Seed the canonical dataset into MariaDB / MySQL.

    Args:
        uri: MariaDB / MySQL DSN. The database segment is ignored for the
            ``CREATE DATABASE`` step and then used verbatim for the
            schema/data load.
        db_name: Target database name. Created if it does not exist.

    Returns:
        The database name that was seeded.
    """
    import pymysql

    if not db_name.replace("_", "").isalnum():
        raise ValueError(
            f"Refusing to CREATE DATABASE with non-identifier name: {db_name!r}"
        )

    base_kwargs = _parse_uri(uri)

    # Step 1: create database if not exists (no DB selected on this connection)
    admin_conn = pymysql.connect(**base_kwargs)
    try:
        with admin_conn.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
                f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        admin_conn.commit()
    finally:
        admin_conn.close()

    # Step 2: connect with target DB selected; apply schema + data
    target_kwargs = dict(base_kwargs, database=db_name)
    dataset = clone_canonical_dataset()
    target_conn = pymysql.connect(**target_kwargs)
    try:
        with target_conn.cursor() as cur:
            for table, ddl in TABLE_SCHEMAS.items():
                cur.execute(ddl)
            for table, rows in dataset.items():
                cols = TABLE_COLUMNS[table]
                placeholders = ", ".join(["%s"] * len(cols))
                col_list = ", ".join(f"`{c}`" for c in cols)
                # MariaDB equivalent of "ON CONFLICT DO NOTHING" =
                # INSERT IGNORE — preserves existing rows on rerun.
                stmt = (
                    f"INSERT IGNORE INTO `{table}` ({col_list}) "
                    f"VALUES ({placeholders})"
                )
                for row in rows:
                    cur.execute(stmt, _row_values(table, row))
        target_conn.commit()
    finally:
        target_conn.close()

    return db_name


def teardown_mariadb(
    *, uri: str = DEFAULT_MARIADB_URI, db_name: str = DEFAULT_MARIADB_DATABASE
) -> None:
    """Drop the seeded MariaDB database."""
    import pymysql

    if not db_name.replace("_", "").isalnum():
        raise ValueError(
            f"Refusing to DROP DATABASE with non-identifier name: {db_name!r}"
        )

    base_kwargs = _parse_uri(uri)
    conn = pymysql.connect(**base_kwargs)
    try:
        with conn.cursor() as cur:
            cur.execute(f"DROP DATABASE IF EXISTS `{db_name}`")
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    seeded = seed_mariadb()
    print(f"MariaDB seed completed for database: {seeded}")
