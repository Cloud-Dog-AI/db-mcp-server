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
# Description: Integration matrix for real shared-backend connector CRUD/discovery/schema coverage.
# Related requirements: CN-01, CD-02, SC-01, CO-01, CO-02
# Related tests: IT1.10

from __future__ import annotations

import os
import time
from pathlib import Path
from urllib.parse import urlparse, urlunparse

import pytest
import requests
from pymongo import MongoClient

from src.core.connectors.cassandra.adapter import CassandraConnector
from src.core.connectors.couchdb.adapter import CouchDBConnector
from src.core.connectors.elasticsearch.adapter import ElasticsearchConnector
from src.core.connectors.mariadb.adapter import MariaDBConnector
from src.core.connectors.mongodb.adapter import MongoDBConnector
from src.core.connectors.opensearch.adapter import OpenSearchConnector
from src.core.connectors.postgresql.adapter import PostgreSQLConnector
from tests.helpers.cassandra_runtime import ensure_real_cassandra
from tests.helpers.couchdb_runtime import cleanup_database as cleanup_couchdb_database
from tests.helpers.couchdb_runtime import ensure_real_couchdb
from tests.helpers.elasticsearch_runtime import cleanup_index as cleanup_elasticsearch_index
from tests.helpers.elasticsearch_runtime import cleanup_template as cleanup_elasticsearch_template
from tests.helpers.elasticsearch_runtime import ensure_real_elasticsearch
from tests.helpers.mongo_runtime import cleanup_database as cleanup_mongodb_database
from tests.helpers.mongo_runtime import ensure_real_mongodb
from tests.helpers.opensearch_runtime import cleanup_index as cleanup_opensearch_index
from tests.helpers.opensearch_runtime import cleanup_template as cleanup_opensearch_template
from tests.helpers.opensearch_runtime import ensure_real_opensearch

