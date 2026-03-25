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
# Description: Canonical e-commerce fixture dataset shared by all connector seed modules.
# Related requirements: W28A-274-K deliverables 1, 2, 3, 4, 5
# Related tests: tests/fixtures/test_seed_data.py

"""Canonical e-commerce fixture dataset for connector test environments."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

COUNTRIES = ["UK", "US", "DE", "FR", "JP"]
CUSTOMER_INDUSTRIES = ["manufacturing", "technology", "logistics", "finance", "retail"]
CUSTOMER_TIERS = ["bronze", "silver", "gold", "platinum"]
PRODUCT_CATEGORIES = [
    ("hardware", "laptops"),
    ("hardware", "networking"),
    ("software", "analytics"),
    ("software", "security"),
    ("services", "consulting"),
]
PRODUCT_TAGS = [
    ["featured", "b2b"],
    ["clearance", "warehouse"],
    ["subscription", "saas"],
    ["priority", "security"],
    ["premium", "support"],
]


@dataclass(frozen=True)
class DatasetSchema:
    entity: str
    fields: tuple[str, ...]
    record_count: int
    relationships: tuple[str, ...]


DATASET_SCHEMA: tuple[DatasetSchema, ...] = (
    DatasetSchema(
        entity="customers",
        fields=("_id", "name", "email", "country", "industry", "status", "tier", "created_at", "updated_at"),
        record_count=25,
        relationships=("orders.customer_id -> customers._id", "invoices.customer_id -> customers._id"),
    ),
    DatasetSchema(
        entity="orders",
        fields=("_id", "customer_id", "product_id", "quantity", "unit_price", "total", "status", "order_date", "ship_date"),
        record_count=50,
        relationships=("orders.customer_id -> customers._id", "orders.product_id -> products._id"),
    ),
    DatasetSchema(
        entity="products",
        fields=("_id", "name", "category", "subcategory", "price", "stock", "supplier_id", "description", "tags"),
        record_count=20,
        relationships=("products.supplier_id -> suppliers._id", "orders.product_id -> products._id"),
    ),
    DatasetSchema(
        entity="suppliers",
        fields=("_id", "name", "country", "rating", "contact_email", "active"),
        record_count=10,
        relationships=("products.supplier_id -> suppliers._id",),
    ),
    DatasetSchema(
        entity="invoices",
        fields=("_id", "order_id", "customer_id", "amount", "tax", "total", "status", "issued_date", "due_date", "paid_date"),
        record_count=35,
        relationships=("invoices.order_id -> orders._id", "invoices.customer_id -> customers._id"),
    ),
)


def _customer_record(index: int) -> dict[str, Any]:
    country = COUNTRIES[(index - 1) % len(COUNTRIES)]
    status = "active" if index % 5 else "inactive"
    updated_at = None if index % 6 == 0 else f"2026-{((index + 2) % 12) + 1:02d}-{((index + 5) % 28) + 1:02d}"
    return {
        "_id": f"C{index:03d}",
        "name": f"Customer {index:02d}",
        "email": f"customer{index:02d}@example.com",
        "country": country,
        "industry": CUSTOMER_INDUSTRIES[(index - 1) % len(CUSTOMER_INDUSTRIES)],
        "status": status,
        "tier": CUSTOMER_TIERS[(index - 1) % len(CUSTOMER_TIERS)],
        "created_at": f"2025-{((index - 1) % 12) + 1:02d}-{((index - 1) % 28) + 1:02d}",
        "updated_at": updated_at,
    }


def _supplier_record(index: int) -> dict[str, Any]:
    country = COUNTRIES[(index + 1) % len(COUNTRIES)]
    return {
        "_id": f"S{index:03d}",
        "name": f"Supplier {index:02d}",
        "country": country,
        "rating": round(3.4 + ((index - 1) % 5) * 0.4, 1),
        "contact_email": None if index % 4 == 0 else f"supplier{index:02d}@example.com",
        "active": index % 5 != 0,
    }


def _product_record(index: int, suppliers: list[dict[str, Any]]) -> dict[str, Any]:
    category, subcategory = PRODUCT_CATEGORIES[(index - 1) % len(PRODUCT_CATEGORIES)]
    description = None if index % 7 == 0 else f"{category.title()} product {index:02d} tuned for enterprise workloads."
    return {
        "_id": f"P{index:03d}",
        "name": f"Product {index:02d}",
        "category": category,
        "subcategory": subcategory,
        "price": round(49.5 + index * 11.75, 2),
        "stock": 18 + index * 7,
        "supplier_id": suppliers[(index - 1) % len(suppliers)]["_id"],
        "description": description,
        "tags": PRODUCT_TAGS[(index - 1) % len(PRODUCT_TAGS)],
    }


def _order_record(index: int, customers: list[dict[str, Any]], products: list[dict[str, Any]]) -> dict[str, Any]:
    customer = customers[(index - 1) % len(customers)]
    product = products[(index - 1) % len(products)]
    quantity = (index % 5) + 1
    unit_price = product["price"]
    status_cycle = ["open", "processing", "shipped", "delivered", "cancelled"]
    status = status_cycle[(index - 1) % len(status_cycle)]
    ship_date = None if status in {"open", "processing", "cancelled"} else f"2026-{((index + 1) % 12) + 1:02d}-{((index + 6) % 28) + 1:02d}"
    return {
        "_id": f"O{index:03d}",
        "customer_id": customer["_id"],
        "product_id": product["_id"],
        "quantity": quantity,
        "unit_price": unit_price,
        "total": round(quantity * unit_price, 2),
        "status": status,
        "order_date": f"2026-{((index - 1) % 12) + 1:02d}-{((index + 2) % 28) + 1:02d}",
        "ship_date": ship_date,
    }


def _invoice_record(index: int, orders: list[dict[str, Any]]) -> dict[str, Any]:
    order = orders[index - 1]
    status_cycle = ["issued", "paid", "overdue", "partially_paid", "void"]
    status = status_cycle[(index - 1) % len(status_cycle)]
    amount = order["total"]
    tax = round(amount * 0.2, 2)
    paid_date = None if status not in {"paid", "partially_paid"} else f"2026-{((index + 3) % 12) + 1:02d}-{((index + 8) % 28) + 1:02d}"
    return {
        "_id": f"I{index:03d}",
        "order_id": order["_id"],
        "customer_id": order["customer_id"],
        "amount": amount,
        "tax": tax,
        "total": round(amount + tax, 2),
        "status": status,
        "issued_date": f"2026-{((index + 1) % 12) + 1:02d}-{((index + 3) % 28) + 1:02d}",
        "due_date": f"2026-{((index + 2) % 12) + 1:02d}-{((index + 10) % 28) + 1:02d}",
        "paid_date": paid_date,
    }


def build_canonical_dataset() -> dict[str, list[dict[str, Any]]]:
    """Return the canonical connector test dataset."""
    customers = [_customer_record(index) for index in range(1, 26)]
    suppliers = [_supplier_record(index) for index in range(1, 11)]
    products = [_product_record(index, suppliers) for index in range(1, 21)]
    orders = [_order_record(index, customers, products) for index in range(1, 51)]
    invoices = [_invoice_record(index, orders) for index in range(1, 36)]
    return {
        "customers": customers,
        "orders": orders,
        "products": products,
        "suppliers": suppliers,
        "invoices": invoices,
    }


CANONICAL_DATASET = build_canonical_dataset()


def clone_canonical_dataset() -> dict[str, list[dict[str, Any]]]:
    """Return a deep copy of the canonical fixture dataset."""
    return deepcopy(CANONICAL_DATASET)


def dataset_counts() -> dict[str, int]:
    """Return entity counts for the canonical dataset."""
    return {name: len(items) for name, items in CANONICAL_DATASET.items()}
