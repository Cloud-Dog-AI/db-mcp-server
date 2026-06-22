---
template-id: T-AGL
template-version: 1.0
applies-to: AGENT-LESSONS.md
registry: service
required: must-have
when-applicable: ""
template-last-updated: 2026-06-12
template-owner: platform-standards

project: db-mcp-server
doc-last-updated: 2026-06-18T00:00:00Z
doc-git-commit: 58fb399bb2ba144e262f97293103a7a0a19ba05d
doc-git-branch: main
doc-source-shas: []
doc-age-policy: 90d
doc-conformance-stamp: 2026-06-18T00:00:00Z
---

# Agent Lessons Learned — db-mcp-server

## Central Programme Lesson Authority

The canonical programme lessons are in `/opt/iac/Development/cloud-dog-ai/cloud-dog-ai-platform-standards/AGENT-LESSONS.md`. This repository file is a service-specific overlay only. If this file conflicts with the central programme file, the central file wins.

Before project work, every agent must read the central `RULES.md`, central `AGENT-LESSONS.md`, `AGENT-BOOTSTRAP-DIRECTIVE.md`, the live `AGENT-DISPATCH-TABLE.md`, the exact lane instruction, and this overlay. Do not copy central rules here; add only service-specific deltas and feed reusable lessons back to the central file.


**Version:** 3.1 — 2026-05-07
**Purpose:** Lessons from agent work on this service. Read BEFORE making changes.

---

## 1. Platform Alignment (BINDING)

This file extends — never overrides — the central platform doctrine. Before any work in
`db-mcp-server`, the agent MUST read:

- `cloud-dog-ai-platform-standards/RULES.md` (latest version)
- `cloud-dog-ai-platform-standards/AGENT-LESSONS.md` (latest version)
- `cloud-dog-ai-platform-standards/AGENT-BOOTSTRAP-DIRECTIVE.md` (latest version)
- This file

Fix-what-you-find is the default (central `RULES.md §14.3` + central `AGENT-LESSONS.md §6.81`/§6.101).
"Not a fix lane" language is invalid unless the instruction is explicitly READ-ONLY/AUDIT-ONLY.

The lessons below capture `db-mcp-server`-specific knowledge only. If you find yourself
re-stating a central rule, stop and link to central instead.

## 2. Code

### 2.1 IDAM Compliance (W28A-705)
- APIKeyAuthoriser wrapper class was eliminated. Replaced with a simple `verify_api_key()` function in `common/auth.py` that delegates directly to `AccessControlService.verify_api_key()`.
- AccessControlService in `core/access_control/service.py` already uses `cloud_dog_idam.api_keys.hashing.hash_api_key` and `key_matches` — the refactoring only removed the unnecessary wrapper class.
- `common/runtime.py` uses a thin `_AuthBridge` class to maintain the `runtime.auth.verify_api_key(key)` call pattern expected by route handlers.
- Custom domain models (AccessUser, AccessGroup, AccessApiKey) in `core/access_control/models.py` are project-specific extensions — they were flagged by the IDAM scanner but serve a legitimate purpose (DB provider roles, profile-scoped access).

### 2.2 WebUI Component Alignment (W28A-715, W28A-965)
- UI component text CHANGES over time as pages are refined. Test assertions that check for specific panel titles, section headings, or button text WILL break when the UI is updated.
- Always verify assertions against the ACTUAL component source before claiming a test failure is a "code bug". Read the `.tsx` file to find the real text.
- Key mappings discovered in W28A-965:
  - SettingsPage: sections are "Service Info", "Server Configuration", "Service-Specific" — NOT "Operations"
  - CataloguePage: heading is "Profile scope" — NOT just "Scope". Namespace table has no separate heading.
  - SearchPage: explain panel is "Matched components" — NOT "Explain match"
  - RelationshipsPage: create button is "Create manual relationship" — NOT "Create curated relationship"
  - EntityDetailPage: panel title is "Sample document shapes" — NOT "Sample shapes"
  - DataBrowserPage: uses `<DataTable>` without `data-testid` attribute — check for `<table>` element presence instead

