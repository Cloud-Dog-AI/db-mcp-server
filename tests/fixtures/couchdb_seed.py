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
# Description: CouchDB seed module for the canonical connector test dataset.
# Related requirements: W28A-274-K deliverables 3, 8

"""CouchDB seed utilities for the canonical connector dataset."""

from __future__ import annotations

import os
from typing import Any

import requests

from tests.fixtures.canonical_data import clone_canonical_dataset

DEFAULT_COUCHDB_BASE_URL = os.getenv("DB_MCP_TEST_COUCHDB_URL", "http://127.0.0.1:5984")
DEFAULT_COUCHDB_PREFIX = os.getenv("DB_MCP_TEST_COUCHDB_PREFIX", "dbmcp_ecommerce")
DEFAULT_COUCHDB_USERNAME = os.getenv("DB_MCP_TEST_COUCHDB_USERNAME", os.getenv("COUCHDB_USER", "admin"))
DEFAULT_COUCHDB_PASSWORD = os.getenv("DB_MCP_TEST_COUCHDB_PASSWORD", os.getenv("COUCHDB_PASSWORD", "cloud-dog-test"))


def _session() -> requests.Session:
    session = requests.Session()
    session.auth = (DEFAULT_COUCHDB_USERNAME, DEFAULT_COUCHDB_PASSWORD)
    session.headers.update({"Content-Type": "application/json"})
    return session


def _database_name(entity: str) -> str:
    return f"{DEFAULT_COUCHDB_PREFIX}_{entity}"


def couchdb_documents() -> dict[str, list[dict[str, Any]]]:
    dataset = clone_canonical_dataset()
    out: dict[str, list[dict[str, Any]]] = {}
    for entity, documents in dataset.items():
        normalised = []
        for doc in documents:
            item = dict(doc)
            item["_id"] = str(item["_id"])
            item["doc_type"] = entity
            normalised.append(item)
        out[entity] = normalised
    return out


def couchdb_design_documents() -> dict[str, dict[str, Any]]:
    return {
        entity: {
            "_id": "_design/common",
            "views": {
                "by_status": {
                    "map": "function(doc){ if(doc.status){ emit(doc.status, null); } }",
                },
                "by_country": {
                    "map": "function(doc){ if(doc.country){ emit(doc.country, null); } }",
                },
            },
            "language": "javascript",
        }
        for entity in ("customers", "orders", "suppliers", "invoices")
    } | {
        "products": {
            "_id": "_design/common",
            "views": {
                "by_category": {
                    "map": "function(doc){ if(doc.category){ emit(doc.category, null); } }",
                },
                "by_supplier": {
                    "map": "function(doc){ if(doc.supplier_id){ emit(doc.supplier_id, null); } }",
                },
            },
            "language": "javascript",
        }
    }


def seed_couchdb(*, base_url: str = DEFAULT_COUCHDB_BASE_URL) -> list[str]:
    session = _session()
    created: list[str] = []
    try:
        for entity, docs in couchdb_documents().items():
            db_name = _database_name(entity)
            session.delete(f"{base_url}/{db_name}")
            response = session.put(f"{base_url}/{db_name}", timeout=30)
            response.raise_for_status()
            created.append(db_name)
            bulk = {"docs": [couchdb_design_documents()[entity], *docs]}
            response = session.post(f"{base_url}/{db_name}/_bulk_docs", json=bulk, timeout=30)
            response.raise_for_status()
        return created
    finally:
        session.close()


def teardown_couchdb(*, base_url: str = DEFAULT_COUCHDB_BASE_URL) -> None:
    session = _session()
    try:
        for entity in clone_canonical_dataset():
            session.delete(f"{base_url}/{_database_name(entity)}", timeout=30)
    finally:
        session.close()


if __name__ == "__main__":
    created = seed_couchdb()
    print("CouchDB seed completed for databases:", ", ".join(created))
