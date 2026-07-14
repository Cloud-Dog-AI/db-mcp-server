# Agent lessons — db-mcp-server

Last reviewed: 2026-07-14
Scope: repository-specific overlay; source lesson path `AGENT-LESSONS.md`.

## Authority and use

The binding programme rules and cross-programme lessons are in `../cloud-dog-ai-platform-standards/AGENT-LESSONS.md` and the central `RULES.md`. This file is an overlay: central authority wins on conflict. Read the exact lane instruction and current repository documentation before acting.

Mutable values such as versions, ports, endpoints, counts, branch names and lane states are not authority here. Verify them from current source, manifests, configuration and SSOT.

## Current project knowledge

### Configuration, identity and security

- **DB-MCP-SERVER-001 — 4.3 RBAC Roles.** 5 built-in roles: `admin` (all), `data_steward`, `developer`, `analyst`, `auditor`. Defined in `defaults.yaml` under `access_control.default_role_permissions`. _(Pre-refresh source: lines 185-187.)_
- **DB-MCP-SERVER-002 — 4.4 Vault Access.** Mount point: `cloud_dog_ai` (NOT `secret`) Config path: `cloud_dog_ai/data/config` Config is stored as JSON string inside a `content` field — must parse: `json.loads(d['data']['data']['content'])` Provider credentials at: `config.dev.databases.providers.{mongodb|postgres|mysql|...}` _(Pre-refresh source: lines 188-193.)_
- **DB-MCP-SERVER-003 — 5.4 WebUI Pages (18 routes).** Dashboard, Profiles, Catalogue, Entity Detail, Data Browser, Search, Relationships, Schema Planner, Audit, Users, Groups, API Keys, RBAC, Jobs, MCP Console, A2A Console, API Docs, Settings. All defined in `cloud-dog-ai-ui-monorepo/apps/db-mcp/src/routes/App.tsx`. _(Pre-refresh source: lines 229-233.)_
- **DB-MCP-SERVER-004 — 7.3 Couchbase Connector.** The Vault has a `couchbase` provider entry but no adapter exists in `src/core/connectors/`. The instruction scope mentions 8 connectors but the code has 7 (MongoDB, CouchDB, OpenSearch, Elasticsearch, Cassandra, PostgreSQL, MariaDB). Couchbase is listed in the instruction's "8 connectors" but is not implemented. _(Pre-refresh source: lines 275-277.)_

### WebUI and routes

- **DB-MCP-SERVER-005 — 5.1 Four-Server Pattern.** API (8086), Web (8087), MCP (8088), A2A (8089) — all started via `server_control.sh`. _(Pre-refresh source: lines 207-209.)_

### Testing and evidence

- **DB-MCP-SERVER-006 — 6.1 UI Monorepo.** App: `cloud-dog-ai-ui-monorepo/apps/db-mcp/` Playwright tests: `apps/db-mcp/tests/e2e/` (auth, sections, connectors, rbac specs) Internal AT tests: `tests/application/AT_WEBUI_E2E/test_webui_e2e.py` (Python + Playwright) _(Pre-refresh source: lines 245-249.)_

### Build and runtime

- **DB-MCP-SERVER-007 — 2.5 Platform Package Usage — Zero Bespoke.** All 6 platform packages are used correctly: `cloud_dog_config` — config loading via `common/config_loader.py` `cloud_dog_logging` — structured logging throughout connectors `cloud_dog_api_kit` — FastAPI app factory, error types, WebApiProxy `cloud_dog_idam` — RBACEngine, API key hashing `cloud_dog_db` — metadata/audit storage `cloud_dog_jobs` — discovery job types (rebuild, sync_profile, sync_entity) Zero `os.environ.get()` in src/, zero raw logging, zero `functools.cache`. _(Pre-refresh source: lines 88-98.)_
- **DB-MCP-SERVER-008 — 3.5 Intermittent ST Failures.** ST1.5 (binary fields), ST1.7 (search metadata), ST1.8 (web UI serving) can fail intermittently on first run due to server startup timing, MongoDB connection warmup, or search index build delays. Re-run before investigating — most pass on second attempt. _(Pre-refresh source: lines 147-149.)_
- **DB-MCP-SERVER-009 — 4.2 Backend Infrastructure (all Terraform-managed, DO NOT provision).** All credentials from Vault at `dev.databases.providers.*`. **Never spin up local DB containers (PC31).** _(Pre-refresh source: lines 172-184.)_
- **DB-MCP-SERVER-010 — 5.3 MCP Tools (45 total).** Organised in `src/servers/mcp/`: `catalog_tools.py` — 4 tools (list_namespaces, list_entities, get_entity, search) `content_tools.py` — 6 tools (read, create, update, delete, count, exists) `schema_tools.py` — 7 tools (describe_entity/fields, list_indexes, sample_shapes, change plan/apply/history) `search_tools.py` — 8 tools (metadata, content, explain_match, related + index status/sync_profile/sync_entity/rebuild) `relationship_tools.py` — 6 tools (list, get, infer, create, update, delete) `access_control_tools.py` — 12 tools (profiles CRUD, users, groups, API keys) _(Pre-refresh source: lines 217-228.)_
- **DB-MCP-SERVER-011 — 5.5 Discovery Index Pipeline.** `DiscoveryIndexService` in `core/search/discovery_index.py` builds a search index across all profiles Index covers: entity names, field names, namespace names, relationship metadata `search.metadata` tool searches the index; `search.content` searches actual data `index.rebuild` triggers a full reindex; `index.sync_profile`/`sync_entity` do incremental updates Index jobs are async via `cloud_dog_jobs` --- _(Pre-refresh source: lines 234-242.)_
- **DB-MCP-SERVER-012 — 6.2 Platform Packages.** `cloud_dog_idam` — RBACEngine, hash_api_key, key_matches `cloud_dog_jobs` — Job types: discovery.rebuild, discovery.sync_profile, discovery.sync_entity `cloud_dog_api_kit` — create_app, WebApiProxy, error types (NotFoundError, ValidationError, InternalError) `cloud_dog_db` — DatabaseSettings, build_sync_engine, probe_database `cloud_dog_config` — load_config, get_config, RuntimeConfig `cloud_dog_logging` — get_logger, structured JSON output _(Pre-refresh source: lines 250-257.)_

### Project operation

- **DB-MCP-SERVER-013 — 7.1 Job Queue.** Currently inline/memory-backed execution via `cloud_dog_jobs`. Real queue workers with persistent retry are outstanding. _(Pre-refresh source: lines 269-271.)_

## Historical provenance

The complete pre-refresh document is preserved at commit `88b1ad0e643d05c9c7549c3dfdc97b658bb1a893`, path `AGENT-LESSONS.md`, SHA-256 `ff78a07339b298d536e71e2157f9c7abe030e3c27cdc95c79856ebc8f2aa3a30`. Its 47 addressable units, including 34 historical, mutable, duplicate or heading-only units omitted from the active body, are mapped individually in the central `lesson-unit-migration.tsv` ledger.

Do not copy an old incident result back into the active body. Revalidate the underlying condition; retain the incident only as provenance when it still explains a current rule.
