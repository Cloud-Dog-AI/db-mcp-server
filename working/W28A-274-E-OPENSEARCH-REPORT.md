# W28A-274-E — OpenSearch Connector Report

## Verdict
PASS

## Scope completed
- Added `opensearch-py>=2.0` to [pyproject.toml](/opt/iac/Development/cloud-dog-ai/db-mcp-server/pyproject.toml)
- Added OpenSearch connector defaults in [defaults.yaml](/opt/iac/Development/cloud-dog-ai/db-mcp-server/defaults.yaml)
- Implemented the OpenSearch adapter contract in [adapter.py](/opt/iac/Development/cloud-dog-ai/db-mcp-server/src/core/connectors/opensearch/adapter.py)
- Registered the adapter export in [__init__.py](/opt/iac/Development/cloud-dog-ai/db-mcp-server/src/core/connectors/opensearch/__init__.py)
- Wired profile-based connector selection in [service.py](/opt/iac/Development/cloud-dog-ai/db-mcp-server/src/core/connectors/service.py)
- Added an OpenSearch filter translator export in [translator.py](/opt/iac/Development/cloud-dog-ai/db-mcp-server/src/core/filters/translator.py) and [__init__.py](/opt/iac/Development/cloud-dog-ai/db-mcp-server/src/core/filters/__init__.py)
- Added real-runtime helper in [opensearch_runtime.py](/opt/iac/Development/cloud-dog-ai/db-mcp-server/tests/helpers/opensearch_runtime.py)
- Added UT/ST/IT coverage:
  - [UT1.14](/opt/iac/Development/cloud-dog-ai/db-mcp-server/tests/unit/UT1.14_OpenSearchConnector/test_opensearch_connector.py)
  - [ST1.10](/opt/iac/Development/cloud-dog-ai/db-mcp-server/tests/system/ST1.10_OpenSearchConnector/test_opensearch_connector_real.py)
  - [IT1.9](/opt/iac/Development/cloud-dog-ai/db-mcp-server/tests/integration/IT1.9_OpenSearchMcpTools/test_opensearch_mcp_tools.py)
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

## OpenSearch behaviour summary
- Namespace maps to the OpenSearch cluster name.
- Entity supports two real forms:
  - concrete index
  - alias
- Mapping-based schema is authoritative.
- `describe_fields()` reads mappings only and does not sample documents.
- `read()` uses OpenSearch query DSL generated from the structured filter model.
- `create()` indexes a document and returns the persisted hit.
- `update()` uses `update_by_query` with generated painless scripts for `$set` and `$unset`.
- `delete()` uses `delete_by_query`.
- `create_index` and `drop_index` manage composable index templates, matching the OpenSearch-native schema-management model.
- `list_indexes()` surfaces relevant aliases and matching index templates for the target entity.
- Relationship inference uses mapping-defined keyword identifier fields ending in `_id`.

## Runtime/config details
- Defaults:
  - `connectors.opensearch.enabled: true`
  - `connectors.opensearch.default_uri: ${vault.dev.databases.opensearch.url || ''}`
  - `connectors.opensearch.timeout_seconds: 30`
- Test overlay:
  - [tests/env-opensearch](/opt/iac/Development/cloud-dog-ai/db-mcp-server/tests/env-opensearch)
- Real OpenSearch runtime used by ST and IT:
  - Docker `opensearchproject/opensearch:2.14.0`
  - host networking
  - `http://127.0.0.1:9200`

## Root cause and runtime fix
Initial real-runtime startup failed for an environment-specific reason, not adapter logic:
- Current OpenSearch 2.14 local startup still enforces `OPENSEARCH_INITIAL_ADMIN_PASSWORD`, even when `plugins.security.disabled=true` is set.
- The first helper revision omitted that variable, then used a password that failed the newer strength validation.
- The runtime helper was corrected to provide a strong initial admin password that satisfies the current container policy.
- After that fix, the real OpenSearch ST and IT runs passed without source changes to the adapter itself.

## Exact commands run
```bash
cd /opt/iac/Development/cloud-dog-ai/db-mcp-server

python3 -m compileall src tests/helpers/opensearch_runtime.py \
  tests/unit/UT1.14_OpenSearchConnector \
  tests/system/ST1.10_OpenSearchConnector \
  tests/integration/IT1.9_OpenSearchMcpTools \
  2>&1 | tee working/w28a-274e-compileall.log

venv/bin/pip install 'opensearch-py>=2.0'

set -a; source /opt/iac/Development/cloud-dog-ai/env-vault; set +a
venv/bin/python -m pytest tests/quality --env tests/env-QT -v --tb=short \
  2>&1 | tee working/w28a-274e-qt.log

set -a; source /opt/iac/Development/cloud-dog-ai/env-vault; set +a
venv/bin/python -m pytest tests/unit/UT1.14_OpenSearchConnector/test_opensearch_connector.py \
  --env tests/env-UT -vv -rs \
  2>&1 | tee working/w28a-274e-ut14.log

set -a; source /opt/iac/Development/cloud-dog-ai/env-vault; set +a
venv/bin/python -m pytest tests/unit --env tests/env-UT -v --tb=short \
  2>&1 | tee working/w28a-274e-ut.log

set -a; source /opt/iac/Development/cloud-dog-ai/env-vault; set +a
venv/bin/python -m pytest tests/system/ST1.10_OpenSearchConnector/test_opensearch_connector_real.py \
  --env tests/env-ST -v --tb=short \
  2>&1 | tee working/w28a-274e-st10.log

set -a; source /opt/iac/Development/cloud-dog-ai/env-vault; set +a
venv/bin/python -m pytest tests/integration/IT1.9_OpenSearchMcpTools/test_opensearch_mcp_tools.py \
  --env tests/env-IT -v --tb=short \
  2>&1 | tee working/w28a-274e-it19.log
```

## Results
- Compile verification: PASS
  - Evidence: [w28a-274e-compileall.log](/opt/iac/Development/cloud-dog-ai/db-mcp-server/working/w28a-274e-compileall.log)
- QT: `1 passed in 0.05s`
  - Evidence: [w28a-274e-qt.log](/opt/iac/Development/cloud-dog-ai/db-mcp-server/working/w28a-274e-qt.log)
- UT1.14 targeted: `2 passed in 0.44s`
  - Evidence: [w28a-274e-ut14.log](/opt/iac/Development/cloud-dog-ai/db-mcp-server/working/w28a-274e-ut14.log)
- UT full: `30 passed in 3.47s`
  - Evidence: [w28a-274e-ut.log](/opt/iac/Development/cloud-dog-ai/db-mcp-server/working/w28a-274e-ut.log)
- ST1.10: `1 passed in 148.29s`
  - Evidence: [w28a-274e-st10.log](/opt/iac/Development/cloud-dog-ai/db-mcp-server/working/w28a-274e-st10.log)
- IT1.9: `1 passed in 73.95s`
  - Evidence: [w28a-274e-it19.log](/opt/iac/Development/cloud-dog-ai/db-mcp-server/working/w28a-274e-it19.log)

## Notes
- ST and IT ran against a real local OpenSearch instance and the real API/MCP stack.
- The local db-mcp stack was confirmed stopped after the IT run.
- The project `venv` interpreter was required for the full validation flow on this host so the newly added OpenSearch dependency was available.