pytestmark = [pytest.mark.integration, pytest.mark.db, pytest.mark.timeout(600)]

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ALL_BACKENDS = ("mongodb", "couchdb", "opensearch", "elasticsearch", "postgresql", "mariadb", "cassandra")
ENV_BACKENDS = {f"env-{name}": name for name in ALL_BACKENDS}


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Parametrize only the active backend for connector-env matrix runs."""
    if "backend" not in metafunc.fixturenames:
        return
    env_args = metafunc.config.getoption("env") or []
    selected = []
    for raw in env_args:
        for part in str(raw).split(","):
            backend = ENV_BACKENDS.get(Path(part.strip()).name)
            if backend and backend not in selected:
                selected.append(backend)
    metafunc.parametrize("backend", selected or list(ALL_BACKENDS))


def _env_file_values(env_name: str) -> dict[str, str]:
    values: dict[str, str] = {}
    path = PROJECT_ROOT / "tests" / env_name
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def _env_value(key: str, env_name: str, default: str = "") -> str:
    return os.environ.get(key) or _env_file_values(env_name).get(key) or _env_file_values("env-all").get(key) or default


def _public_url(uri: str) -> str:
    parsed = urlparse(uri)
    netloc = parsed.hostname or ""
    if parsed.port:
        netloc = f"{netloc}:{parsed.port}"
    return urlunparse((parsed.scheme, netloc, parsed.path, "", "", "")).rstrip("/")


def _authed_request(base_url: str, method: str, path: str, **kwargs) -> requests.Response:
    parsed = urlparse(base_url)
    clean_url = _public_url(base_url) + path
    if parsed.username:
        kwargs.setdefault("auth", (parsed.username, parsed.password or ""))
    return requests.request(method, clean_url, **kwargs)
@pytest.mark.IT
@pytest.mark.mcp
@pytest.mark.req("FR-019")


def test_real_backend_connector_operations(backend: str) -> None:
    """Exercise real CRUD, discovery, schema, indexes, and relationship paths for one backend."""
    runners = {
        "mongodb": _run_mongodb,
        "couchdb": _run_couchdb,
        "opensearch": _run_opensearch,
        "elasticsearch": _run_elasticsearch,
        "postgresql": _run_postgresql,
        "mariadb": _run_mariadb,
        "cassandra": _run_cassandra,
    }
    runners[backend]()


def _run_mongodb() -> None:
    uri = ensure_real_mongodb()
    namespace = f"dbmcp_it_backend_{int(time.time())}"
    entity = "widgets"
    client = MongoClient(uri, serverSelectionTimeoutMS=3000)
    try:
        client[namespace][entity].insert_many(
            [
                {"name": "alpha", "owner_id": "u1", "value": 1},
                {"name": "beta", "owner_id": "u2", "value": 2},
            ]
        )
        connector = MongoDBConnector(uri=uri)
        try:
            assert connector.validate_profile()["ok"] is True
            assert any(item["name"] == namespace for item in connector.list_namespaces())
            assert any(item["name"] == entity for item in connector.list_entities(namespace))
            assert any(item["name"] == "owner_id" for item in connector.describe_fields(namespace, entity)["fields"])
            assert connector.sample_shapes(namespace, entity, n=2)
            created = connector.create(namespace, entity, {"name": "gamma", "owner_id": "u3", "value": 3})
            assert created["document"]["name"] == "gamma"
            assert len(connector.read(namespace, entity, {"owner_id": "u3"}, limit=5)) == 1
            assert connector.update(namespace, entity, {"owner_id": "u3"}, {"$set": {"value": 9}})["modified_count"] == 1
            assert connector.count(namespace, entity, {"owner_id": "u3"}) == 1
            index_name = connector.schema_change_apply(
                connector.schema_change_plan(
                    {
                        "operation": "create_index",
                        "namespace": namespace,
                        "entity": entity,
                        "keys": [{"field": "owner_id", "direction": "asc"}],
                        "name": "owner_id_it_idx",
                    }
                )
            )["index_name"]
            assert any(item["name"] == index_name for item in connector.list_indexes(namespace, entity))
            assert any(item["field"] == "owner_id" for item in connector.extract_relationships(namespace, entity))
            assert connector.delete(namespace, entity, {"owner_id": "u3"})["deleted_count"] == 1
        finally:
            connector.close()
    finally:
        client.close()
        cleanup_mongodb_database(namespace)


def _run_couchdb() -> None:
    uri = ensure_real_couchdb()
    base_url = _public_url(uri)
    namespace = f"dbmcp_it_backend_{int(time.time())}"
    entity = "widgets"
    session = requests.Session()
    parsed = urlparse(uri)
    if parsed.username:
        session.auth = (parsed.username, parsed.password or "")
    session.headers.update({"Content-Type": "application/json"})
    try:
        response = session.put(f"{base_url}/{namespace}", timeout=10)
        response.raise_for_status()
        response = session.post(
            f"{base_url}/{namespace}/_bulk_docs",
            json={
                "docs": [
                    {
                        "_id": "_design/common",
                        "views": {"by_status": {"map": "function(doc){ if(doc.status){ emit(doc.status, null); } }"}},
                    },
                    {"_id": "1", "doc_type": entity, "name": "alpha", "owner_id": "u1", "status": "active", "value": 1},
                    {"_id": "2", "doc_type": entity, "name": "beta", "owner_id": "u2", "status": "inactive", "value": 2},
                ]
            },
            timeout=10,
        )
        response.raise_for_status()
        connector = CouchDBConnector(uri=uri)
        assert connector.validate_profile()["ok"] is True
        assert any(item["name"] == namespace for item in connector.list_namespaces())
        entities = {item["name"] for item in connector.list_entities(namespace)}
        assert {entity, "common/by_status"}.issubset(entities)
        assert any(item["name"] == "owner_id" for item in connector.describe_fields(namespace, entity)["fields"])
        assert connector.sample_shapes(namespace, entity, n=2)
        created = connector.create(namespace, entity, {"name": "gamma", "owner_id": "u3", "value": 3})
        assert created["document"]["doc_type"] == entity
        assert len(connector.read(namespace, entity, {"owner_id": "u3"}, limit=5)) == 1
        assert connector.update(namespace, entity, {"owner_id": "u3"}, {"$set": {"value": 9}})["modified_count"] == 1
        assert connector.count(namespace, entity, {"owner_id": "u3"}) == 1
        applied = connector.schema_change_apply(
            connector.schema_change_plan(
                {
                    "operation": "create_index",
                    "namespace": namespace,
                    "entity": entity,
                    "keys": [{"field": "name", "direction": "asc"}],
                    "name": "name_it_idx",
                }
            )
        )
        assert applied["index_name"] == "name_it_idx"
        assert any(item["name"] == "name_it_idx" for item in connector.list_indexes(namespace, entity))
        assert isinstance(connector.extract_relationships(namespace, entity), list)
        assert connector.delete(namespace, entity, {"owner_id": "u3"})["deleted_count"] == 1
    finally:
        session.close()
        cleanup_couchdb_database(namespace)


def _run_opensearch() -> None:
    base_url = ensure_real_opensearch()
    index_name = f"dbmcp_it_backend_widgets_{int(time.time())}"
    template_name = f"dbmcp_{index_name}_owner_id_asc"
    try:
        _create_search_index(base_url, index_name)
        connector = OpenSearchConnector(uri=base_url)
        _assert_search_connector(connector, index_name, template_name)
    finally:
        cleanup_opensearch_template(template_name)
        cleanup_opensearch_index(index_name)


def _run_elasticsearch() -> None:
    base_url = ensure_real_elasticsearch()
    index_name = f"dbmcp_it_backend_widgets_{int(time.time())}"
    template_name = f"dbmcp_{index_name}_owner_id_asc"
    try:
        _create_search_index(base_url, index_name)
        connector = ElasticsearchConnector(uri=base_url)
        _assert_search_connector(connector, index_name, template_name)
    finally:
        cleanup_elasticsearch_template(template_name, base_url)
        cleanup_elasticsearch_index(index_name, base_url)


def _create_search_index(base_url: str, index_name: str) -> None:
    mapping = {
        "settings": {"number_of_replicas": 0},
        "mappings": {
            "properties": {
                "name": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                "owner_id": {"type": "keyword"},
                "status": {"type": "keyword"},
                "value": {"type": "integer"},
            }
        },
    }
    _authed_request(base_url, "PUT", f"/{index_name}", json=mapping, timeout=20).raise_for_status()
    bulk = "\n".join(
        [
            f'{{"index": {{"_index": "{index_name}", "_id": "1"}}}}',
            '{"name":"alpha","owner_id":"u1","status":"active","value":1}',
            f'{{"index": {{"_index": "{index_name}", "_id": "2"}}}}',
            '{"name":"beta","owner_id":"u2","status":"inactive","value":2}',
            "",
        ]
    )
    _authed_request(
        base_url,
        "POST",
        "/_bulk",
        data=bulk,
        headers={"Content-Type": "application/x-ndjson"},
        timeout=30,
    ).raise_for_status()
    _authed_request(base_url, "POST", "/_refresh", timeout=10).raise_for_status()


def _assert_search_connector(connector, index_name: str, template_name: str) -> None:
    namespace = connector.list_namespaces()[0]["name"]
    assert connector.validate_profile()["ok"] is True
    assert any(item["name"] == index_name for item in connector.list_entities(namespace))
    assert any(item["name"] == "owner_id" for item in connector.describe_fields(namespace, index_name)["fields"])
    assert connector.sample_shapes(namespace, index_name, n=2)
    created = connector.create(namespace, index_name, {"name": "gamma", "owner_id": "u3", "value": 3})
    assert created["document"]["owner_id"] == "u3"
    assert len(connector.read(namespace, index_name, {"term": {"owner_id": "u3"}}, limit=5)) == 1
    assert connector.update(namespace, index_name, {"term": {"owner_id": "u3"}}, {"$set": {"value": 9}})["modified_count"] == 1
    assert connector.count(namespace, index_name, {"term": {"owner_id": "u3"}}) == 1
    assert any(item["field"] == "owner_id" for item in connector.extract_relationships(namespace, index_name))
    applied = connector.schema_change_apply(
        connector.schema_change_plan(
            {
                "operation": "create_index",
                "namespace": namespace,
                "entity": index_name,
                "keys": [{"field": "owner_id", "direction": "asc"}],
            }
        )
    )
    assert applied["index_name"] == template_name
    assert any(item["name"] == template_name for item in connector.list_indexes(namespace, index_name))
    assert connector.delete(namespace, index_name, {"term": {"owner_id": "u3"}})["deleted_count"] == 1


def _run_postgresql() -> None:
    uri = _env_value("DB_MCP_TEST_POSTGRESQL_URI", "env-postgresql")
    _assert_relational_connector(PostgreSQLConnector(uri=uri), "public", "pg")


def _run_mariadb() -> None:
    uri = _env_value("DB_MCP_TEST_MARIADB_URI", "env-mariadb")
    namespace = _env_value("DB_MCP_TEST_MARIADB_DATABASE", "env-mariadb", "dbmcp_ecommerce")
    _assert_relational_connector(MariaDBConnector(uri=uri), namespace, "maria")


def _assert_relational_connector(connector, namespace: str, prefix: str) -> None:
    entity = f"w28a95b_{prefix}_widgets_{int(time.time())}"
    index_name = f"{entity}_owner_idx"
    try:
        assert connector.validate_profile()["ok"] is True
        assert any(item["name"] == namespace for item in connector.list_namespaces())
        connector.schema_change_apply(
            {
                "operation": "create_entity",
                "namespace": namespace,
                "entity": entity,
                "columns": {"id": "integer", "name": "text", "owner_id": "text", "value": "integer"},
                "primary_key": "id",
            }
        )
        assert any(item["name"] == entity for item in connector.list_entities(namespace))
        assert any(item["name"] == "owner_id" for item in connector.describe_fields(namespace, entity)["fields"])
        created = connector.create(namespace, entity, {"id": 1, "name": "alpha", "owner_id": "u1", "value": 10})
        assert created["document"]["owner_id"] == "u1"
        assert connector.sample_shapes(namespace, entity, n=1)
        assert len(connector.read(namespace, entity, {"id": 1}, limit=5)) == 1
        assert connector.update(namespace, entity, {"id": 1}, {"$set": {"value": 11}})["modified_count"] == 1
        assert connector.count(namespace, entity, {"id": 1}) == 1
        applied = connector.schema_change_apply(
            connector.schema_change_plan(
                {
                    "operation": "create_index",
                    "namespace": namespace,
                    "entity": entity,
                    "column": "owner_id",
                    "name": index_name,
                }
            )
        )
        assert applied["index_name"] == index_name
        assert any(item["name"] == index_name for item in connector.list_indexes(namespace, entity))
        assert isinstance(connector.extract_relationships(namespace, entity), list)
        assert connector.delete(namespace, entity, {"id": 1})["deleted_count"] == 1
    finally:
        try:
            connector.schema_change_apply({"operation": "drop_entity", "namespace": namespace, "entity": entity})
        finally:
            connector.close()


def _run_cassandra() -> None:
    host, port, keyspace = ensure_real_cassandra()
    username = _env_value("DB_MCP_TEST_CASSANDRA_USERNAME", "env-cassandra")
    password = _env_value("DB_MCP_TEST_CASSANDRA_PASSWORD", "env-cassandra")
    connector = CassandraConnector(
        host=host,
        port=port,
        username=username or None,
        password=password or None,
        timeout_seconds=15,
    )
    entity = f"w28a95b_cass_widgets_{int(time.time())}"
    index_name = f"idx_{entity}_owner_id"
    try:
        assert connector.validate_profile()["ok"] is True
        assert any(item["name"] == keyspace for item in connector.list_namespaces())
        connector.schema_change_apply(
            {
                "operation": "create_entity",
                "namespace": keyspace,
                "entity": entity,
                "columns": {"id": "text", "name": "text", "owner_id": "text", "value": "int"},
                "primary_key": "id",
            }
        )
        assert any(item["name"] == entity for item in connector.list_entities(keyspace))
        assert any(item["name"] == "owner_id" for item in connector.describe_fields(keyspace, entity)["fields"])
        connector.create(keyspace, entity, {"id": "t1", "name": "alpha", "owner_id": "u1", "value": 10})
        assert connector.sample_shapes(keyspace, entity, n=1)
        assert len(connector.read(keyspace, entity, {"id": "t1"}, limit=1)) == 1
        assert connector.update(keyspace, entity, {"id": "t1"}, {"$set": {"value": 11}})["modified_count"] == 1
        assert connector.count(keyspace, entity, {"id": "t1"}) == 1
        applied = connector.schema_change_apply(
            connector.schema_change_plan(
                {
                    "operation": "create_index",
                    "namespace": keyspace,
                    "entity": entity,
                    "column": "owner_id",
                    "name": index_name,
                }
            )
        )
        assert applied["index_name"] == index_name
        assert any(item["name"] == index_name for item in connector.list_indexes(keyspace, entity))
        assert any(item["field"] == "owner_id" for item in connector.extract_relationships(keyspace, entity))
        assert connector.delete(keyspace, entity, {"id": "t1"})["deleted_count"] == 1
    finally:
        try:
            connector.schema_change_apply(
                {"operation": "drop_index", "namespace": keyspace, "entity": entity, "name": index_name}
            )
            connector.schema_change_apply({"operation": "drop_entity", "namespace": keyspace, "entity": entity})
        finally:
            connector.close()
