# db-mcp-server — Tests

## Implemented tiers

### QT
- `tests/quality/QT1.1_ProjectStructure/test_project_structure.py`
  - Verifies the four server entry points, core runtime modules, docs, and control assets exist.
  - Confirms the project is no longer in planning-only shape.

### UT
- `tests/unit/UT1.1_ConfigLoading/test_config_loading.py`
  - Loads config through `cloud_dog_config` using `--env` file input.
  - Verifies four-server ports, auth key override, and runtime config output.
- `tests/unit/UT1.2_AuthMiddleware/test_auth_middleware.py`
  - Verifies API key enforcement on protected API routes.
  - Verifies public health endpoints stay reachable without credentials.
- `tests/unit/UT1.3_AccessControlService/test_access_control_service.py`
  - Verifies profile field masking and field exclusion logic.
  - Verifies API-key capability scoping intersects with RBAC permissions.
  - Verifies group role assignments contribute to a user's effective permissions.
- `tests/unit/UT1.4_MongoDBConnector/test_mongodb_connector.py`
  - Verifies MongoDB adapter capability reporting, catalogue access, structured read/write operations, schema planning, and relationship inference with mocked `pymongo`.
  - Verifies BSON normalisation and Mongo-specific operation shaping without using a live backend.
- `tests/unit/UT1.5_FilterModel/test_filter_model.py`
  - Verifies structured filter parsing from explicit group JSON and backwards-compatible legacy flat dictionaries.
  - Verifies translation of filter conditions and nested boolean groups into MongoDB query documents.
- `tests/unit/UT1.6_CatalogTools/test_catalog_tools.py`
  - Verifies catalogue tools call the connector manager, apply principal/profile scoping, and return only permitted catalogue metadata.
- `tests/unit/UT1.7_ContentTools/test_content_tools.py`
  - Verifies content tool filter translation, single and bulk create semantics, masked-field reads, and audited mutation calls.
- `tests/unit/UT1.8_RelationshipTools/test_relationship_tools.py`
  - Verifies relationship tool CRUD and inferred-relationship flow against the shared metadata-backed service.
- `tests/unit/UT1.9_SearchIndexer/test_search_indexer.py`
  - Verifies discovery query token normalisation and FTS5 query construction.
  - Verifies profile indexing produces field, relationship-hint, and content-excerpt discovery documents while respecting profile index policy.
- `tests/unit/UT1.10_SearchService/test_search_service.py`
  - Verifies SQLite FTS5-backed metadata/content search, match explanation, and index-status serialisation.
- `tests/unit/UT1.12_SchemaChangeService/test_schema_change_service.py`
  - Verifies schema-change operation parsing, approval gating, plan persistence, apply execution, and history retrieval.
  - Verifies index refresh is triggered after apply and that audit identifiers are carried into persisted history.
- `tests/unit/UT1.13_CouchDBConnector/test_couchdb_connector.py`
  - Verifies CouchDB adapter capability reporting, profile validation, namespace and entity discovery, CRUD, count, schema operations, and relationship extraction with mocked HTTP/session behaviour.
  - Verifies Mango index creation payload shaping and CouchDB-specific entity abstraction without a live backend.
- `tests/unit/UT1.14_OpenSearchConnector/test_opensearch_connector.py`
  - Verifies OpenSearch adapter capability reporting, cluster and entity discovery, mapping-based schema description, CRUD, count, schema operations, and relationship extraction with a mocked OpenSearch client.
  - Verifies query-DLS execution shaping and index-template lifecycle without a live backend.

### ST
- `tests/system/ST1.1_ServerStartup/test_server_startup.py`
  - Starts all four local servers with `server_control.sh --env tests/env-ST start all`.
  - Probes `/health` on API, Web, MCP, and A2A.
  - Stops all servers with `server_control.sh --env tests/env-ST stop all`.
- `tests/system/ST1.2_AccessControlApi/test_access_control_api.py`
  - Exercises real API CRUD for profiles, users, groups, and API keys.
  - Verifies unauthenticated requests return `401` and least-privilege denials return `403`.
  - Verifies audit events are written for create and denied actions.
- `tests/system/ST1.3_MongoDBConnector/test_mongodb_connector_real.py`
  - Exercises the MongoDB adapter against a real local MongoDB 6 runtime.
  - Verifies namespace discovery, collection discovery, field inference, index listing, CRUD, count, and relationship extraction.
  - Uses a local Docker Mongo 6 container on `127.0.0.1:27018` via host networking because host port publishing resets `pymongo` sessions on this machine.
