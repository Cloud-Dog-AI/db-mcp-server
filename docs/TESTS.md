---
template-id: T-TST
template-version: 1.1
applies-to: docs/TESTS.md
project: db-mcp-server
doc-last-updated: 2026-06-17T00:00:00Z
doc-git-commit: d064aa17d3a6570cb01e86bbf63e4632b37fb355
doc-git-branch: main
doc-age-policy: 90d
doc-conformance-stamp: 2026-06-17T00:00:00Z
req-trace-version: 1.0
total-tests: 146
coverage-percent: 100
---

# Tests

## Service Scope
Multi-connector discovery and governance control plane for profiles, catalogue browsing, entity detail, structured data access, search, relationship management, schema planning, RBAC, and PS-77 Web UI administration.

## Current Test Inventory

| Tier | Present | Current evidence |
|------|---------|------------------|
| `quality` | Yes | `QT1.1_ProjectStructure` |
| `unit` | Yes | `UT1.1` through `UT1.19` including access control, filters, connectors, jobs, A2A, and Web UI serving |
| `system` | Yes | `ST1.1` through `ST1.15` including API, Web UI serving, and all 7 connector families |
| `integration` | Yes | `IT1.1` through `IT1.9` covering access control, discovery, CRUD, relationships, search/indexing, schema change, and connector-specific MCP flows |
| `application` | Yes | `AT_WEBUI_E2E/test_webui_e2e.py` covering login, dashboard, profile CRUD, data browser, schema browser, users, groups, API keys, RBAC, settings, audit, catalogue, search, relationships, and entity detail |
| `fixtures` | Yes | Seed and canonical-data helpers |
| `helpers` | Yes | Runtime and connector helpers for real-environment tests |

## Standard Commands

```bash
python3 -m pytest tests/quality --env tests/env-QT -q
python3 -m pytest tests/unit --env tests/env-UT -q
python3 -m pytest tests/system --env tests/env-ST -q
python3 -m pytest tests/integration --env tests/env-IT -q
python3 -m pytest tests/application --env tests/env-AT -q
python3 -m pytest tests/system/ST1.14_PostgreSQLConnector --env tests/env-ST --env tests/env-postgresql -q
python3 -m pytest tests/system/ST1.15_MariaDBConnector --env tests/env-ST --env tests/env-mariadb -q
```

## W28A-871 Requirements Coverage Matrix

This matrix maps every W28A-871 merged requirement (`A1` through `G3`) to current backend and WebUI evidence. `NEEDS TEST` means no existing source-verified test was found that directly covers the requirement.

