# W28A-274-C — MongoDB Connector Report

## Verdict
PASS

## Scope completed
- Added `pymongo>=4.0.0` to [pyproject.toml](/opt/iac/Development/cloud-dog-ai/db-mcp-server/pyproject.toml)
- Added MongoDB connector defaults in [defaults.yaml](/opt/iac/Development/cloud-dog-ai/db-mcp-server/defaults.yaml)
- Implemented connector contract in [src/core/connectors/mongodb/adapter.py](/opt/iac/Development/cloud-dog-ai/db-mcp-server/src/core/connectors/mongodb/adapter.py)
- Implemented profile-scoped MongoDB connector service in [src/core/connectors/mongodb/service.py](/opt/iac/Development/cloud-dog-ai/db-mcp-server/src/core/connectors/mongodb/service.py)
- Registered MongoDB MCP tools in [src/servers/mcp/mongodb_tools.py](/opt/iac/Development/cloud-dog-ai/db-mcp-server/src/servers/mcp/mongodb_tools.py) and [src/servers/mcp/app.py](/opt/iac/Development/cloud-dog-ai/db-mcp-server/src/servers/mcp/app.py)
- Added real test helper in [tests/helpers/mongo_runtime.py](/opt/iac/Development/cloud-dog-ai/db-mcp-server/tests/helpers/mongo_runtime.py)
- Added UT/ST/IT coverage:
  - [UT1.4](/opt/iac/Development/cloud-dog-ai/db-mcp-server/tests/unit/UT1.4_MongoDBConnector/test_mongodb_connector.py)
  - [ST1.3](/opt/iac/Development/cloud-dog-ai/db-mcp-server/tests/system/ST1.3_MongoDBConnector/test_mongodb_connector_real.py)
  - [IT1.2](/opt/iac/Development/cloud-dog-ai/db-mcp-server/tests/integration/IT1.2_MongoDbMcpTools/test_mongodb_mcp_tools.py)
- Updated [docs/TESTS.md](/opt/iac/Development/cloud-dog-ai/db-mcp-server/docs/TESTS.md) and [CONTEXT-SUMMARY.md](/opt/iac/Development/cloud-dog-ai/db-mcp-server/CONTEXT-SUMMARY.md)

## Adapter coverage
Implemented methods:
1. `capability_report()`
2. `list_namespaces()`
3. `list_entities(namespace)`
4. `describe_entity(namespace, entity)`
5. `describe_fields(namespace, entity)`
6. `read(namespace, entity, filter, projection, sort, limit)`
7. `create(namespace, entity, document)`
8. `update(namespace, entity, filter, update)`
9. `delete(namespace, entity, filter)`
10. `count(namespace, entity, filter)`
11. `sample_shapes(namespace, entity, n)`
12. `list_indexes(namespace, entity)`
13. `schema_change_plan(operation)`
14. `schema_change_apply(plan)`
15. `extract_relationships(namespace, entity)`

## MCP tools delivered
- `catalog.list_namespaces`
- `catalog.list_entities`
- `catalog.get_entity`
- `schema.describe_entity`
- `schema.describe_fields`
- `schema.list_indexes`
- `data.read`
- `data.create`
- `data.update`
- `data.delete`
- `data.count`

## Runtime/config details
- Defaults:
  - `connectors.mongodb.enabled: true`
  - `connectors.mongodb.default_uri: ${vault.dev.databases.mongodb.uri}`
  - `connectors.mongodb.timeout_ms: 30000`
- Test overlays use:
  - `CLOUD_DOG__CONNECTORS__MONGODB__DEFAULT_URI=mongodb://127.0.0.1:27018`
- Real MongoDB ST/IT runtime:
  - Docker `mongo:6.0`
  - host networking
  - bound to `127.0.0.1:27018`

## Root cause and fix during delivery
Initial ST failed for an environment-specific reason, not adapter logic:
- Local legacy Mongo on `127.0.0.1:27017` was too old for `pymongo 4.x`.
- Docker port publishing to `127.0.0.1:27018` accepted TCP but reset `pymongo` sessions on this host.
- Verified fix: run Mongo 6 with `--network host --bind_ip 127.0.0.1 --port 27018`.
- Updated `tests/helpers/mongo_runtime.py` to use that topology.

## Exact commands run
```bash
cd /opt/iac/Development/cloud-dog-ai/db-mcp-server
venv/bin/python -m pytest tests/unit/UT1.4_MongoDBConnector --env tests/env-UT -v --tb=short \
  2>&1 | tee working/w28a-274c-ut14.log

venv/bin/python -m pytest tests/system/ST1.3_MongoDBConnector --env tests/env-ST -v --tb=short \
  2>&1 | tee working/w28a-274c-st13.log

venv/bin/python -m pytest tests/integration/IT1.2_MongoDbMcpTools --env tests/env-IT -v --tb=short \
  2>&1 | tee working/w28a-274c-it12.log

venv/bin/python -m pytest \
  tests/unit/UT1.4_MongoDBConnector \
  tests/system/ST1.3_MongoDBConnector \
  tests/integration/IT1.2_MongoDbMcpTools \
  --env tests/env-IT -v --tb=short \
  2>&1 | tee working/w28a-274c-targeted.log

venv/bin/python -m compileall src tests start_api_server.py start_web_server.py start_mcp_server.py start_a2a_server.py \
  2>&1 | tee working/w28a-274c-compileall.log
```

## Results
- UT1.4: `2 passed in 0.98s`
  - Evidence: [w28a-274c-ut14.log](/opt/iac/Development/cloud-dog-ai/db-mcp-server/working/w28a-274c-ut14.log)
- ST1.3: `1 passed in 2.34s`
  - Evidence: [w28a-274c-st13.log](/opt/iac/Development/cloud-dog-ai/db-mcp-server/working/w28a-274c-st13.log)
- IT1.2: `1 passed in 71.42s`
  - Evidence: [w28a-274c-it12.log](/opt/iac/Development/cloud-dog-ai/db-mcp-server/working/w28a-274c-it12.log)
- Targeted verification: `4 passed in 72.14s`
  - Evidence: [w28a-274c-targeted.log](/opt/iac/Development/cloud-dog-ai/db-mcp-server/working/w28a-274c-targeted.log)
- Compile check: PASS
  - Evidence: [w28a-274c-compileall.log](/opt/iac/Development/cloud-dog-ai/db-mcp-server/working/w28a-274c-compileall.log)

## Notes
- IT executed against real local MongoDB and real `db-mcp-server` API/MCP processes started and stopped via `server_control.sh` only.
- One unrelated baseline observation remains outside W28A-274-C scope: API `/health` returned `503` under `tests/env-IT` while the API profile endpoints and MCP Mongo operations succeeded. Mongo connector pass criteria were still met because the real CRUD lifecycle completed successfully through API + MCP.
