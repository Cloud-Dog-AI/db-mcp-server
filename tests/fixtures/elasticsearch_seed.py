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
# Description: Elasticsearch seed module for the canonical connector test dataset.
# Related requirements: W28A-274-K deliverables 4, 8
# Recent changes:
#   W28A-274-F — Dedicated implementation (Elasticsearch 8.x rejects _id in mappings)

"""Elasticsearch seed utilities for the canonical connector dataset."""

from __future__ import annotations

import json
import os
from typing import Any

import requests

from tests.fixtures.canonical_data import clone_canonical_dataset
from tests.fixtures.opensearch_seed import FIELD_MAPPINGS

DEFAULT_ELASTICSEARCH_URL = os.getenv(
    "DB_MCP_TEST_ELASTICSEARCH_URL", "http://127.0.0.1:9201"
)
DEFAULT_ELASTICSEARCH_PREFIX = os.getenv(
    "DB_MCP_TEST_ELASTICSEARCH_PREFIX", "dbmcp_ecommerce"
)


def _index_name(entity: str) -> str:
    return f"{DEFAULT_ELASTICSEARCH_PREFIX}_{entity}"


def _mapping_for_documents(documents: list[dict[str, Any]]) -> dict[str, Any]:
    """Build an Elasticsearch-compatible mapping (excludes reserved ``_id``)."""
    properties: dict[str, Any] = {}
    for document in documents:
        for key in document:
            if key == "_id":
                continue
            if key in FIELD_MAPPINGS:
                properties[key] = FIELD_MAPPINGS[key]
    return {
        "settings": {"number_of_replicas": 0},
        "mappings": {"properties": properties},
    }


def seed_elasticsearch(*, base_url: str = DEFAULT_ELASTICSEARCH_URL) -> list[str]:
    """Seed the canonical dataset into Elasticsearch.

    Args:
        base_url: Full URL including credentials, e.g.
            ``http://elastic:pass@host:9200``.

    Returns:
        List of index names that were created.
    """
    dataset = clone_canonical_dataset()
    session = requests.Session()
    created: list[str] = []
    try:
        for entity, documents in dataset.items():
            index_name = _index_name(entity)
            session.delete(f"{base_url}/{index_name}", timeout=30)
            response = session.put(
                f"{base_url}/{index_name}",
                json=_mapping_for_documents(documents),
                timeout=30,
            )
            response.raise_for_status()
            created.append(index_name)
            lines: list[str] = []
            for document in documents:
                lines.append(
                    json.dumps(
                        {"index": {"_index": index_name, "_id": document["_id"]}}
                    )
                )
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


def teardown_elasticsearch(*, base_url: str = DEFAULT_ELASTICSEARCH_URL) -> None:
    """Drop seeded Elasticsearch indices."""
    session = requests.Session()
    try:
        for entity in clone_canonical_dataset():
            session.delete(f"{base_url}/{_index_name(entity)}", timeout=30)
    finally:
        session.close()


if __name__ == "__main__":
    created = seed_elasticsearch()
    print("Elasticsearch seed completed for indices:", ", ".join(created))
