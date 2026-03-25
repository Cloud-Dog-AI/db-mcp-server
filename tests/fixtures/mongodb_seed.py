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
# Description: MongoDB seed module for the canonical connector test dataset.
# Related requirements: W28A-274-K deliverables 2, 8
# Related tests: tests/fixtures/test_seed_data.py, ST1.4, ST1.5, ST1.6

"""MongoDB seed utilities for the canonical connector dataset."""

from __future__ import annotations

import os
from typing import Any

from pymongo import MongoClient

from tests.fixtures.canonical_data import clone_canonical_dataset

DEFAULT_MONGODB_URI = os.getenv("DB_MCP_TEST_MONGODB_URI", os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27018"))
DEFAULT_MONGODB_DB = os.getenv("DB_MCP_TEST_MONGODB_DB", os.getenv("MONGODB_DB", "dbmcp_ecommerce"))

INDEX_DEFINITIONS: dict[str, list[tuple[list[tuple[str, int]], str]]] = {
    "customers": [([("country", 1)], "customers_country")],
    "orders": [([("customer_id", 1)], "orders_customer_id"), ([("product_id", 1)], "orders_product_id")],
    "products": [([("supplier_id", 1)], "products_supplier_id")],
    "invoices": [([("order_id", 1)], "invoices_order_id"), ([("customer_id", 1)], "invoices_customer_id")],
}


def clone_seed_collections() -> dict[str, list[dict[str, Any]]]:
    """Return a deep copy of the canonical Mongo seed collections."""
    return clone_canonical_dataset()


SEED_COLLECTIONS = clone_seed_collections()


def seed_mongodb(*, uri: str = DEFAULT_MONGODB_URI, db_name: str = DEFAULT_MONGODB_DB) -> str:
    """Seed the canonical dataset into MongoDB."""
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    try:
        client.drop_database(db_name)
        db = client[db_name]
        for name, documents in clone_seed_collections().items():
            db[name].insert_many(documents)
            for spec, index_name in INDEX_DEFINITIONS.get(name, []):
                db[name].create_index(spec, name=index_name)
        return db_name
    finally:
        client.close()


def teardown_mongodb(*, uri: str = DEFAULT_MONGODB_URI, db_name: str = DEFAULT_MONGODB_DB) -> None:
    """Drop the seeded MongoDB database."""
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    try:
        client.drop_database(db_name)
    finally:
        client.close()


if __name__ == "__main__":
    seeded = seed_mongodb()
    print(f"MongoDB seed completed for database: {seeded}")
