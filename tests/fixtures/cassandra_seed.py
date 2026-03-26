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
# Description: Cassandra seed module for the canonical connector test dataset.
# Related requirements: W28A-274-K deliverables 5, 8

"""Cassandra seed utilities for the canonical connector dataset."""

from __future__ import annotations

import os
from typing import Any

from tests.fixtures.canonical_data import clone_canonical_dataset

DEFAULT_CASSANDRA_HOST = os.getenv("DB_MCP_TEST_CASSANDRA_HOST", "127.0.0.1")
DEFAULT_CASSANDRA_PORT = int(os.getenv("DB_MCP_TEST_CASSANDRA_PORT", "9042"))
DEFAULT_CASSANDRA_KEYSPACE = os.getenv("DB_MCP_TEST_CASSANDRA_KEYSPACE", "dbmcp_ecommerce")
DEFAULT_CASSANDRA_USERNAME = os.getenv("DB_MCP_TEST_CASSANDRA_USERNAME", "cassandra")
DEFAULT_CASSANDRA_PASSWORD = os.getenv("DB_MCP_TEST_CASSANDRA_PASSWORD", "cassandra")

TABLE_SCHEMAS = {
    "customers": """
        CREATE TABLE IF NOT EXISTS customers (
            id text PRIMARY KEY,
            name text,
            email text,
            country text,
            industry text,
            status text,
            tier text,
            created_at date,
            updated_at date
        )
    """,
    "orders": """
        CREATE TABLE IF NOT EXISTS orders (
            id text PRIMARY KEY,
            customer_id text,
            product_id text,
            quantity int,
            unit_price double,
            total double,
            status text,
            order_date date,
            ship_date date
        )
    """,
    "products": """
        CREATE TABLE IF NOT EXISTS products (
            id text PRIMARY KEY,
            name text,
            category text,
            subcategory text,
            price double,
            stock int,
            supplier_id text,
            description text,
            tags list<text>
        )
    """,
    "suppliers": """
        CREATE TABLE IF NOT EXISTS suppliers (
            id text PRIMARY KEY,
            name text,
            country text,
            rating double,
            contact_email text,
            active boolean
        )
    """,
    "invoices": """
        CREATE TABLE IF NOT EXISTS invoices (
            id text PRIMARY KEY,
            order_id text,
            customer_id text,
            amount double,
            tax double,
            total double,
            status text,
            issued_date date,
            due_date date,
            paid_date date
        )
    """,
}


def _cql_literal(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        return "[" + ", ".join(_cql_literal(item) for item in value) + "]"
    return "'" + str(value).replace("'", "''") + "'"


def build_cassandra_cql(*, keyspace: str = DEFAULT_CASSANDRA_KEYSPACE) -> str:
    """Build the full Cassandra schema and insert script."""
    dataset = clone_canonical_dataset()
    statements = [
        f"DROP KEYSPACE IF EXISTS {keyspace};",
        f"CREATE KEYSPACE {keyspace} WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': 1}};",
        f"USE {keyspace};",
    ]
    for table, ddl in TABLE_SCHEMAS.items():
        statements.append(ddl.strip() + ";")
        for row in dataset[table]:
            mapped = {"id" if k == "_id" else k: v for k, v in row.items()}
            columns = ", ".join(mapped.keys())
            values = ", ".join(_cql_literal(value) for value in mapped.values())
            statements.append(f"INSERT INTO {table} ({columns}) VALUES ({values});")
    return "\n".join(statements) + "\n"


def seed_cassandra(*, keyspace: str = DEFAULT_CASSANDRA_KEYSPACE) -> str:
    """Seed Cassandra by executing generated CQL statements over the native protocol."""
    from cassandra.auth import PlainTextAuthProvider
    from cassandra.cluster import Cluster

    auth_provider: PlainTextAuthProvider | None = None
    if DEFAULT_CASSANDRA_USERNAME:
        auth_provider = PlainTextAuthProvider(
            username=DEFAULT_CASSANDRA_USERNAME,
            password=DEFAULT_CASSANDRA_PASSWORD,
        )
    cluster = Cluster(
        [DEFAULT_CASSANDRA_HOST],
        port=DEFAULT_CASSANDRA_PORT,
        auth_provider=auth_provider,
        connect_timeout=30,
    )
    session = cluster.connect()
    try:
        cql = build_cassandra_cql(keyspace=keyspace)
        for statement in cql.split(";"):
            sql = statement.strip()
            if not sql:
                continue
            if sql.upper().startswith("USE "):
                session.set_keyspace(sql.split()[-1])
                continue
            session.execute(sql)
        return keyspace
    finally:
        session.shutdown()
        cluster.shutdown()


if __name__ == "__main__":
    seeded = seed_cassandra()
    print(f"Cassandra seed completed for keyspace: {seeded}")