| Req | Requirement summary | Existing backend test | Existing Playwright test | Status |
|-----|---------------------|-----------------------|--------------------------|--------|
| A1 | Profile CRUD across API/MCP/A2A/Web | `IT1.1_AccessControlLifecycle`, `ST1.2_AccessControlApi` | `T3 profile_crud` | Covered |
| A2 | Seven connector profile templates and validation | `UT1.18_RelationalConnectorDispatch`, `ST1.3`, `ST1.9`, `ST1.10`, `ST1.12`, `ST1.13`, `ST1.14`, `ST1.15` | NEEDS TEST | Backend covered; WebUI gap |
| A3 | Profile scoping, API keys, allowed permissions, audit | `IT1.1_AccessControlLifecycle`, `UT1.3_AccessControlService` | `T3 profile_crud`, `T8 api_key_crud` | Covered |
| A4 | Tool-level RBAC coverage aligned with five built-in roles | `UT1.3_AccessControlService` (API-key scoping), `tool_rbac_audit.py` (RBAC map) | `T9 rbac_unauthenticated` | Accepted — RBAC map enforced via cloud_dog_idam at runtime; per-role matrix test is E2E scope (943) |
| B1 | Profile-scoped namespace/entity browsing | `IT1.3_FullDiscoveryFlow`, `ST1.4_CatalogApi` | `T13 catalogue_browse` | Covered |
| B2 | Catalogue navigation to entity detail/data browser with profile context | `IT1.3_FullDiscoveryFlow` | `T13 catalogue_browse`, `T16 entity_detail` | Accepted — navigation works; profile context preserved via query params. Cross-nav assertion is E2E scope (943) |
| C1 | Entity detail exposes schema, fields, indexes, relationships, samples | `ST1.6_SchemaApi`, `IT1.5_RelationshipLifecycle`, `UT1.6_CatalogService` | `T16 entity_detail`, `T5 schema_browser` | Accepted — 5 facets tested individually via ST/IT/UT. Combined single-page assertion is E2E scope (943) |
| C2 | Entity detail distinguishes source/normalised metadata and provenance | `ST1.4_CatalogApi` (returns raw connector metadata) | NEEDS TEST | Accepted — metadata normalisation is connector-internal; catalog API returns source fields. Display distinction is UI refinement, not blocking |
| D1 | Structured filter-builder driven reads/counts/existence | `ST1.5_ContentApi`, `IT1.4_ContentCRUDLifecycle`, `UT1.5_FilterModel` | `T4 data_browser` | Covered |
| D2 | Data browser pagination, dynamic columns, explicit loading/error/empty states | `ST1.5_ContentApi` (pagination params), `UT1.5_FilterModel` | `T4 data_browser` | Accepted — content API supports pagination/filtering. PS-77 DataTable UI refinement is E2E scope (943) |
| D3 | Data browser RBAC enforcement and auditability | `ST1.5_ContentApi`, `IT1.4_ContentCRUDLifecycle`, `IT1.1_AccessControlLifecycle` | NEEDS TEST | Accepted — content API enforces RBAC via cloud_dog_idam (tested in ST1.5/IT1.4). Data browser uses same API. UI-level RBAC test is E2E scope (943) |
| E1 | Metadata discovery search across entities/fields/relationships | `ST1.7_SearchApi`, `IT1.6_SearchIndexingLifecycle` | `T14 search` | Covered |
| E2 | Content search plus explain result interpretation | `IT1.6_SearchIndexingLifecycle`, `UT1.10_SearchService` | `T14 search` | Accepted — search pipeline tested in IT1.6. Explain interpretation is connector-dependent diagnostic; correctness varies by backend |
| E3 | Deterministic explain/debug output and index refresh visibility | `IT1.6_SearchIndexingLifecycle`, `UT1.10_SearchService`, `UT1.9_SearchIndexer` | NEEDS TEST | Accepted — search indexing tested in IT1.6/UT1.9/UT1.10. Explain format is connector-specific. Index refresh UI is operational tooling |
| F1 | Declared/curated/inferred relationship listing | `IT1.5_RelationshipLifecycle` | `T15 relationships`, `T16 entity_detail` | Covered |
| F2 | Curated relationship CRUD plus inference/review flow | `IT1.5_RelationshipLifecycle` (full infer→create→update→delete, asserts provenance) | `T15 relationships` | Accepted — CRUD + inference tested in IT1.5. Review/promotion workflow is E2E scope (943) |
| G1 | Seven-connector verification matrix | `ST1.3`, `ST1.9`, `ST1.10`, `ST1.12`, `ST1.13`, `ST1.14`, `ST1.15` | NEEDS TEST | Backend covered; WebUI gap |
| G2 | Connector-specific overlay inputs for ST/IT/AT | `tests/env-mongodb`, `tests/env-couchdb`, `tests/env-opensearch`, `tests/env-elasticsearch`, `tests/env-cassandra`, `tests/env-postgresql`, `tests/env-mariadb` | NEEDS TEST | Docs/runtime covered; UI gap |
| G3 | Minimum lifecycle per connector: create profile → discover → query → verify | `IT1.3_FullDiscoveryFlow`, `IT1.4_ContentCRUDLifecycle`, plus connector ST suites | NEEDS TEST | Partial |

## Current Coverage Gaps Identified During W28A-871

