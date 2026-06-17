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
# Description: Verification tests for canonical connector seed data.
# Related requirements: W28A-274-K deliverables 2, 6, 8, 9
# Related tests: scripts/seed-test-data.sh

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest
from pymongo import MongoClient

from tests.fixtures.canonical_data import dataset_counts

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MONGODB_COMPOSE_FILE = PROJECT_ROOT / "docker" / "docker-compose.mongodb.yml"
SEED_SCRIPT = PROJECT_ROOT / "scripts" / "seed-test-data.sh"

pytestmark = [pytest.mark.db, pytest.mark.system]


@pytest.fixture(scope="module")
def seeded_mongodb() -> MongoClient:
    env = os.environ.copy()
    env.setdefault("DB_MCP_TEST_MONGODB_URI", "mongodb://127.0.0.1:27018")
    env.setdefault("DB_MCP_TEST_MONGODB_DB", "dbmcp_ecommerce")
    subprocess.run([str(SEED_SCRIPT), "mongodb"], cwd=PROJECT_ROOT, env=env, check=True)
    client = MongoClient(env["DB_MCP_TEST_MONGODB_URI"], serverSelectionTimeoutMS=5000)
    try:
        client.admin.command("ping")
        yield client
    finally:
        client.close()
        subprocess.run(
            ["docker", "compose", "-f", str(MONGODB_COMPOSE_FILE), "down", "-v"],
            cwd=PROJECT_ROOT,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-012")


def test_seed_counts_match_canonical_dataset(seeded_mongodb: MongoClient) -> None:
    db_name = os.environ.get("DB_MCP_TEST_MONGODB_DB", "dbmcp_ecommerce")
    database = seeded_mongodb[db_name]
    for entity, expected_count in dataset_counts().items():
        assert database[entity].count_documents({}) == expected_count
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-012")


def test_cross_collection_references_resolve(seeded_mongodb: MongoClient) -> None:
    db_name = os.environ.get("DB_MCP_TEST_MONGODB_DB", "dbmcp_ecommerce")
    database = seeded_mongodb[db_name]

    customer_ids = {item["_id"] for item in database.customers.find({}, {"_id": 1})}
    order_ids = {item["_id"] for item in database.orders.find({}, {"_id": 1})}
    product_ids = {item["_id"] for item in database.products.find({}, {"_id": 1})}
    supplier_ids = {item["_id"] for item in database.suppliers.find({}, {"_id": 1})}

    assert customer_ids
    assert order_ids
    assert product_ids
    assert supplier_ids

    for order in database.orders.find({}, {"customer_id": 1, "product_id": 1}):
        assert order["customer_id"] in customer_ids
        assert order["product_id"] in product_ids

    for invoice in database.invoices.find({}, {"customer_id": 1, "order_id": 1}):
        assert invoice["customer_id"] in customer_ids
        assert invoice["order_id"] in order_ids

    for product in database.products.find({}, {"supplier_id": 1}):
        assert product["supplier_id"] in supplier_ids
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-012")


def test_field_types_and_nullability_are_preserved(seeded_mongodb: MongoClient) -> None:
    db_name = os.environ.get("DB_MCP_TEST_MONGODB_DB", "dbmcp_ecommerce")
    database = seeded_mongodb[db_name]

    product = database.products.find_one({"description": None})
    assert product is not None
    assert isinstance(product["tags"], list)
    assert all(isinstance(tag, str) for tag in product["tags"])
    assert isinstance(product["price"], float)
    assert isinstance(product["stock"], int)

    supplier = database.suppliers.find_one({"contact_email": None})
    assert supplier is not None
    assert isinstance(supplier["active"], bool)

    invoice = database.invoices.find_one({"paid_date": None})
    assert invoice is not None
    assert isinstance(invoice["amount"], float)
    assert isinstance(invoice["tax"], float)
