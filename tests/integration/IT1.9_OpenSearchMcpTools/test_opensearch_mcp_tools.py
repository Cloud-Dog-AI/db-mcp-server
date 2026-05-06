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
# Description: Integration test for OpenSearch MCP tools against a real local OpenSearch 2 runtime.
# Related requirements: CN-01, CD-02, SC-01, CO-01, CO-02
# Related tests: IT1.9

from __future__ import annotations

import subprocess
import time
from pathlib import Path

import httpx
import pytest
import requests

from tests.helpers.opensearch_runtime import cleanup_index, cleanup_template, ensure_real_opensearch
from tests.helpers.server_runtime import resolved_api_key, service_base_url

pytestmark = [pytest.mark.integration, pytest.mark.timeout(300)]


def _start_servers(root: Path, env_file: Path) -> None:
    subprocess.run(["bash", str(root / "server_control.sh"), "--env", str(env_file), "start", "all"], check=True, cwd=root)


def _stop_servers(root: Path, env_file: Path) -> None:
    subprocess.run(["bash", str(root / "server_control.sh"), "--env", str(env_file), "stop", "all"], check=True, cwd=root)


def _wait(url: str) -> None:
    deadline = time.time() + 90
    while time.time() < deadline:
        try:
            response = httpx.get(url, timeout=5.0)
            if response.status_code == 200:
                return
        except httpx.HTTPError:
            pass
        time.sleep(1)
    pytest.fail(f"Timed out waiting for {url}")


def test_opensearch_mcp_tools_crud_lifecycle() -> None:
    """OpenSearch MCP tools should perform real CRUD against a real local runtime."""
    base_url = ensure_real_opensearch()
    index_name = f"dbmcp_it_widgets_{int(time.time())}"
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

    root = Path(__file__).resolve().parents[3]
    env_file = root / "tests" / "env-IT"
    _start_servers(root, env_file)
    try:
        api_base_url = service_base_url("api", env_file, default_tier="IT")
        mcp_base_url = service_base_url("mcp", env_file, default_tier="IT")
        _wait(f"{mcp_base_url}/health")
        api = httpx.Client(base_url=api_base_url, timeout=10.0)
        mcp = httpx.Client(base_url=mcp_base_url, timeout=10.0)
        headers = {"X-API-Key": resolved_api_key(env_file, default_tier="IT")}

        cluster_name = requests.get(base_url, timeout=10).json()["cluster_name"]

        profile_response = api.post(
            "/v1/profiles",
            headers=headers,
            json={
                "name": "opensearch-it-profile",
                "source_type": "opensearch",
                "source_connection": base_url,
                "allowed_permissions": [
                    "catalog.read",
                    "schema.read",
                    "data.read",
                    "data.create",
                    "data.update",
                    "data.delete",
                ],
            },
        )
        assert profile_response.status_code == 200, profile_response.text
        profile_id = profile_response.json()["data"]["profile_id"]

        list_ns = mcp.post("/mcp/tools/catalog.list_namespaces", headers=headers, json={"profile_id": profile_id})
        assert list_ns.status_code == 200, list_ns.text
        namespaces = list_ns.json()["data"]["items"]
        assert any(item["name"] == cluster_name for item in namespaces)

        list_entities = mcp.post(
            "/mcp/tools/catalog.list_entities",
            headers=headers,
            json={"profile_id": profile_id, "namespace": cluster_name},
        )
        assert list_entities.status_code == 200, list_entities.text
        entity_names = {item["name"] for item in list_entities.json()["data"]["items"]}
        assert index_name in entity_names

        desc_fields = mcp.post(
            "/mcp/tools/schema.describe_fields",
            headers=headers,
            json={"profile_id": profile_id, "namespace": cluster_name, "entity": index_name},
        )
        assert desc_fields.status_code == 200, desc_fields.text
        assert any(item["name"] == "owner_id" for item in desc_fields.json()["data"]["fields"])

        count_before = mcp.post(
            "/mcp/tools/data.count",
            headers=headers,
            json={"profile_id": profile_id, "namespace": cluster_name, "entity": index_name, "filter": {}},
        )
        assert count_before.status_code == 200, count_before.text
        assert count_before.json()["data"]["count"] == 2

        created = mcp.post(
            "/mcp/tools/data.create",
            headers=headers,
            json={
                "profile_id": profile_id,
                "namespace": cluster_name,
                "entity": index_name,
                "document": {"name": "gamma", "owner_id": "u3", "value": 3},
            },
        )
        assert created.status_code == 200, created.text
        assert created.json()["data"]["document"]["owner_id"] == "u3"

        read = mcp.post(
            "/mcp/tools/data.read",
            headers=headers,
            json={
                "profile_id": profile_id,
                "namespace": cluster_name,
                "entity": index_name,
                "filter": {"owner_id": "u3"},
                "limit": 5,
            },
        )
        assert read.status_code == 200, read.text
        assert len(read.json()["data"]["items"]) == 1

        updated = mcp.post(
            "/mcp/tools/data.update",
            headers=headers,
            json={
                "profile_id": profile_id,
                "namespace": cluster_name,
                "entity": index_name,
                "filter": {"owner_id": "u3"},
                "update": {"$set": {"value": 9}},
            },
        )
        assert updated.status_code == 200, updated.text
        assert updated.json()["data"]["modified_count"] == 1

        deleted = mcp.post(
            "/mcp/tools/data.delete",
            headers=headers,
            json={
                "profile_id": profile_id,
                "namespace": cluster_name,
                "entity": index_name,
                "filter": {"owner_id": "u3"},
            },
        )
        assert deleted.status_code == 200, deleted.text
        assert deleted.json()["data"]["deleted_count"] == 1
    finally:
        _stop_servers(root, env_file)
        cleanup_index(index_name)
