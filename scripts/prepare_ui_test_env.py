#!/usr/bin/env python3
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

"""Prepare deterministic db-mcp-server state for WebUI E2E runs."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

import httpx
from pymongo import MongoClient

from src.common.config_loader import load_runtime_config

ROOT = Path(__file__).resolve().parents[1]


def _runtime_config():
    env_file = os.environ.get("DB_MCP_SERVER_ENV_FILE", "tests/env-AT")
    return load_runtime_config([env_file])


def _loopback_host(host: str | None) -> str:
    resolved = str(host or "").strip()
    if resolved in {"", "0.0.0.0", "::"}:
        return "127.0.0.1"
    return resolved


def _base_url(env_var: str, surface: str) -> str:
    override = os.environ.get(env_var)
    if override:
        return override.rstrip("/")
    config = _runtime_config()
    return (
        f"http://{_loopback_host(config.get(f'{surface}_server.host'))}:"
        f"{int(config.get(f'{surface}_server.port'))}"
    )


API_BASE_URL = _base_url("DB_MCP_UI_API_BASE_URL", "api")
MCP_BASE_URL = _base_url("DB_MCP_UI_MCP_BASE_URL", "mcp")
API_KEY = os.environ.get("DB_MCP_UI_API_KEY", "test-api-key")
PROFILE_NAME = os.environ.get("DB_MCP_UI_PROFILE_NAME", "ui-e2e-profile")
NAMESPACE = os.environ.get("DB_MCP_UI_NAMESPACE", "dbmcp_ui_e2e")
HEADERS = {"X-API-Key": API_KEY}
def ensure_real_mongodb() -> str:
    """Use the configured shared MongoDB; local backend containers are forbidden."""
    mongo_uri = str(
        os.environ.get("DB_MCP_TEST_MONGODB_URI")
        or _runtime_config().get("connectors.mongodb.default_uri")
        or ""
    ).strip()
    if not mongo_uri:
        raise RuntimeError("Shared MongoDB URI is not configured for the WebUI test tier")
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    try:
        client.admin.command("ping")
    except Exception as exc:
        raise RuntimeError("Configured shared MongoDB is not reachable") from exc
    finally:
        client.close()
    return mongo_uri


def seed_mongodb(*, uri: str, db_name: str) -> str:
    customers: list[dict[str, Any]] = []
    customer_countries = ["UK", "US", "DE", "FR", "NL"]
    industries = ["manufacturing", "technology", "logistics", "finance", "retail"]
    statuses = ["active", "active", "active", "inactive"]
    for index in range(1, 21):
        customers.append({
            "_id": f"C{index:03d}",
            "name": f"Customer {index:02d}",
            "email": f"customer{index:02d}@example.com",
            "country": customer_countries[(index - 1) % len(customer_countries)],
            "industry": industries[(index - 1) % len(industries)],
            "status": statuses[(index - 1) % len(statuses)],
            "created_at": f"2025-{((index - 1) % 12) + 1:02d}-{((index - 1) % 27) + 1:02d}",
        })

    suppliers = []
    supplier_countries = ["DE", "CN", "PL", "US", "GB"]
    for index in range(1, 11):
        suppliers.append({
            "_id": f"S{index:03d}",
            "name": f"Supplier {index:02d}",
            "country": supplier_countries[(index - 1) % len(supplier_countries)],
            "rating": round(3.5 + ((index - 1) % 5) * 0.3, 1),
        })

    products = []
    categories = ["hardware", "software", "services"]
    for index in range(1, 16):
        products.append({
            "_id": f"P{index:03d}",
            "name": f"Product {index:02d}",
            "category": categories[(index - 1) % len(categories)],
            "price": round(10 + index * 2.75, 2),
            "stock": 100 + index * 25,
            "supplier_id": suppliers[(index - 1) % len(suppliers)]["_id"],
        })

    orders = []
    order_statuses = ["draft", "confirmed", "shipped", "cancelled"]
    for index in range(1, 51):
        customer = customers[(index - 1) % len(customers)]
        product = products[(index - 1) % len(products)]
        quantity = ((index - 1) % 7 + 1) * 10
        orders.append({
            "_id": f"O{index:03d}",
            "customer_id": customer["_id"],
            "product_id": product["_id"],
            "product": product["name"],
            "quantity": quantity,
            "price": product["price"],
            "status": order_statuses[(index - 1) % len(order_statuses)],
            "order_date": f"2026-{((index - 1) % 12) + 1:02d}-{((index - 1) % 27) + 1:02d}",
        })

    invoices = []
    invoice_statuses = ["paid", "due", "overdue"]
    for index in range(1, 31):
        order = orders[index - 1]
        invoices.append({
            "_id": f"I{index:03d}",
            "order_id": order["_id"],
            "customer_id": order["customer_id"],
            "amount": round(order["quantity"] * order["price"], 2),
            "status": invoice_statuses[(index - 1) % len(invoice_statuses)],
            "due_date": f"2026-{((index + 1) % 12) + 1:02d}-{((index - 1) % 27) + 1:02d}",
        })

    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    try:
        db = client[db_name]
        db.client.drop_database(db_name)
        for name, documents in {
            "customers": customers,
            "orders": orders,
            "products": products,
            "suppliers": suppliers,
            "invoices": invoices,
        }.items():
            db[name].insert_many(documents)
        db["orders"].create_index([("customer_id", 1)], name="orders_customer_id")
        db["orders"].create_index([("product_id", 1)], name="orders_product_id")
        db["invoices"].create_index([("order_id", 1)], name="invoices_order_id")
        db["products"].create_index([("supplier_id", 1)], name="products_supplier_id")
        return db_name
    finally:
        client.close()


def wait_for(url: str, timeout_seconds: int = 60) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            response = httpx.get(url, timeout=5.0)
            if response.status_code == 200:
                return
        except httpx.HTTPError:
            pass
        time.sleep(1)
    raise RuntimeError(f"Timed out waiting for {url}")


def call(method: str, url: str, **kwargs):
    response = httpx.request(method, url, headers=HEADERS, timeout=30.0, **kwargs)
    response.raise_for_status()
    return response.json().get("data")


def main() -> None:
    mongo_uri = ensure_real_mongodb()
    seed_mongodb(uri=mongo_uri, db_name=NAMESPACE)

    wait_for(f"{API_BASE_URL}/health")
    wait_for(f"{MCP_BASE_URL}/health")

    profiles = call("GET", f"{API_BASE_URL}/v1/profiles")
    for item in profiles:
        if item.get("name") == PROFILE_NAME:
            call("DELETE", f"{API_BASE_URL}/v1/profiles/{item['profile_id']}")

    payload = {
        "name": PROFILE_NAME,
        "source_type": "mongodb",
        "source_connection": mongo_uri,
        "description": "Deterministic WebUI E2E profile.",
        "namespaces": [NAMESPACE],
        "entities": ["customers", "orders", "products", "suppliers", "invoices"],
        "enabled_tools": [
            "catalog.list_namespaces", "catalog.list_entities", "catalog.get_entity",
            "schema.describe_entity", "schema.describe_fields", "schema.list_indexes",
            "schema.sample_shapes", "schema.change.plan", "schema.change.apply",
            "data.read", "data.count", "search.metadata", "search.content",
            "search.explain_match", "relationship.list", "relationship.infer",
            "relationship.create", "relationship.delete", "audit.list_events",
            "index.status", "index.sync_profile", "index.rebuild"
        ],
        "allowed_permissions": [
            "catalog.read", "schema.read", "schema.change", "relationship.read",
            "relationship.change", "content.search", "data.read", "data.create",
            "data.update", "data.delete", "index.manage", "audit.read", "profile.manage"
        ],
        "field_masks": {},
        "field_exclusions": [],
        "index_policy": {
            "enabled": True,
            "include_content": True,
            "content_fields": ["name", "email", "product", "status"],
            "max_documents_per_entity": 10,
        },
    }
    created = call("POST", f"{API_BASE_URL}/v1/profiles", json=payload)
    sync_result = call("POST", f"{MCP_BASE_URL}/mcp/tools/index.sync_profile", json={"profile_id": created["profile_id"]})

    output = {
        "profile_id": created["profile_id"],
        "profile_name": PROFILE_NAME,
        "namespace": NAMESPACE,
        "sync_result": sync_result,
    }
    working = ROOT / "working"
    working.mkdir(parents=True, exist_ok=True)
    (working / "ui-e2e-state.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
