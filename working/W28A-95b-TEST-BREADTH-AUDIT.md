# W28A-95b DB-MCP Preprod IT/AT/QT Breadth Audit

Date: 2026-05-08
Repo: `/opt/iac/Development/cloud-dog-ai/db-mcp-server`
Branch/head at startup: `main` / `ca5ab65 chore: W28A-90e baseline db-mcp fixes`

## Execution Notes

- The repo provides `venv/` and does not provide `.venv/`; runs used `venv/bin/python`.
- The startup gate was clean before this work (`git status -sb` returned `## main`).
- No database containers were created. Test runtime helpers were changed to use repo/preprod env contracts and fail loudly instead of launching Docker fallbacks.
- Connector-only env files are not standalone app envs. The test harness now builds `working/w28a-95b-composite-env-*` files from `tests/env-IT` plus the selected connector env so the required single-`--env` matrix can start the app and still load connector-specific variables.

## Required Run Summaries

| Run | Log | Result |
| --- | --- | --- |
| IT preprod full | `working/it-95b-preprod-full.log` | `1 failed, 8 passed in 492.96s (0:08:12)` |
| AT preprod full | `working/at-95b-preprod-full.log` | `17 passed in 160.46s (0:02:40)` |
| QT full | `working/qt-95b-full.log` | `1 passed in 0.06s` |
| Matrix `tests/env-mongodb` | `working/w28a-95b-env-mongodb-it.log` | `1 failed, 8 passed in 519.86s (0:08:39)` |
| Matrix `tests/env-couchdb` | `working/w28a-95b-env-couchdb-it.log` | `9 passed in 575.05s (0:09:35)` |
| Matrix `tests/env-opensearch` | `working/w28a-95b-env-opensearch-it.log` | `1 failed, 8 passed in 492.95s (0:08:12)` |
| Matrix `tests/env-elasticsearch` | `working/w28a-95b-env-elasticsearch-it.log` | `1 failed, 8 passed in 488.02s (0:08:08)` |
| Matrix `tests/env-postgresql` | `working/w28a-95b-env-postgresql-it.log` | `1 failed, 8 passed in 488.78s (0:08:08)` |
| Matrix `tests/env-mariadb` | `working/w28a-95b-env-mariadb-it.log` | `1 failed, 8 passed in 490.36s (0:08:10)` |
| Matrix `tests/env-cassandra` | `working/w28a-95b-env-cassandra-it.log` | `1 failed, 8 passed in 491.12s (0:08:11)` |

## Failure Disposition

- Remaining IT failure: `tests/integration/IT1.8_CouchDbMcpTools/test_couchdb_mcp_tools.py::test_couchdb_mcp_tools_crud_lifecycle`.
- Full IT and all non-CouchDB matrix envs fail because CouchDB credentials resolved through `tests/env-IT` plus fallback `tests/env-all` receive HTTP 401 from the shared CouchDB backend.
- `tests/env-couchdb` passes all integration tests, which proves the CouchDB backend itself is reachable and usable when the CouchDB-specific env contract is selected.
- OpenSearch initially failed because `tests/env-IT` omitted `DB_MCP_TEST_OPENSEARCH_URL`; the helper now resolves repo env contracts and OpenSearch passes in full IT and matrix runs.

## Coverage Answer

- MongoDB: covered by real IT CRUD (`IT1.2`) and the generic discovery/content/relationship/schema/index IT flows. AT creates WebUI profiles using the shared MongoDB URI.
- CouchDB: covered by real IT CRUD (`IT1.8`). It passes when `tests/env-couchdb` is active; it fails under `tests/env-IT` because fallback CouchDB credentials are invalid.
- OpenSearch: covered by real IT CRUD (`IT1.9`) and passes after repo-env URL resolution.
- Elasticsearch: only lightly covered by access-control profile metadata creation (`source_type: elasticsearch`). There is no real Elasticsearch CRUD/discovery IT in `tests/integration`.
- PostgreSQL: no real PostgreSQL integration coverage in `tests/integration`; connector env exists, but the matrix still executes the MongoDB/CouchDB/OpenSearch integration suite.
- MariaDB: no real MariaDB integration coverage in `tests/integration`; connector env exists, but the matrix still executes the MongoDB/CouchDB/OpenSearch integration suite.
- Cassandra: no real Cassandra integration coverage in `tests/integration`; connector env exists, but the matrix still executes the MongoDB/CouchDB/OpenSearch integration suite.

Conclusion: W28A-95b does not validate all provided backends at integration depth. It validates MongoDB, CouchDB, and OpenSearch with real CRUD paths. Elasticsearch, PostgreSQL, MariaDB, and Cassandra need dedicated integration tests or a parameterized connector matrix that invokes their real connector CRUD/list/schema paths.

## Hardcoding, Skips, And Duplication

- Skips/xfails: none found in `tests/integration`, `tests/application`, or `tests/quality`.
- Docker/container hardcoding: removed from MongoDB, CouchDB, Elasticsearch, and Cassandra runtime helpers for this preprod path. Helpers now use env contracts and fail loudly.
- Server env hardcoding: integration tests no longer hard-code `tests/env-IT` for server startup; they resolve the active pytest `--env`.
- Stale server handling: direct IT server starters now stop existing app surfaces before start, matching the safer shared helper behavior.
- Credential leakage: CouchDB failed request URLs are sanitized by separating the public base URL from session auth.
- Remaining duplication: each direct connector IT still has local `_start_servers`, `_stop_servers`, and `_wait` helper copies. This is not a behavioral failure, but it should be consolidated into `tests.helpers.core_tools_runtime` or `tests.helpers.server_runtime`.