### 2.3 All 8 Connectors ARE Implemented
The README previously claimed CouchDB, OpenSearch, Elasticsearch, and Cassandra were "Not Yet Implemented". This was FALSE. All 8 connectors have full adapter implementations:
- **MongoDB** — `src/core/connectors/mongodb/adapter.py` (489 lines)
- **CouchDB** — `src/core/connectors/couchdb/adapter.py` (853 lines)
- **OpenSearch** — `src/core/connectors/opensearch/adapter.py` (615 lines)
- **Elasticsearch** — `src/core/connectors/elasticsearch/adapter.py` (843 lines)
- **Cassandra** — `src/core/connectors/cassandra/adapter.py` (771 lines)
- **PostgreSQL** — `src/core/connectors/relational.py` shared module + `postgresql/adapter.py`
- **MariaDB** — `src/core/connectors/relational.py` shared module + `mariadb/adapter.py`

**Never trust README "Not Yet Implemented" claims — grep the source.**

### 2.4 API Prefix & PS-92 Base Path (updated 2026-05-06, basepath fix)
db-mcp uses `api_server.base_path: "/v1"` in `defaults.yaml`. The Python fallback in `src/common/base_paths.py` also defaults to `"/v1"`. Traefik strips `/api` from incoming requests before forwarding to the API server on port 8086, so the API server registers routes at `/v1/...` (e.g. `/v1/users`, `/v1/profiles`). The external-facing path is `/api/v1/users` (Traefik strips `/api`, API receives `/v1/users`).

The web server's `/api` proxy mirrors Traefik's strip: `strip_prefix="/api"` so that local-dev and system-test paths (`/api/v1/ping`) also work correctly. The `/webapi` proxy path does NOT add a rewrite prefix -- after stripping `/webapi`, the path is already `/v1/...` which matches the API routes directly.

**PS-92 status:** Implemented. All four surfaces have `base_path` in `defaults.yaml`: API=`/v1`, Web=`""`, MCP=`/mcp`, A2A=`/a2a`.

### 2.5 Platform Package Usage — Zero Bespoke
All 6 platform packages are used correctly:
- `cloud_dog_config` — config loading via `common/config_loader.py`
- `cloud_dog_logging` — structured logging throughout connectors
- `cloud_dog_api_kit` — FastAPI app factory, error types, WebApiProxy
- `cloud_dog_idam` — RBACEngine, API key hashing
- `cloud_dog_db` — metadata/audit storage
- `cloud_dog_jobs` — discovery job types (rebuild, sync_profile, sync_entity)

Zero `os.environ.get()` in src/, zero raw logging, zero `functools.cache`.

### 2.6 API-REFERENCE.md Uplift (W28A-997)
The original `docs/API-REFERENCE.md` was a 31-line skeleton with aspirational text. W28A-997 rewrote it to 243 lines covering all 4 surfaces:
- API REST: 35 endpoints (4 health + 8 operational + 20 access-control + 3 auto-doc)
- MCP: 45 tools across 7 registries (access_control, catalog, schema, content, relationship, audit, search)
- A2A: 6 HTTP + 2 WebSocket + 4 skills
- Web: 6 direct + 5 proxy families

Every entry was verified against source code. No aspirational/invented entries.

### 2.7 Traceability Matrix Gap Triage (W28A-1001)
The W28A-871 matrix had 5 GAP + 4 PARTIAL items (A4, C2, D2, D3, E3, B2, C1, E2, F2). All 9 were triaged as ACCEPTED because:
- Backend functionality IS tested at API/integration level (ST, IT suites)
- The gaps are UI-level assertions (PS-77 DataTable, cross-page navigation, role×tool matrices)
- These UI-level tests are E2E scope (W28A-943), not unit/integration scope
- No requirement was silently deleted — each has an explicit rationale in TESTS.md

---

## 3. Test Environment

### 3.1 Test Env File Patterns
- Tests require `--env tests/env-{TIER}` flag — will fail without it
- Connector-specific tests need TWO env files: `--env tests/env-ST --env tests/env-{connector}`
  - Example: `pytest tests/system/ST1.14_PostgreSQLConnector/ --env tests/env-ST --env tests/env-postgresql`
- The connector env files set `CLOUD_DOG__CONNECTORS__{CONNECTOR}__DEFAULT_URI`
- db-mcp uses `venv/` not `.venv/` — check before running

### 3.2 MongoDB Test URI Mismatch (W28A-965 fix)
IT1.2 was failing because the test inserted data into a LOCAL test container (`mongodb://127.0.0.1:27018`) but the server connected to the env-IT MongoDB (`mongodb://mongo0.app.vpc0.cloud-dog.net:27017`). **Different MongoDB instances.**

Fix: `_resolve_mongodb_uri()` reads the URI from the env file so test data insertion and server use the SAME instance. Always ensure test setup and server connect to the SAME backend.

