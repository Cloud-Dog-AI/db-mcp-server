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
# Description: OpenSearch seed module for the canonical connector test dataset.
# Related requirements: W28A-274-K deliverables 4, 8

"""OpenSearch seed utilities for the canonical connector dataset."""

from __future__ import annotations

import json
import os
from typing import Any

import requests

from tests.fixtures.canonical_data import clone_canonical_dataset

DEFAULT_OPENSEARCH_URL = os.getenv("DB_MCP_TEST_OPENSEARCH_URL", "http://127.0.0.1:9200")
DEFAULT_OPENSEARCH_PREFIX = os.getenv("DB_MCP_TEST_OPENSEARCH_PREFIX", "dbmcp_ecommerce")

FIELD_MAPPINGS = {
    "_id": {"type": "keyword"},
    "name": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
    "email": {"type": "keyword"},
    "country": {"type": "keyword"},
    "industry": {"type": "keyword"},
    "status": {"type": "keyword"},
    "tier": {"type": "keyword"},
    "created_at": {"type": "date", "format": "strict_date_optional_time||yyyy-MM-dd"},
    "updated_at": {"type": "date", "format": "strict_date_optional_time||yyyy-MM-dd", "ignore_malformed": True},
    "customer_id": {"type": "keyword"},
    "product_id": {"type": "keyword"},
    "quantity": {"type": "integer"},
    "unit_price": {"type": "double"},
    "total": {"type": "double"},
    "order_date": {"type": "date", "format": "strict_date_optional_time||yyyy-MM-dd"},
    "ship_date": {"type": "date", "format": "strict_date_optional_time||yyyy-MM-dd", "ignore_malformed": True},
    "category": {"type": "keyword"},
    "subcategory": {"type": "keyword"},
    "price": {"type": "double"},
    "stock": {"type": "integer"},
    "supplier_id": {"type": "keyword"},
    "description": {"type": "text"},
    "tags": {"type": "keyword"},
    "rating": {"type": "double"},
    "contact_email": {"type": "keyword"},
    "active": {"type": "boolean"},
    "order_id": {"type": "keyword"},
    "amount": {"type": "double"},
    "tax": {"type": "double"},
    "issued_date": {"type": "date", "format": "strict_date_optional_time||yyyy-MM-dd"},
    "due_date": {"type": "date", "format": "strict_date_optional_time||yyyy-MM-dd"},
    "paid_date": {"type": "date", "format": "strict_date_optional_time||yyyy-MM-dd", "ignore_malformed": True},
}


def _index_name(entity: str) -> str:
    return f"{DEFAULT_OPENSEARCH_PREFIX}_{entity}"


def _mapping_for_documents(documents: list[dict[str, Any]]) -> dict[str, Any]:
    properties: dict[str, Any] = {}
    for document in documents:
        for key in document:
            if key in FIELD_MAPPINGS:
                properties[key] = FIELD_MAPPINGS[key]
    return {"mappings": {"properties": properties}}


def seed_opensearch(*, base_url: str = DEFAULT_OPENSEARCH_URL) -> list[str]:
    dataset = clone_canonical_dataset()
    session = requests.Session()
    created: list[str] = []
    try:
        for entity, documents in dataset.items():
            index_name = _index_name(entity)
            session.delete(f"{base_url}/{index_name}", timeout=30)
            response = session.put(f"{base_url}/{index_name}", json=_mapping_for_documents(documents), timeout=30)
            response.raise_for_status()
            created.append(index_name)
            lines = []
            for document in documents:
                lines.append(json.dumps({"index": {"_index": index_name, "_id": document["_id"]}}))
                lines.append(json.dumps(document, default=str))
            response = session.post(
                f"{base_url}/_bulk",
                data="\n".join(lines) + "\n",
                headers={"Content-Type": "application/x-ndjson"},
                timeout=60,
            )
            response.raise_for_status()
        session.post(f"{base_url}/_refresh", timeout=30).raise_for_status()
        return created
    finally:
        session.close()


def teardown_opensearch(*, base_url: str = DEFAULT_OPENSEARCH_URL) -> None:
    session = requests.Session()
    try:
        for entity in clone_canonical_dataset():
            session.delete(f"{base_url}/{_index_name(entity)}", timeout=30)
    finally:
        session.close()


if __name__ == "__main__":
    created = seed_opensearch()
    print("OpenSearch seed completed for indices:", ", ".join(created))
