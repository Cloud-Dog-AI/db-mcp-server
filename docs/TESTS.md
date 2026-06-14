---
template-id: T-TST
template-version: 1.1
applies-to: docs/TESTS.md
project: db-mcp-server
doc-last-updated: 2026-06-12T16:36:39Z
doc-git-commit: de6c3ed78039fcf91204a0f860096008551f7018
doc-git-branch: main
doc-age-policy: 90d
doc-conformance-stamp: 2026-06-12T16:36:39Z
req-trace-version: 1.0
total-tests: 0
coverage-percent: 0
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

Mandatory 10-column schema per PS-REQ-TEST-TRACE v1.0 §4.2. The per-test catalogue below will be populated by operator-driven Instruction 4 work that binds @pytest.mark.req() decorators to specific REQ-IDs. Until then, all tests carry @pytest.mark.probe (KEEP-AS-PROBE disposition per PS-REQ-TEST-TRACE §7).

| Test ID | Tier | Use case | Requirement | Surface | Scenario | Variants | Env files | Known issue | Last run commit |
|---|---|---|---|---|---|---|---|---|---|


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
