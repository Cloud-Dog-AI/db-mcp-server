# W28A-95b DB-MCP Preprod IT/AT/QT Breadth Audit

Date: 2026-05-08
Repo: `/opt/iac/Development/cloud-dog-ai/db-mcp-server`
Return commit base: `0124152 test(db-mcp): validate preprod connector breadth W28A-95b`

## Execution Notes

- The repo provides `venv/` and does not provide `.venv/`; runs used `venv/bin/python`.
- No database containers were created. Runtime helpers use repo/preprod env contracts and fail loudly instead of launching Docker fallbacks.
- CouchDB fallback resolution now prefers `tests/env-couchdb` over `tests/env-all`, fixing the previous `tests/env-IT` HTTP 401 failure.
- `tests/integration/IT1.10_BackendConnectorMatrix/test_backend_connector_matrix.py` adds real backend-specific connector integration coverage. `tests/env-IT` collects all seven backend cases; each connector env collects only its matching backend case, so matrix logs are backend-specific without skips.

## Required Run Summaries

| Run | Log | Result |
| --- | --- | --- |
| IT preprod full | `working/it-95b-preprod-full.log` | `16 passed in 581.60s (0:09:41)` |
| AT preprod full | `working/at-95b-preprod-full.log` | `17 passed in 159.25s (0:02:39)` |
| QT full | `working/qt-95b-full.log` | `1 passed in 0.06s` |
| Matrix `tests/env-mongodb` | `working/w28a-95b-env-mongodb-it.log` | `10 passed in 579.24s (0:09:39)` |
| Matrix `tests/env-couchdb` | `working/w28a-95b-env-couchdb-it.log` | `10 passed in 581.42s (0:09:41)` |
| Matrix `tests/env-opensearch` | `working/w28a-95b-env-opensearch-it.log` | `10 passed in 581.52s (0:09:41)` |
| Matrix `tests/env-elasticsearch` | `working/w28a-95b-env-elasticsearch-it.log` | `10 passed in 578.51s (0:09:38)` |
| Matrix `tests/env-postgresql` | `working/w28a-95b-env-postgresql-it.log` | `10 passed in 579.18s (0:09:39)` |
| Matrix `tests/env-mariadb` | `working/w28a-95b-env-mariadb-it.log` | `10 passed in 580.21s (0:09:40)` |
| Matrix `tests/env-cassandra` | `working/w28a-95b-env-cassandra-it.log` | `10 passed in 591.99s (0:09:51)` |

## Failure Disposition

- No IT, AT, QT, or backend-matrix failures remain.
- No skips or xfails were used.
- Log scan found no credential-bearing URLs or known checked-in backend passwords in the W28A-95b evidence logs.

## Coverage Answer

| Backend | Real operations tested | Proving logs |
| --- | --- | --- |
| MongoDB | `validate_profile`, namespace/entity discovery, field schema, sample shapes, create/read/update/count/delete, index create/list, relationship inference | `working/it-95b-preprod-full.log`, `working/w28a-95b-env-mongodb-it.log` |
| CouchDB | `validate_profile`, namespace/entity discovery including view entity, field schema, sample shapes, create/read/update/count/delete, Mango index create/list, relationship inference | `working/it-95b-preprod-full.log`, `working/w28a-95b-env-couchdb-it.log` |
| OpenSearch | `validate_profile`, cluster/index discovery, field schema, sample shapes, create/read/update/count/delete using term queries, index-template create/list, relationship inference | `working/it-95b-preprod-full.log`, `working/w28a-95b-env-opensearch-it.log` |
| Elasticsearch | `validate_profile`, cluster/index discovery, field schema, sample shapes, create/read/update/count/delete using term queries, index-template create/list, relationship inference | `working/it-95b-preprod-full.log`, `working/w28a-95b-env-elasticsearch-it.log` |
| PostgreSQL | `validate_profile`, schema/table discovery, field schema, sample shapes, create/read/update/count/delete, index create/list, relationship API call | `working/it-95b-preprod-full.log`, `working/w28a-95b-env-postgresql-it.log` |
| MariaDB | `validate_profile`, database/table discovery, field schema, sample shapes, create/read/update/count/delete, index create/list, relationship API call | `working/it-95b-preprod-full.log`, `working/w28a-95b-env-mariadb-it.log` |
| Cassandra | `validate_profile`, keyspace/table discovery, field schema, sample shapes, create/read/update/count/delete, secondary index create/list/drop, relationship inference | `working/it-95b-preprod-full.log`, `working/w28a-95b-env-cassandra-it.log` |

Conclusion: W28A-95b now validates all provided backends at integration depth. The full IT suite proves all seven backends in one preprod run; each backend-specific matrix env also proves its corresponding backend via one real connector case plus the existing IT suite.

## Hardcoding, Skips, And Duplication

- Skips/xfails: none found in `tests/integration`, `tests/application`, or `tests/quality`.
- Docker/container hardcoding: removed from MongoDB, CouchDB, Elasticsearch, and Cassandra runtime helpers for this preprod path. Helpers now use env contracts and fail loudly.
- Server env hardcoding: integration tests resolve the active pytest `--env`.
- Stale server handling: direct IT server starters stop existing app surfaces before start, matching the safer shared helper behavior.
- Credential leakage: CouchDB and Elasticsearch request setup separates public request URLs from session/auth credentials where direct HTTP setup is required.
- Remaining duplication: direct connector IT files still have local `_start_servers`, `_stop_servers`, and `_wait` helper copies. This should be consolidated later, but it is not substituting for backend coverage.