- `tests/system/ST1.4_CatalogApi/test_catalog_api.py`
  - Exercises catalogue discovery against the real API stack and seeded MongoDB dataset.
  - Verifies namespace listing, entity listing, entity metadata, and keyword search via the connector-agnostic catalogue tool surface.
- `tests/system/ST1.5_ContentApi/test_content_api.py`
  - Exercises real API content CRUD against the structured filter model.
  - Verifies create, read, update, delete, count, and exists semantics with audit emission.
- `tests/system/ST1.6_SchemaApi/test_schema_api.py`
  - Exercises schema describe, field describe, index listing, sample shapes, schema change planning/apply, persisted history, and discovery refresh via the real API stack.
- `tests/system/ST1.7_SearchApi/test_search_api.py`
  - Exercises profile-scoped discovery indexing and metadata search on the real API/MCP stack and seeded MongoDB dataset.
  - Verifies `index.sync_profile`, `search.metadata`, `search.explain_match`, and `index.status`.
- `tests/system/ST1.8_WebUiServing/test_web_ui_system_serving.py`
  - Starts the real four-surface stack with `tests/env-ST-WEBUI`.
  - Verifies the web surface serves the SPA shell, `/runtime-config.js`, browser-history routes, and same-origin API proxying.
- `tests/system/ST1.9_CouchDBConnector/test_couchdb_connector_real.py`
  - Exercises the CouchDB adapter against a real local CouchDB 3 runtime.
  - Verifies database discovery, entity discovery, field inference, index listing, CRUD, count, and relationship extraction.
  - Uses a local Docker CouchDB 3 container on `127.0.0.1:5984` via host networking because bridged port publishing reset host HTTP client sessions on this machine.
- `tests/system/ST1.10_OpenSearchConnector/test_opensearch_connector_real.py`
  - Exercises the OpenSearch adapter against a real local OpenSearch 2 runtime.
  - Verifies cluster discovery, index discovery, mapping-based field description, CRUD, count, template-backed schema changes, and relationship extraction.
  - Uses a local Docker OpenSearch 2 container on `127.0.0.1:9200` via host networking and a strong initial admin password because current OpenSearch startup enforces that bootstrap requirement even in local test mode.

### IT
- `tests/integration/IT1.1_AccessControlLifecycle/test_access_control_lifecycle.py`
  - Creates a profile, user, group, and scoped API key via the real API server.
  - Verifies permitted and denied profile-scoped actions via API.
  - Verifies MCP tool catalogue exposure, admin execution, and admin-only denial for a limited principal.
- `tests/integration/IT1.2_MongoDbMcpTools/test_mongodb_mcp_tools.py`
  - Creates a real MongoDB profile through the API server and executes Mongo catalogue/schema/data tools through the MCP server.
  - Verifies namespace listing, collection listing, field inference, document count, create, read, update, and delete through real HTTP requests.
  - Starts and stops the project using `server_control.sh --env tests/env-IT`.
- `tests/integration/IT1.3_FullDiscoveryFlow/test_full_discovery_flow.py`
  - Verifies the full discovery path: profiles, namespaces, entities, schema detail, sample read, and catalogue search on the seeded dataset.
- `tests/integration/IT1.4_ContentCRUDLifecycle/test_content_crud_lifecycle.py`
  - Verifies end-to-end create, read, update, reread, delete, and post-delete verification using the structured filter model on the real stack.
- `tests/integration/IT1.5_RelationshipLifecycle/test_relationship_lifecycle.py`
  - Verifies relationship inference, curated relationship creation, metadata update, delete, and audit visibility on the real stack.
- `tests/integration/IT1.6_SearchIndexingLifecycle/test_search_indexing_lifecycle.py`
  - Verifies full discovery indexing lifecycle: sync profile, metadata search, content search, related-entity search, entity resync, rebuild, and final status reporting.
- `tests/integration/IT1.7_SchemaChangeLifecycle/test_schema_change_lifecycle.py`
  - Verifies full schema workflow: plan, approve, apply, audit-log visibility, history visibility, and index refresh on the real stack.
- `tests/integration/IT1.8_CouchDbMcpTools/test_couchdb_mcp_tools.py`
  - Creates a real CouchDB profile through the API server and executes catalogue, schema, and data tools through the MCP server.
  - Verifies namespace listing, entity listing, field inference, count, create, read, update, and delete through real HTTP requests against the real four-surface stack.
- `tests/integration/IT1.9_OpenSearchMcpTools/test_opensearch_mcp_tools.py`
  - Creates a real OpenSearch profile through the API server and executes catalogue, schema, and data tools through the MCP server.
  - Verifies cluster namespace discovery, index listing, mapping-based field description, count, create, read, update, and delete through real HTTP requests against the real four-surface stack.

### AT
- None yet.