### 3.3 PostgreSQL/MariaDB Connector Credentials
The connector env files need real credentials from Vault, not placeholders:
- PostgreSQL: `providers.postgres` → `db2.app.vpc0.cloud-dog.net:5432`, user `postgres`
- MariaDB: `providers.mysql` → `db1.app.vpc0.cloud-dog.net:3306`, user `root`
- These are the provider-level credentials (admin access), suitable for connector testing
- The URI format matters: PostgreSQL uses `postgresql://`, MariaDB uses `mariadb+pymysql://`

### 3.4 Test Counts (W28A-966a baseline, 2026-04-21)
| Suite | Count | Duration |
|-------|-------|----------|
| UT | 53 | ~7s |
| ST (all connectors) | 16 | ~770s |
| IT | 9 | ~730s |
| AT (E2E) | 17 | ~155s |
| **Total** | **95** | |

### 3.5 Intermittent ST Failures
ST1.5 (binary fields), ST1.7 (search metadata), ST1.8 (web UI serving) can fail intermittently on first run due to server startup timing, MongoDB connection warmup, or search index build delays. Re-run before investigating — most pass on second attempt.

### 3.6 `server_control.sh` restart hygiene matters (2026-05-06)
- `stop all` cannot rely only on pidfiles. When a prior local run leaves a listener behind, the next `start` can fail with `ERROR: [Errno 98] ... address already in use` even though the pidfile path is clean.
- The practical fix is port-based cleanup on shutdown as well as pid-based cleanup. `fuser -n tcp <port>` is available on this host and is reliable enough for db-mcp's fixed local ports 8086-8089.
- Detached server launch via shell job-control (`nohup ... &` / `setsid ... &`) was materially less stable than foreground startup in this environment. A Python `subprocess.Popen(..., start_new_session=True)` launcher is more predictable for local test orchestration because it avoids shell job reaping edge cases.
- The restart-heavy ST cases are sensitive to over-starting surfaces they do not use. API/MCP tests should not treat web/a2a startup failures as product regressions when the test only exercises `/v1/*` and `/mcp/*`.

### 3.7 W28A-88d current blocker shape (2026-05-07)
- The W28A-88d sweep did NOT finish green. Treat any older "full regression green" claim in this repo as historical, not current.
- Current local blocker is still repeated detached local surface startup under system-test orchestration, not a cleanly isolated application assertion failure.
- `start_api_server.py` is stable in the foreground, but detached API/MCP startup through `server_control.sh` has been intermittently failing during restart-heavy test sequences.
- `ST1.1` and connector-specific STs can pass while later restart-heavy API/MCP system tests still fail. Do not assume a green early ST segment means the process manager problem is gone.
- Latest honest status and evidence for this sweep is in `working/W28A-88d-REPORT.md`.

---

## 4. Infrastructure

### 4.1 Ports
- API: 8086, Web: 8087, MCP: 8088, A2A: 8089
- Preprod: `dbmcpserver0.cloud-dog.net`
- Terraform: `docker_image.dbmcpserver`, `docker_container.dbmcpserver0`

### 4.2 Backend Infrastructure (all Terraform-managed, DO NOT provision)
| Backend | Host | Port |
|---------|------|------|
| MongoDB | mongo0.app.vpc0.cloud-dog.net | 27017 |
| CouchDB | couchdb0.app.vpc0.cloud-dog.net | 5984 |
| OpenSearch | opensearch0.app.vpc0.cloud-dog.net | 9200 |
| Elasticsearch | elastic0.app.vpc0.cloud-dog.net | 9200 |
| Cassandra | cassandra0.app.vpc0.cloud-dog.net | 9042 |
| PostgreSQL | db2.app.vpc0.cloud-dog.net | 5432 |
| MariaDB | db1.app.vpc0.cloud-dog.net | 3306 |

All credentials from Vault at `dev.databases.providers.*`. **Never spin up local DB containers (PC31).**

### 4.3 RBAC Roles
5 built-in roles: `admin` (all), `data_steward`, `developer`, `analyst`, `auditor`. Defined in `defaults.yaml` under `access_control.default_role_permissions`.

### 4.4 Vault Access
- Mount point: `cloud_dog_ai` (NOT `secret`)
- Config path: `cloud_dog_ai/data/config`
- Config is stored as JSON string inside a `content` field — must parse: `json.loads(d['data']['data']['content'])`
- Provider credentials at: `config.dev.databases.providers.{mongodb|postgres|mysql|...}`