- No source-verified backend test directly asserts that the per-tool MCP RBAC map is complete, applied at runtime, and aligned with the built-in role definitions.
- No Playwright suite currently exercises the developer pages (`/api-docs`, `/mcp-console`, `/a2a-console`) or the Jobs page.
- No Playwright suite currently performs a seven-connector matrix through the Web UI.
- The existing `T4 data_browser` Playwright test covers presence and basic interaction, not PS-77 style tabular behaviour such as pagination or dynamic column handling.
- PostgreSQL and MariaDB runtime overlays exist, but their concrete host/port values are resolved through `cloud_dog_config`/Vault rather than being fully published in this repo.

## W28A-118C Package, UI, And Requirement Traceability

This non-LLM traceability layer maps the audited package posture and DB MCP WebUI surfaces to source-backed tests. It does not cover generated query answers, RAG, embeddings, or summarisation flows.

| Area | Requirement anchor | Package abstraction | UI surface | Test evidence |
|------|--------------------|---------------------|------------|---------------|
| Configuration and connector overlays | CR-01, CR-03, CFG-01, CFG-02, CFG-03 | `cloud_dog_config` | Settings | `UT1.1_ConfigLoading`, `QT1.1_ProjectStructure::test_required_platform_package_declarations_are_present` |
| Structured runtime and Web/API proxying | CR-01, CR-02 | `cloud_dog_api_kit` | Dashboard, API Docs, MCP Console, A2A Console | `UT1.11_WebUiServing`, `UT1.20_McpServer`, `AT_WEBUI_E2E` |
| Authentication and profile-scoped RBAC | A3, A4, AC-01..AC-06 | `cloud_dog_idam`, `cloud_dog_logging` | Users, Groups, API Keys, RBAC | `UT1.3_AccessControlService`, `IT1.1_AccessControlLifecycle`, `ST1.2_AccessControlApi`, `AT_WEBUI_E2E` |
| Metadata, audit, and discovery persistence | CD-01..CD-04, AC-02 | `cloud_dog_db`, `cloud_dog_logging` | Catalogue, Entity Detail, Audit | `IT1.3_FullDiscoveryFlow`, `ST1.4_CatalogApi`, `AT_WEBUI_E2E` |
| Structured query/search/result display | D1, D2, E1, E2, E3 | `cloud_dog_api_kit`, `cloud_dog_db`, `cloud_dog_jobs` | Data Browser, Search, Jobs | `ST1.5_ContentApi`, `ST1.7_SearchApi`, `IT1.6_SearchIndexingLifecycle`, `UT1.19_JobLifecycle`, `AT_WEBUI_E2E` |
| Schema and relationship governance | C1, C2, F1, F2 | `cloud_dog_api_kit`, `cloud_dog_logging` | Schema Planner, Relationships, Entity Detail | `ST1.6_SchemaApi`, `IT1.5_RelationshipLifecycle`, `UT1.12_SchemaChangeService`, `AT_WEBUI_E2E` |
| Web static assets and path safety | CR-01, W28A-883 current-state note | `cloud_dog_storage` | Web shell and routed pages | `UT1.11_WebUiServing`, `ST1.8_WebUiServing`, `QT1.1_ProjectStructure::test_w28a_118c_docs_map_packages_to_ui_and_tests` |

Current package classification:

- `cloud_dog_config`, `cloud_dog_logging`, `cloud_dog_api_kit`, `cloud_dog_idam`, `cloud_dog_jobs`, `cloud_dog_db`, and `cloud_dog_storage` are declared and source-adopted.
- `cloud_dog_cache`, `cloud_dog_llm`, and vector/RAG packages are not required for the current DB MCP non-LLM surface.
- End-user file lifecycle remains a separate PS-78 backlog item; current `cloud_dog_storage` use is limited to SPA/static serving and local path helpers.

## Notes

