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
# Description: System test for the OpenSearch adapter against a real local OpenSearch 2 runtime.
# Related requirements: CN-01
# Related tests: ST1.10

from __future__ import annotations

import time

import pytest
import requests

from src.core.connectors.opensearch.adapter import OpenSearchConnector
from tests.helpers.opensearch_runtime import cleanup_index, cleanup_template, ensure_real_opensearch

pytestmark = [pytest.mark.system, pytest.mark.timeout(240)]


def test_opensearch_adapter_against_real_local_runtime() -> None:
    """OpenSearch adapter methods should work against a real local runtime."""
    base_url = ensure_real_opensearch()
    index_name = f"dbmcp_st_widgets_{int(time.time())}"
    template_name = f"dbmcp_{index_name}_owner_id_asc"
    mapping = {
        "mappings": {
            "properties": {
                "name": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                "owner_id": {"type": "keyword"},
                "status": {"type": "keyword"},
                "value": {"type": "integer"},
            }
        }
    }
    response = requests.put(f"{base_url}/{index_name}", json=mapping, timeout=20)
    response.raise_for_status()
    bulk = "\n".join(
        [
            f'{{"index": {{"_index": "{index_name}", "_id": "1"}}}}',
            '{"name":"alpha","owner_id":"u1","status":"active","value":1}',
            f'{{"index": {{"_index": "{index_name}", "_id": "2"}}}}',
            '{"name":"beta","owner_id":"u2","status":"inactive","value":2}',
            "",
        ]
    )
    response = requests.post(
        f"{base_url}/_bulk",
        data=bulk,
        headers={"Content-Type": "application/x-ndjson"},
        timeout=30,
    )
    response.raise_for_status()
    requests.post(f"{base_url}/_refresh", timeout=10).raise_for_status()

    connector = OpenSearchConnector(uri=base_url)
    try:
        namespace = connector.list_namespaces()[0]["name"]
        assert connector.validate_profile()["ok"] is True
        assert any(item["name"] == index_name for item in connector.list_entities(namespace))
        fields = connector.describe_fields(namespace, index_name)
        assert any(item["name"] == "owner_id" for item in fields["fields"])
        created = connector.create(namespace, index_name, {"name": "gamma", "owner_id": "u3", "value": 3})
        assert created["document"]["owner_id"] == "u3"
        rows = connector.read(namespace, index_name, {"term": {"owner_id": "u3"}}, limit=5)
        assert len(rows) == 1
        updated = connector.update(namespace, index_name, {"term": {"owner_id": "u3"}}, {"$set": {"value": 9}})
        assert updated["modified_count"] == 1
        assert connector.count(namespace, index_name, {"term": {"owner_id": "u3"}}) == 1
        relationships = connector.extract_relationships(namespace, index_name)
        assert any(item["field"] == "owner_id" for item in relationships)
        plan = connector.schema_change_plan(
            {
                "operation": "create_index",
                "namespace": namespace,
                "entity": index_name,
                "keys": [{"field": "owner_id", "direction": "asc"}],
            }
        )
        applied = connector.schema_change_apply(plan)
        assert applied["index_name"] == template_name
        indexes = connector.list_indexes(namespace, index_name)
        assert any(item["name"] == template_name for item in indexes)
        deleted = connector.delete(namespace, index_name, {"term": {"owner_id": "u3"}})
        assert deleted["deleted_count"] == 1
    finally:
        cleanup_template(template_name)
        cleanup_index(index_name)
