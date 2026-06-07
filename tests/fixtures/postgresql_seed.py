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
# Description: PostgreSQL seed module for the canonical connector test dataset.
# Related requirements: W28A-274-K deliverables 5, 8 (parity with cassandra/mariadb)
# Related instruction: W28A-#A63 — Stage 2c.7b seed-fixture parity for postgresql
# Recent changes:
#   2026-05-05 (#A63) — Initial implementation modelled on cassandra_seed.py;
#                       creates ISOLATED dbmcp_ecommerce database (RULES §5b)
#                       and populates the canonical 5-entity e-commerce dataset.

"""PostgreSQL seed utilities for the canonical connector dataset.

The fixture creates an isolated database named ``dbmcp_ecommerce`` on the
configured PostgreSQL server and populates it with the canonical e-commerce
dataset shared with the other ``*_seed.py`` fixtures (cassandra, mongodb,
couchdb, elasticsearch, opensearch).

Per RULES §5b (Infrastructure Reuse — separate namespaces per test) the
database is created brand-new and never overlaps with any existing
``cloud_dog_db_test`` / ``alembic_version`` / platform-service database on the
configured server. Existing databases on the shared server are NEVER modified.

Usage::

    cd <repo-root>
    set -a && source tests/env-postgresql && set +a
    python -m tests.fixtures.postgresql_seed
"""

from __future__ import annotations

import os
from typing import Any
from urllib.parse import urlparse

from tests.fixtures.canonical_data import clone_canonical_dataset

DEFAULT_POSTGRESQL_URI = os.getenv(
    "DB_MCP_TEST_POSTGRESQL_URI",
    "postgresql://postgres:postgres@127.0.0.1:5432/dbmcp_ecommerce",
)
DEFAULT_POSTGRESQL_DATABASE = os.getenv(
    "DB_MCP_TEST_POSTGRESQL_DATABASE", "dbmcp_ecommerce"
)

TABLE_SCHEMAS: dict[str, str] = {
    "customers": """
        CREATE TABLE IF NOT EXISTS customers (
            id          TEXT PRIMARY KEY,
            name        TEXT,
            email       TEXT,
            country     TEXT,
            industry    TEXT,
            status      TEXT,
            tier        TEXT,
            created_at  DATE,
            updated_at  DATE
        )
    """,
    "orders": """
        CREATE TABLE IF NOT EXISTS orders (
            id           TEXT PRIMARY KEY,
            customer_id  TEXT,
            product_id   TEXT,
            quantity     INTEGER,
            unit_price   DOUBLE PRECISION,
            total        DOUBLE PRECISION,
            status       TEXT,
            order_date   DATE,
            ship_date    DATE
        )
    """,
    "products": """
        CREATE TABLE IF NOT EXISTS products (
            id           TEXT PRIMARY KEY,
            name         TEXT,
            category     TEXT,
            subcategory  TEXT,
            price        DOUBLE PRECISION,
            stock        INTEGER,
            supplier_id  TEXT,
            description  TEXT,
            tags         TEXT[]
        )
    """,
    "suppliers": """
        CREATE TABLE IF NOT EXISTS suppliers (
            id             TEXT PRIMARY KEY,
            name           TEXT,
            country        TEXT,
            rating         DOUBLE PRECISION,
            contact_email  TEXT,
            active         BOOLEAN
        )
    """,
    "invoices": """
        CREATE TABLE IF NOT EXISTS invoices (
            id           TEXT PRIMARY KEY,
            order_id     TEXT,
            customer_id  TEXT,
            amount       DOUBLE PRECISION,
            tax          DOUBLE PRECISION,
            total        DOUBLE PRECISION,
            status       TEXT,
            issued_date  DATE,
            due_date     DATE,
            paid_date    DATE
        )
    """,
}