### 4.5 Docker Build
- Build script: `bash docker-build.sh`
- Registry: `registry.cloud-dog.net:443/cloud-dog/db-mcp-server:latest`
- Image uses `python:3.12-slim`, needs Vault CA cert at build time
- Terraform target: `docker_image.dbmcpserver` + `docker_container.dbmcpserver0`

### 4.6 Multi-Agent Conflicts
When multiple agents run on the same server, they can fight over notification-agent ports (8020-8023). Agent sessions from the dispatch table (W28A-925, 928b, 930b) may auto-restart notification-agent with different env files, causing 401 key mismatches and Connection Refused errors for other agents' tests. Always check `pgrep -af start_api_server` before running IT tests that depend on shared services.

---

## 5. Architecture

### 5.1 Four-Server Pattern
API (8086), Web (8087), MCP (8088), A2A (8089) — all started via `server_control.sh`.

### 5.2 Connector Architecture
- `ConnectorManager` in `core/connectors/service.py` dispatches to per-provider adapters
- Base adapter: `core/connectors/base.py` — defines the interface (list_namespaces, list_entities, describe_entity, read_data, etc.)
- Relational adapters (PostgreSQL, MariaDB) share `core/connectors/relational.py` — a SQLAlchemy-based base that both extend
- MongoDB adapter is standalone (489 lines) with its own service layer in `mongodb/service.py`
- Profile-based access: each profile binds to one connector type + connection + permissions

### 5.3 MCP Tools (45 total)
Organised in `src/servers/mcp/`:
- `catalog_tools.py` — 4 tools (list_namespaces, list_entities, get_entity, search)
- `content_tools.py` — 6 tools (read, create, update, delete, count, exists)
- `schema_tools.py` — 7 tools (describe_entity/fields, list_indexes, sample_shapes, change plan/apply/history)
- `search_tools.py` — 8 tools (metadata, content, explain_match, related + index status/sync_profile/sync_entity/rebuild)
- `relationship_tools.py` — 6 tools (list, get, infer, create, update, delete)
- `access_control_tools.py` — 12 tools (profiles CRUD, users, groups, API keys)
- `audit_tools.py` — 2 tools (list/get events)
- `mongodb_tools.py` — MongoDB-specific tools (built separately, used by A2A surface)
- `tool_rbac_audit.py` — RBAC enforcement + audit middleware with `TOOL_RBAC_MAP` covering all 45 tools

### 5.4 WebUI Pages (18 routes)
Dashboard, Profiles, Catalogue, Entity Detail, Data Browser, Search, Relationships, Schema Planner, Audit, Users, Groups, API Keys, RBAC, Jobs, MCP Console, A2A Console, API Docs, Settings.

All defined in `cloud-dog-ai-ui-monorepo/apps/db-mcp/src/routes/App.tsx`.

### 5.5 Discovery Index Pipeline
- `DiscoveryIndexService` in `core/search/discovery_index.py` builds a search index across all profiles
- Index covers: entity names, field names, namespace names, relationship metadata
- `search.metadata` tool searches the index; `search.content` searches actual data
- `index.rebuild` triggers a full reindex; `index.sync_profile`/`sync_entity` do incremental updates
- Index jobs are async via `cloud_dog_jobs`

---

## 6. Related Projects

### 6.1 UI Monorepo
- App: `cloud-dog-ai-ui-monorepo/apps/db-mcp/`
- Playwright tests: `apps/db-mcp/tests/e2e/` (auth, sections, connectors, rbac specs)
- Internal AT tests: `tests/application/AT_WEBUI_E2E/test_webui_e2e.py` (Python + Playwright)

### 6.2 Platform Packages
- `cloud_dog_idam` — RBACEngine, hash_api_key, key_matches
- `cloud_dog_jobs` — Job types: discovery.rebuild, discovery.sync_profile, discovery.sync_entity
- `cloud_dog_api_kit` — create_app, WebApiProxy, error types (NotFoundError, ValidationError, InternalError)
- `cloud_dog_db` — DatabaseSettings, build_sync_engine, probe_database
- `cloud_dog_config` — load_config, get_config, RuntimeConfig
- `cloud_dog_logging` — get_logger, structured JSON output

### 6.3 Platform Standards
- PS-71: IDAM (users, groups, API keys, RBAC)
- PS-73: Settings page structure
- PS-77: WebUI chrome (login, dashboard, menu, session)
- PS-78: File lifecycle (W28A-883 addendum — outstanding)
- PS-92: Configurable base paths (W28A-969 — standard defined, implementation pending W28A-970)

---