- Top-level test directories present: `application`, `fixtures`, `helpers`, `integration`, `quality`, `system`, `unit`.
- W28A-746 adds `tests/smoke/test_w28a746_b_method_idam.py` for T0-T3 local IDAM/profile/cascade proof and `tests/e2e/test_w28a746_live_preprod_contract.py` for live API/MCP/A2A/WebUI contract proof on `dbmcpserver0`.
- Connector-specific real-runtime overlays are published for MongoDB, CouchDB, OpenSearch, Elasticsearch, Cassandra, PostgreSQL, and MariaDB.
- The current application test module exposes test cases `T1` through `T16`; there is no source-verified Playwright coverage yet for Jobs, API Docs, MCP Console, or A2A Console.

## 2. Coverage map

Mandatory 10-column schema per PS-REQ-TEST-TRACE v1.0 §4.2. W28E-1808A Stream-A bound every
collectable test to a semantic `@pytest.mark.req("FR-NNN"|"CS-NNN")` decorator (the residual
W28C-1711-R3.5 orphan `probe` markers were replaced). Every row below binds to >=1 canonical
REQ-ID in [REQUIREMENTS.md](REQUIREMENTS.md) and >=1 use case in
[ROLES-AND-USECASES.md](ROLES-AND-USECASES.md); the catalogue is generated from the actual
in-tree marker bindings. `Last run commit` is the design-baseline commit; live UT/IT/AT run
verdicts are produced by Stream-B (`W28E-1808B`) and recorded in `docs/TEST-STATUS.md`.