### Fixture Verification
- `tests/fixtures/test_seed_data.py`
  - Starts the MongoDB Docker test environment through `scripts/seed-test-data.sh mongodb`.
  - Verifies canonical record counts, cross-entity references, and field-type/nullability preservation on the seeded dataset.

## Env files
- `tests/env-QT`
- `tests/env-UT`
- `tests/env-ST`
- `tests/env-ST-WEBUI`
- `tests/env-IT`
- `tests/env-AT`
- `tests/env-mongodb`
- `tests/env-couchdb`
- `tests/env-opensearch`
- `tests/env-elasticsearch`
- `tests/env-cassandra`
- `tests/env-all`

## Run commands
```bash
venv/bin/python -m pytest tests/quality --env tests/env-QT -v --tb=short
venv/bin/python -m pytest tests/unit --env tests/env-UT -v --tb=short
venv/bin/python -m pytest tests/system --env tests/env-ST -v --tb=short
venv/bin/python -m pytest tests/system --env tests/env-ST-WEBUI -v --tb=short
venv/bin/python -m pytest tests/integration --env tests/env-IT -v --tb=short
venv/bin/python -m pytest tests/ --env tests/env-IT -q --tb=short
./scripts/seed-test-data.sh mongodb
./scripts/seed-test-data.sh couchdb
venv/bin/python -m pytest tests/fixtures/test_seed_data.py --env tests/env-mongodb -v --tb=short
cd /opt/iac/Development/cloud-dog-ai/cloud-dog-ai-ui-monorepo && npm --prefix apps/db-mcp run typecheck
cd /opt/iac/Development/cloud-dog-ai/cloud-dog-ai-ui-monorepo && npm --prefix apps/db-mcp run lint
cd /opt/iac/Development/cloud-dog-ai/cloud-dog-ai-ui-monorepo && npm --prefix apps/db-mcp run build
cd /opt/iac/Development/cloud-dog-ai/cloud-dog-ai-ui-monorepo && npm --prefix apps/db-mcp run e2e -- --reporter=line
```

## Latest run history
- `2026-03-24` QT: `1 passed`
  - Evidence: `working/w28a-274a-qt.log`
- `2026-03-24` UT: `8 passed`
  - Evidence: `working/w28a-274b-ut.log`
- `2026-03-24` UT1.4: `2 passed in 0.98s`
  - Evidence: `working/w28a-274c-ut14.log`
- `2026-03-24` ST1.1: `1 passed in 70.00s`
  - Evidence: `working/w28a-274a-st.log`
- `2026-03-24` ST1.2: `1 passed in 77.97s`
  - Evidence: `working/w28a-274b-st12.log`
- `2026-03-24` ST1.3: `1 passed in 2.34s`
  - Evidence: `working/w28a-274c-st13.log`
- `2026-03-24` IT1.1: `1 passed in 79.92s`
  - Evidence: `working/w28a-274b-it11.log`
- `2026-03-24` IT1.2: `1 passed in 71.42s`
  - Evidence: `working/w28a-274c-it12.log`
- `2026-03-24` Mongo targeted verification: `4 passed in 72.14s`
  - Evidence: `working/w28a-274c-targeted.log`
- `2026-03-24` full suite: `12 passed`
  - Evidence: `working/w28a-274b-tests.log`
  - Inventory evidence: `working/w28a-274b-collect.log`
- `2026-03-24` compile verification for structured filter/core tools: PASS
  - Evidence: `working/w28a-274h-r2-compileall.log`
- `2026-03-24` QT full: `1 passed in 0.04s`
  - Evidence: `working/w28a-274h-r2-qt.log`
- `2026-03-24` UT full: `16 passed in 3.03s`
  - Evidence: `working/w28a-274h-r2-ut-full.log`
- `2026-03-24` UT1.5-UT1.8 targeted: `6 passed in 0.59s`
  - Evidence: `working/w28a-274h-r2-ut.log`
- `2026-03-24` ST1.4 targeted: `1 passed in 72.67s`
  - Evidence: `working/w28a-274h-r2-st14.log`
- `2026-03-24` ST1.5 targeted: `1 passed in 73.02s`
  - Evidence: `working/w28a-274h-r2-st15.log`
- `2026-03-24` ST1.6 targeted: `1 passed in 71.97s`
  - Evidence: `working/w28a-274h-r2-st16.log`
- `2026-03-24` ST full: `6 passed in 355.56s`
  - Evidence: `working/w28a-274h-r2-st-full.log`
- `2026-03-24` IT1.3 targeted: `1 passed in 72.59s`
  - Evidence: `working/w28a-274h-r2-it13.log`