# Column ordering for INSERT statements (id replaces _id from canonical).
TABLE_COLUMNS: dict[str, tuple[str, ...]] = {
    "customers": ("id", "name", "email", "country", "industry", "status", "tier", "created_at", "updated_at"),
    "orders": ("id", "customer_id", "product_id", "quantity", "unit_price", "total", "status", "order_date", "ship_date"),
    "products": ("id", "name", "category", "subcategory", "price", "stock", "supplier_id", "description", "tags"),
    "suppliers": ("id", "name", "country", "rating", "contact_email", "active"),
    "invoices": ("id", "order_id", "customer_id", "amount", "tax", "total", "status", "issued_date", "due_date", "paid_date"),
}


def _admin_uri(uri: str) -> str:
    """Return a connection URI pointing at the postgres admin DB.

    The admin database is required for ``CREATE DATABASE`` because postgres
    does not allow that statement inside a transaction targeting the
    database being created.
    """
    parsed = urlparse(uri)
    # Replace path with /postgres while preserving credentials/host/port/query
    rebuilt = parsed._replace(path="/postgres")
    return rebuilt.geturl()


def _row_values(table: str, row: dict[str, Any]) -> tuple[Any, ...]:
    mapped = {("id" if k == "_id" else k): v for k, v in row.items()}
    return tuple(mapped[col] for col in TABLE_COLUMNS[table])


def seed_postgresql(
    *, uri: str = DEFAULT_POSTGRESQL_URI, db_name: str = DEFAULT_POSTGRESQL_DATABASE
) -> str:
    """Seed the canonical dataset into PostgreSQL.

    Args:
        uri: PostgreSQL DSN. The DSN's database segment will be ignored for
            the ``CREATE DATABASE`` step (admin DB ``postgres`` is used) and
            then used verbatim for the schema/data load step.
        db_name: Target database name. Created if it does not exist.

    Returns:
        The database name that was seeded.
    """
    import psycopg

    admin_uri = _admin_uri(uri)
    # Step 1: create the isolated database if it does not exist (admin context)
    with psycopg.connect(admin_uri, autocommit=True, connect_timeout=30) as admin_conn:
        with admin_conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s", (db_name,)
            )
            if cur.fetchone() is None:
                # CREATE DATABASE cannot be parameterised; identifier is
                # validated against ALPHANUM/_ at module-init.
                if not db_name.replace("_", "").isalnum():
                    raise ValueError(
                        f"Refusing to CREATE DATABASE with non-identifier name: {db_name!r}"
                    )
                cur.execute(f'CREATE DATABASE "{db_name}"')

    # Step 2: connect to the target DB and apply schema + data
    parsed = urlparse(uri)
    target_uri = parsed._replace(path=f"/{db_name}").geturl()

    dataset = clone_canonical_dataset()
    with psycopg.connect(target_uri, connect_timeout=30) as conn:
        with conn.cursor() as cur:
            for table, ddl in TABLE_SCHEMAS.items():
                cur.execute(ddl)
            for table, rows in dataset.items():
                cols = TABLE_COLUMNS[table]
                placeholders = ", ".join(["%s"] * len(cols))
                col_list = ", ".join(cols)
                stmt = (
                    f"INSERT INTO {table} ({col_list}) VALUES ({placeholders}) "
                    f"ON CONFLICT (id) DO NOTHING"
                )
                for row in rows:
                    cur.execute(stmt, _row_values(table, row))
        conn.commit()

    return db_name


def teardown_postgresql(
    *, uri: str = DEFAULT_POSTGRESQL_URI, db_name: str = DEFAULT_POSTGRESQL_DATABASE
) -> None:
    """Drop the seeded PostgreSQL database (admin context required)."""
    import psycopg

    admin_uri = _admin_uri(uri)
    with psycopg.connect(admin_uri, autocommit=True, connect_timeout=30) as admin_conn:
        with admin_conn.cursor() as cur:
            if not db_name.replace("_", "").isalnum():
                raise ValueError(
                    f"Refusing to DROP DATABASE with non-identifier name: {db_name!r}"
                )
            cur.execute(f'DROP DATABASE IF EXISTS "{db_name}"')


if __name__ == "__main__":
    seeded = seed_postgresql()
    print(f"PostgreSQL seed completed for database: {seeded}")