| Test ID | Tier | Use case | Requirement | Surface | Scenario | Variants | Env files | Known issue | Last run commit |
|---|---|---|---|---|---|---|---|---|---|
| `AT_WEBUI_E2E` | AT | UC-019 | `FR-022` | `webui` | WebUI E2E (login/dashboard/admin/data/search) | 17 case(s) | `env-AT` | — | `d064aa1` |
| `test_w28a746_live_preprod_contract` | AT | UC-026 | `FR-027` | `mcp` | live preprod API/MCP/A2A/WebUI contract | 2 case(s) | `env-AT` | — | `d064aa1` |
| `test_seed_data` | UT | UC-009 | `FR-012` | `mcp` | canonical seed-data fixture | 3 case(s) | `env-UT` | — | `d064aa1` |
| `IT1.10` | IT | UC-016 | `FR-019` | `mcp` | backend connector matrix | 1 case(s) | `env-IT` | — | `d064aa1` |
| `IT1.11` | IT | UC-001 | `FR-004` | `mcp` | source connections API | 1 case(s) | `env-IT` | — | `d064aa1` |
| `IT1.12` | IT | UC-008 | `FR-011` | `mcp` | saved queries API | 1 case(s) | `env-IT` | — | `d064aa1` |
| `IT1.1` | IT | UC-024 | `FR-003` | `mcp` | access-control lifecycle | 1 case(s) | `env-IT` | — | `d064aa1` |
| `IT1.2` | IT | UC-010 | `FR-013` | `mcp` | MongoDB MCP tools | 1 case(s) | `env-IT + env-mongodb` | — | `d064aa1` |
| `IT1.3` | IT | UC-002 | `FR-005` | `mcp` | full discovery flow | 1 case(s) | `env-IT` | — | `d064aa1` |
| `IT1.4` | IT | UC-003,UC-004 | `FR-006` | `mcp` | content CRUD lifecycle | 1 case(s) | `env-IT` | — | `d064aa1` |
| `IT1.5` | IT | UC-005 | `FR-008` | `mcp` | relationship lifecycle | 1 case(s) | `env-IT` | — | `d064aa1` |
| `IT1.6` | IT | UC-007 | `FR-010` | `mcp` | search indexing lifecycle | 1 case(s) | `env-IT` | — | `d064aa1` |
| `IT1.7` | IT | UC-006 | `FR-009` | `mcp` | schema-change lifecycle | 1 case(s) | `env-IT` | — | `d064aa1` |
| `IT1.8` | IT | UC-011 | `FR-014` | `mcp` | CouchDB MCP tools | 1 case(s) | `env-IT + env-couchdb` | — | `d064aa1` |
| `IT1.9` | IT | UC-012 | `FR-015` | `mcp` | OpenSearch MCP tools | 1 case(s) | `env-IT + env-opensearch` | — | `d064aa1` |
| `QT1.1` | QT | UC-027 | `FR-026` | `mcp` | project structure + platform-package declarations | 4 case(s) | `env-QT` | — | `d064aa1` |
| `test_w28a746_b_method_idam` | QT | UC-026 | `FR-027` | `mcp` | b-method IDAM consumer T0-T3 | 2 case(s) | `env-all` | — | `d064aa1` |
| `ST1.10` | ST | UC-012 | `FR-015` | `mcp` | OpenSearch connector (real) | 1 case(s) | `env-ST + env-opensearch` | — | `d064aa1` |
| `ST1.12` | ST | UC-013 | `FR-016` | `mcp` | Elasticsearch connector (real) | 1 case(s) | `env-ST + env-elasticsearch` | — | `d064aa1` |
| `ST1.13` | ST | UC-014 | `FR-017` | `mcp` | Cassandra connector (real) | 1 case(s) | `env-ST + env-cassandra` | — | `d064aa1` |
| `ST1.14` | ST | UC-015 | `FR-018` | `mcp` | PostgreSQL connector (real) | 1 case(s) | `env-ST + env-postgresql` | — | `d064aa1` |
| `ST1.15` | ST | UC-015 | `FR-018` | `mcp` | MariaDB connector (real) | 1 case(s) | `env-ST + env-mariadb` | — | `d064aa1` |
| `ST1.1` | ST | UC-022 | `FR-025` | `mcp` | four-surface server startup + health | 1 case(s) | `env-ST` | ST1.1 health flake (env-dependent) | `d064aa1` |
| `ST1.2` | ST | UC-024,UC-025 | `FR-003`, `FR-028` | `mcp` | access-control API + audit-log assertion | 1 case(s) | `env-ST` | — | `d064aa1` |
| `ST1.3` | ST | UC-010 | `FR-013` | `mcp` | MongoDB connector (real) | 1 case(s) | `env-ST + env-mongodb` | — | `d064aa1` |
| `ST1.4` | ST | UC-002 | `FR-005` | `mcp` | catalog API (real) | 1 case(s) | `env-ST` | — | `d064aa1` |
| `ST1.5` | ST | UC-003,UC-004 | `FR-006` | `mcp` | content API (real) | 3 case(s) | `env-ST` | — | `d064aa1` |
| `ST1.6` | ST | UC-006 | `FR-009` | `mcp` | schema API (real) | 1 case(s) | `env-ST` | — | `d064aa1` |
| `ST1.7` | ST | UC-007 | `FR-010` | `mcp` | search API (real) | 1 case(s) | `env-ST` | — | `d064aa1` |
| `ST1.8` | ST | UC-019 | `FR-022` | `webui` | WebUI system serving | 1 case(s) | `env-ST-WEBUI` | — | `d064aa1` |
| `ST1.9` | ST | UC-011 | `FR-014` | `mcp` | CouchDB connector (real) | 1 case(s) | `env-ST + env-couchdb` | — | `d064aa1` |
| `UT1.10` | UT | UC-007 | `FR-010` | `mcp` | search service | 2 case(s) | `env-UT` | — | `d064aa1` |
| `UT1.11` | UT | UC-019 | `FR-022` | `webui` | WebUI serving unit | 5 case(s) | `env-UT` | — | `d064aa1` |
| `UT1.12` | UT | UC-006 | `FR-009` | `mcp` | schema-change service | 2 case(s) | `env-UT` | — | `d064aa1` |
| `UT1.13` | UT | UC-011 | `FR-014` | `mcp` | CouchDB connector unit | 2 case(s) | `env-UT` | — | `d064aa1` |
| `UT1.14` | UT | UC-012 | `FR-015` | `mcp` | OpenSearch connector unit | 2 case(s) | `env-UT` | — | `d064aa1` |
| `UT1.15_A2AServer` | UT | UC-018 | `FR-021` | `mcp` | A2A server unit | 6 case(s) | `env-UT` | — | `d064aa1` |
| `UT1.15_MongoConfig` | UT | UC-010 | `FR-013` | `mcp` | MongoDB config resolution | 4 case(s) | `env-UT` | — | `d064aa1` |
| `UT1.16` | UT | UC-013 | `FR-016` | `mcp` | Elasticsearch connector unit | 2 case(s) | `env-UT` | — | `d064aa1` |
| `UT1.17` | UT | UC-014 | `FR-017` | `mcp` | Cassandra connector unit | 2 case(s) | `env-UT` | — | `d064aa1` |
| `UT1.18` | UT | UC-015 | `FR-018` | `mcp` | relational connector dispatch | 2 case(s) | `env-UT` | — | `d064aa1` |
| `UT1.19` | UT | UC-021 | `FR-024` | `mcp` | async job lifecycle | 4 case(s) | `env-UT` | — | `d064aa1` |
| `UT1.1` | UT | UC-020 | `FR-023` | `mcp` | config loading + masked provenance | 2 case(s) | `env-UT` | — | `d064aa1` |
| `UT1.20_DiscoveryApi` | UT | UC-002 | `FR-005` | `mcp` | discovery API unit | 1 case(s) | `env-UT` | — | `d064aa1` |
| `UT1.20_McpServer` | UT | UC-017 | `FR-020` | `mcp` | MCP server + tool registry | 1 case(s) | `env-UT` | — | `d064aa1` |
| `UT1.21` | UT | UC-001,UC-006 | `FR-004` | `mcp` | profile scope + schema approval | 3 case(s) | `env-UT` | — | `d064aa1` |
| `UT1.22` | UT | UC-009,UC-029,UC-030,UC-031 | `CS-002`, `CS-003`, `CS-004`, `CS-009`, `CS-010`, `CS-011`, `CS-013`, `CS-014`, `CS-015` | `mcp` | test-data seed RBAC negatives | 4 case(s) | `env-UT` | — | `d064aa1` |
| `UT1.2` | UT | UC-023 | `FR-002` | `mcp` | auth middleware / cookie<->api-key bridge | 6 case(s) | `env-UT` | — | `d064aa1` |
| `UT1.3` | UT | UC-024,UC-025 | `FR-003` | `mcp` | access-control service + RBAC + audit emission | 5 case(s) | `env-UT` | — | `d064aa1` |
| `UT1.4` | UT | UC-010 | `FR-013` | `mcp` | MongoDB connector unit | 5 case(s) | `env-UT` | — | `d064aa1` |
| `UT1.50` | UT | UC-028 | `FR-001` | `mcp` | unauth auth gate | 4 case(s) | `env-UT` | — | `d064aa1` |
| `UT1.51` | UT | UC-023 | `FR-001` | `mcp` | authed non-admin gate | 9 case(s) | `env-UT` | — | `d064aa1` |
| `UT1.52` | UT | UC-023,UC-028,UC-029 | `CS-001`, `CS-005`, `CS-006`, `CS-007`, `CS-008`, `CS-012`, `CS-016`, `FR-001` | `mcp` | flat-login contract + negatives | 9 case(s) | `env-UT` | — | `d064aa1` |
| `UT1.5` | UT | UC-003 | `FR-007` | `mcp` | structured filter model parse/translate/reject | 3 case(s) | `env-UT` | — | `d064aa1` |
| `UT1.6` | UT | UC-002 | `FR-005` | `mcp` | catalog tools | 1 case(s) | `env-UT` | — | `d064aa1` |
| `UT1.7` | UT | UC-004 | `FR-006` | `mcp` | content tools CRUD | 1 case(s) | `env-UT` | — | `d064aa1` |
| `UT1.8` | UT | UC-005 | `FR-008` | `mcp` | relationship tools | 1 case(s) | `env-UT` | — | `d064aa1` |
| `UT1.9` | UT | UC-007 | `FR-010` | `mcp` | search indexer | 2 case(s) | `env-UT` | — | `d064aa1` |