## 7. Known Issues & Outstanding Items

### 7.1 Job Queue
Currently inline/memory-backed execution via `cloud_dog_jobs`. Real queue workers with persistent retry are outstanding.

### 7.2 PS-78 File Lifecycle
W28A-883 addendum requires file upload/download/browser surfaces, MCP file tools, A2A file conventions, and WebUI file management. Not yet implemented.

### 7.3 Couchbase Connector
The Vault has a `couchbase` provider entry but no adapter exists in `src/core/connectors/`. The instruction scope mentions 8 connectors but the code has 7 (MongoDB, CouchDB, OpenSearch, Elasticsearch, Cassandra, PostgreSQL, MariaDB). Couchbase is listed in the instruction's "8 connectors" but is not implemented.

### 7.4 PS-92 Base Path -- IMPLEMENTED (2026-05-06)
All four surfaces now have `base_path` in `defaults.yaml`: API=`/v1`, Web=`""`, MCP=`/mcp`, A2A=`/a2a`. Python fallbacks in `src/common/base_paths.py` match. Traefik strips `/api` before forwarding to the API server, so `base_path` must NOT include `/api`. See section 1.4 for full details.

### 7.5 Traceability Matrix — 9 Items Accepted
5 GAP + 4 PARTIAL items from W28A-871 were triaged in W28A-1001 as ACCEPTED. All are UI-level E2E assertions deferred to W28A-943. Backend functionality is fully tested. See TESTS.md for per-item rationale.

### 7.7 Preprod PW testing requires E2E_WEB_PASSWORD=OrangeRiverTable (2026-05-06)

**Origin:** PW rerun wave 2026-05-06. Without `E2E_WEB_PASSWORD=OrangeRiverTable`, all auth-gated tests fail at login. The fixture reads this env var for preprod credential injection. Also set `E2E_BASE_URL=https://dbmcpserver0.cloud-dog.net` and `E2E_USE_LOCAL_SERVER=0`. Full env block:
```bash
E2E_BASE_URL=https://dbmcpserver0.cloud-dog.net E2E_USE_LOCAL_SERVER=0 E2E_WEB_PASSWORD=OrangeRiverTable
```

### 7.8 OpenSearch shard limit — A142 cleanup resolved (2026-05-06)

OpenSearch at `opensearch0.app.vpc0.cloud-dog.net:1201` was at 999/1000 shards, blocking new index creation (HTTP 400). A142 cleaned test-detritus indices, reducing to 22 shards. Shard limit raised to 2000 as safety net. Post-cleanup, db-mcp PW score improved from ~91% to **100%** (11/11).

### 7.6 API-REFERENCE.md Thin Spots
While uplifted from 31→243 lines (W28A-997), the doc could benefit from more detailed request/response schema examples for the 45 MCP tools. Current coverage is tabular (method, path, auth, reqs) without full JSON schema definitions.

### 7.9 Traefik stripprefix / base_path alignment fix (2026-05-06)

> See platform AGENT-LESSONS.md §6.37 for the cross-service rule.

**Root cause:** Traefik has `stripprefix.prefixes=/api` on the `dbmcpserver0_api_path` router (priority 200). It strips `/api` from incoming requests before forwarding to the API server on port 8086. The old `api_server.base_path="/api/v1"` meant routes were registered at `/api/v1/users`. After Traefik stripped `/api`, the API server received `/v1/users` but had no route there -- 404. Only the doubled path `/api/api/v1/users` worked.

**Fix:** Changed `api_server.base_path` from `/api/v1` to `/v1` in `defaults.yaml` and the Python fallback in `src/common/base_paths.py`. Also fixed the web server's `/api` proxy to strip `/api` (matching Traefik) and removed the webapi rewrite prefix (no longer needed since the base_path IS the post-strip path).

**Files changed:** `defaults.yaml`, `src/common/base_paths.py`, `src/servers/web/app.py`, `scripts/prepare_ui_test_env.py`, and 7 test files (UT1.2, ST1.2, IT1.1, IT1.2, IT1.8, IT1.9, AT_WEBUI_E2E, helpers/core_tools_runtime.py).

**Key rule:** When Traefik strips `/api`, the API server's `base_path` must NOT include `/api`. Use `/v1`, not `/api/v1`. This applies to every service where Traefik has a `stripprefix.prefixes=/api` middleware.

**Diagnostic:** If `curl /api/api/v1/endpoint` returns 200 but `curl /api/v1/endpoint` returns 404, the base_path includes the Traefik-stripped prefix.
