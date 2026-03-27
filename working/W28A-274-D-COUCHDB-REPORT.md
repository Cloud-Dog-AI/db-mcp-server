# W28A-274-D — CouchDB Connector Report

## Verdict
PASS

## Scope completed
- Added `couchdb>=1.2` to [pyproject.toml](/opt/iac/Development/cloud-dog-ai/db-mcp-server/pyproject.toml)
- Added CouchDB connector defaults in [defaults.yaml](/opt/iac/Development/cloud-dog-ai/db-mcp-server/defaults.yaml)
- Implemented the CouchDB adapter contract in [adapter.py](/opt/iac/Development/cloud-dog-ai/db-mcp-server/src/core/connectors/couchdb/adapter.py)
- Registered the adapter export in [__init__.py](/opt/iac/Development/cloud-dog-ai/db-mcp-server/src/core/connectors/couchdb/__init__.py)
- Wired profile-based connector selection in [service.py](/opt/iac/Development/cloud-dog-ai/db-mcp-server/src/core/connectors/service.py)
- Added a CouchDB filter translator export in [translator.py](/opt/iac/Development/cloud-dog-ai/db-mcp-server/src/core/filters/translator.py) and [__init__.py](/opt/iac/Development/cloud-dog-ai/db-mcp-server/src/core/filters/__init__.py)
- Added real-runtime helper in [couchdb_runtime.py](/opt/iac/Development/cloud-dog-ai/db-mcp-server/tests/helpers/couchdb_runtime.py)
- Added UT/ST/IT coverage:
  - [UT1.13](/opt/iac/Development/cloud-dog-ai/db-mcp-server/tests/unit/UT1.13_CouchDBConnector/test_couchdb_connector.py)
  - [ST1.9](/opt/iac/Development/cloud-dog-ai/db-mcp-server/tests/system/ST1.9_CouchDBConnector/test_couchdb_connector_real.py)
  - [IT1.8](/opt/iac/Development/cloud-dog-ai/db-mcp-server/tests/integration/IT1.8_CouchDbMcpTools/test_couchdb_mcp_tools.py)
- Updated [docs/TESTS.md](/opt/iac/Development/cloud-dog-ai/db-mcp-server/docs/TESTS.md)

## Adapter contract coverage
Implemented methods:
1. `capability_report()`
2. `validate_profile()`
3. `list_namespaces()`
4. `list_entities(namespace)`
5. `describe_entity(namespace, entity)`
6. `describe_fields(namespace, entity)`
7. `read(namespace, entity, filter, projection, sort, limit)`
8. `create(namespace, entity, document)`
9. `update(namespace, entity, filter, update)`
10. `delete(namespace, entity, filter)`
11. `count(namespace, entity, filter)`
12. `sample_shapes(namespace, entity, n)`
13. `list_indexes(namespace, entity)`
14. `schema_change_plan(operation)`
15. `schema_change_apply(plan)`
16. `extract_relationships(namespace, entity)`
17. `close()`

## CouchDB behaviour summary
- Namespace maps to CouchDB database.
- Entity supports four modes:
  - `_documents` for raw document access
  - logical document-set entities inferred from `doc_type`
  - adapter-managed logical entities backed by `_design/dbmcp_entity_<entity>`
  - view entities exposed as `<design>/<view>`
- Non-design document reads are sourced from `_all_docs?include_docs=true` and filtered client-side.
- Logical entity CRUD scopes documents by `doc_type == entity`.
- `create()` auto-populates `doc_type` when writing to a logical entity.
- View entities are treated as read-only for content and schema mutation.
- Schema create/drop entity operations manage adapter-owned design documents.
- Schema create/drop index operations manage Mango indexes.
- Mango index field generation was normalised to real CouchDB shape, for example `{fields: [{\"name\": \"asc\"}]}`.
- Partial selector matching accepts both literal and `$eq` `doc_type` selectors when reconciling existing indexes.

## Runtime/config details
- Defaults:
  - `connectors.couchdb.enabled: true`
  - `connectors.couchdb.default_uri: ${vault.dev.databases.couchdb.uri}`
  - `connectors.couchdb.timeout_seconds: 30`
- Test overlay:
  - [tests/env-couchdb](/opt/iac/Development/cloud-dog-ai/db-mcp-server/tests/env-couchdb)
- Real CouchDB runtime used by ST and IT:
  - Docker `couchdb:3`
  - host networking
  - `http://admin:cloud-dog-test@127.0.0.1:5984`

## Root cause and runtime fix
Initial real-runtime probing failed for an environment-specific reason, not adapter logic:
- Host requests to a bridged/published CouchDB port were being reset on this machine.
- Direct `curl` inside the container succeeded, which isolated the problem to host-to-published-port behaviour.
- The runtime helper was changed to run CouchDB with `--network host`.
- The helper also ensures `_users` and `_replicator` exist before tests proceed.

## Exact commands run
```bash
cd /opt/iac/Development/cloud-dog-ai/db-mcp-server

python3 -m compileall src tests/helpers/couchdb_runtime.py \
  tests/unit/UT1.13_CouchDBConnector \
  tests/system/ST1.9_CouchDBConnector \
  tests/integration/IT1.8_CouchDbMcpTools \
  2>&1 | tee working/w28a-274d-compileall.log

set -a; source /opt/iac/Development/cloud-dog-ai/env-vault; set +a
venv/bin/python -m pytest tests/quality --env tests/env-QT -v --tb=short \
  2>&1 | tee working/w28a-274d-qt.log

set -a; source /opt/iac/Development/cloud-dog-ai/env-vault; set +a
venv/bin/python -m pytest tests/unit --env tests/env-UT -v --tb=short \
  2>&1 | tee working/w28a-274d-ut.log

set -a; source /opt/iac/Development/cloud-dog-ai/env-vault; set +a
venv/bin/python -m pytest tests/system/ST1.9_CouchDBConnector/test_couchdb_connector_real.py \
  --env tests/env-ST -v --tb=short \
  2>&1 | tee working/w28a-274d-st19.log

set -a; source /opt/iac/Development/cloud-dog-ai/env-vault; set +a
venv/bin/python -m pytest tests/integration/IT1.8_CouchDbMcpTools/test_couchdb_mcp_tools.py \
  --env tests/env-IT -v --tb=short \
  2>&1 | tee working/w28a-274d-it18.log
```

## Results
- Compile verification: PASS
  - Evidence: [w28a-274d-compileall.log](/opt/iac/Development/cloud-dog-ai/db-mcp-server/working/w28a-274d-compileall.log)
- QT: `1 passed in 0.05s`
  - Evidence: [w28a-274d-qt.log](/opt/iac/Development/cloud-dog-ai/db-mcp-server/working/w28a-274d-qt.log)
- UT full: `28 passed in 3.44s`
  - Evidence: [w28a-274d-ut.log](/opt/iac/Development/cloud-dog-ai/db-mcp-server/working/w28a-274d-ut.log)
- ST1.9: `1 passed in 0.40s`
  - Evidence: [w28a-274d-st19.log](/opt/iac/Development/cloud-dog-ai/db-mcp-server/working/w28a-274d-st19.log)
- IT1.8: `1 passed in 71.32s`
  - Evidence: [w28a-274d-it18.log](/opt/iac/Development/cloud-dog-ai/db-mcp-server/working/w28a-274d-it18.log)

## Notes
- ST and IT ran against a real local CouchDB instance and the real API/MCP stack.
- The project `venv` interpreter was required for full test execution on this host because the system `python3` environment is missing some repo dependencies used by the full unit suite.