- `2026-03-24` IT1.4 targeted: `1 passed in 71.71s`
  - Evidence: `working/w28a-274h-r2-it14.log`
- `2026-03-24` IT1.5 targeted: `1 passed in 72.55s`
  - Evidence: `working/w28a-274h-r2-it15.log`
- `2026-03-24` IT full: `5 passed in 362.06s`
  - Evidence: `working/w28a-274h-r2-it-full.log`
- `2026-03-24` compile verification for search/indexing: PASS
  - Evidence: `working/w28a-274i-compileall.log`
- `2026-03-24` UT1.9 + UT1.10 targeted: `4 passed in 1.11s`
  - Evidence: `working/w28a-274i-ut.log`
- `2026-03-24` ST1.7 targeted: `1 passed in 72.72s`
  - Evidence: `working/w28a-274i-st17-rerun.log`
- `2026-03-24` IT1.6 targeted: `1 passed in 73.97s`
  - Evidence: `working/w28a-274i-it16-rerun.log`
- `2026-03-24` QT full after search/indexing: `1 passed in 0.04s`
  - Evidence: `working/w28a-274i-qt.log`
- `2026-03-24` UT full after search/indexing: `20 passed in 3.10s`
  - Evidence: `working/w28a-274i-ut-full.log`
- `2026-03-24` ST full after search/indexing: `7 passed in 431.04s`
  - Evidence: `working/w28a-274i-st-full.log`
- `2026-03-24` IT full after search/indexing: `6 passed in 439.03s`
  - Evidence: `working/w28a-274i-it-full.log`
- `2026-03-24` WebUI frontend typecheck: PASS
  - Evidence: `working/w28a-274j-ui-typecheck.log`
- `2026-03-24` WebUI frontend lint: PASS
  - Evidence: `working/w28a-274j-ui-lint.log`
- `2026-03-24` WebUI frontend build: PASS
  - Evidence: `working/w28a-274j-ui-build.log`
- `2026-03-24` WebUI frontend Playwright + axe: `9 passed in 31.0s`
  - Evidence: `working/w28a-274j-ui-e2e.log`
- `2026-03-24` WebUI service QT + UT: `24 passed in 3.62s`
  - Evidence: `working/w28a-274j-qt-ut.log`
- `2026-03-24` WebUI service ST: `8 passed in 506.53s`
  - Evidence: `working/w28a-274j-st.log`
- `2026-03-25` Mongo seed orchestration: PASS
  - Evidence: `working/w28a-274k-seed-mongodb.log`
- `2026-03-25` fixture verification: `3 passed in 8.50s`
  - Evidence: `working/w28a-274k-test-seed-data.log`
- `2026-03-25` compile verification for schema-change tooling: PASS
  - Evidence: `working/w28a-274l-compileall.log`
- `2026-03-25` QT + UT full after schema-change tooling: `27 passed in 3.30s`
  - Evidence: `working/w28a-274l-qt-ut.log`
- `2026-03-25` ST full after schema-change tooling: `8 passed in 501.45s`
  - Evidence: `working/w28a-274l-st.log`
- `2026-03-25` IT full after schema-change tooling: `7 passed in 506.19s`
  - Evidence: `working/w28a-274l-it.log`
- `2026-03-25` compile verification for CouchDB connector: PASS
  - Evidence: `working/w28a-274d-compileall.log`
- `2026-03-25` QT full after CouchDB connector: `1 passed in 0.05s`
  - Evidence: `working/w28a-274d-qt.log`
- `2026-03-25` UT full after CouchDB connector: `28 passed in 3.44s`
  - Evidence: `working/w28a-274d-ut.log`
- `2026-03-25` ST1.9 targeted: `1 passed in 0.40s`
  - Evidence: `working/w28a-274d-st19.log`
- `2026-03-25` IT1.8 targeted: `1 passed in 71.32s`
  - Evidence: `working/w28a-274d-it18.log`
- `2026-03-25` compile verification for OpenSearch connector: PASS
  - Evidence: `working/w28a-274e-compileall.log`
- `2026-03-25` QT full after OpenSearch connector: `1 passed in 0.05s`
  - Evidence: `working/w28a-274e-qt.log`
- `2026-03-25` UT1.14 targeted: `2 passed in 0.44s`
  - Evidence: `working/w28a-274e-ut14.log`
- `2026-03-25` UT full after OpenSearch connector: `30 passed in 3.47s`
  - Evidence: `working/w28a-274e-ut.log`
- `2026-03-25` ST1.10 targeted: `1 passed in 148.29s`
  - Evidence: `working/w28a-274e-st10.log`
- `2026-03-25` IT1.9 targeted: `1 passed in 73.95s`
  - Evidence: `working/w28a-274e-it19.log`