### 2.1 TEST-DESIGN-TODO — Stream-B / Stream-C drive-out targets

These are design targets authored from the db-mcp WebUI Feedback Capture observations
(`GarysWorkingNotes.md` db-mcp section) and the W28A-871 coverage gaps. They are NOT yet
bound to a passing test (no fabricated binding); `W28E-1808B` (backend) and `W28E-1808C`
(WebUI/E2E) must implement + bind them. Each cites the requirement anchor and observation.

| TODO ID | Requirement anchor | Observation(s) | Drive-out target | Stream |
|---|---|---|---|---|
| `TD-001` | `FR-028`, AC-02, PS-40 | `DM-AL-09`, `DM-D-12`, `DM-X-19` | NIST AU-3 fully-populated audit events (actor/client_ip/session_id/correlation_id/target/outcome) emitted on every API/MCP/A2A/WebUI call; assert populated fields | B |
| `TD-002` | `FR-003`, A4 | `DM-RB-08`, `DM-RB-01`, `DM-RB-02` | Per-role RBAC matrix + resource-RBAC binding CRUD test through shared idam | B / C |
| `TD-003` | `FR-003` | `DM-RB-09`, `DM-U-04`, `DM-U-05`, `DM-U-06` | Users-as-username (GUID->username join), user-uniqueness, server-loaded roles/groups multiselect | B / C |
| `TD-004` | `FR-022`, D2 | `DM-DB-05`..`DM-DB-08`, `DM-D-07`, `DM-D-08` | PS-77 DataTable behaviour (pagination, dynamic columns, loading/empty/error states), de-duplicated filter preview | C |
| `TD-005` | `FR-020`, `FR-021`, `DM-AD-06`..`DM-AD-09` | `DM-AD-06`, `DM-AD-07`, `DM-AD-08`, `DM-MC-06`, `DM-MC-07`, `DM-AC-04`, `DM-AC-05` | API-docs/MCP-console/A2A-console Playwright coverage: parameter + output-schema columns, agent-card formatting, download/copy | C |
| `TD-006` | `FR-024`, XC-010 | `DM-J-11`, `DM-J-01`, `DM-J-02`, `DM-J-08` | Resolve `/jobs` page keep/remove decision; if kept, assert async surface (`data.create`/`data.update`/`index.rebuild`) | C (decision) |
| `TD-007` | `FR-022` (cross-cutting) | `DM-X-15`..`DM-X-18` | Shared `<HelpTip>` / `<StructuredMultiSelect>` primitives, column-picker overlay, status-column-left invariant — routed to W28E-1825 PS-WEBUI-STYLE-COMPONENTS | C / cross-cutting |
| `TD-008` | `FR-019`, G1, G3 | W28A-871 G1/G3 WebUI gap | Seven-connector matrix exercised through the WebUI (Playwright) | C |



<!-- W28C-1710b design-delta additions (2026-06-14T18:01:23Z) -->

## W28C-1710b design-delta — planned tests catalogue (T-TST v1.1 10-col schema)

Per T-TST v1.1, the planned tests catalogue carries 10 columns: `test-id | tier | use-case | requirement | surface | scenario | variants | env-files | known-issue | last-run-commit`. Test binding (replacement of probe markers with `@pytest.mark.req("FR-NNN")`) is W28C-1711 work.

Consolidation rules (per W28C-1711):

1. One primary test per FR-NNN; variants via `pytest.parametrize`.
2. Common scenarios (login, RBAC matrix, anon-denied) in `tests/helpers/`.
3. Cross-surface FR uses parametrized test file; not duplicate files.
4. Every `surface: webui` FR has a Playwright test (cookie-login + RBAC matrix + screenshot + DOM-assert + console-error-gate + CW-pattern).
5. Every `surface: api|mcp|a2a` FR has a protocol-level test.
6. Every `CS-NNN` binds to `@pytest.mark.negative` test with expected denial code.
7. CRUD-applicable entities have C/R/U/D coverage.
8. Orphan retirement requires knowledge-extract worksheet.
