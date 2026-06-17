---
template-id: T-REQ
template-version: 1.1
applies-to: docs/REQUIREMENTS.md
project: db-mcp-server
doc-last-updated: 2026-06-17T00:00:00Z
doc-git-commit: d064aa17d3a6570cb01e86bbf63e4632b37fb355
doc-git-branch: main
doc-age-policy: indefinite
doc-conformance-stamp: 2026-06-17T00:00:00Z
req-trace-version: 1.0
req-id-prefixes-used: [FR, CS, NF, CR, CD, SC, CO, SI, RL, CN, AC, CFG]
surface-coverage: [api, mcp, a2a, webui]
stream-a-lane: W28E-1808A
---

# db-mcp-server — REQUIREMENTS
## W28A-421 Review Status
- Reviewed for external/shareable publication during W28A-421.
- Source basis: `defaults.yaml`, current server and connector source, current db-mcp WebUI routes, and current MCP tool registry definitions.
- W28A-871 Phase 1 refresh: source-verified 7 connector adapters, 18 routed WebUI pages, 45 `ToolContract` MCP tools plus the legacy MCP alias path enabled by `include_legacy_tools_alias=True`.
- Internal-only absolute paths, environment-specific hosts, and private registries have been removed from this shareable document set.

**Version:** 0.2 • 2026-04-09
**Status:** Planning + W28A-871 Phase 1 merge

## Executive Summary
`db-mcp-server` is a Cloud-Dog AI MCP and admin service for multi-connector discovery, schema inspection, structured content operations, relationship management, and discovery indexing. The current Phase 1 specification covers seven connectors: MongoDB, PostgreSQL, MariaDB, CouchDB, OpenSearch, Elasticsearch, and Cassandra. The service uses a profile-based connection model with RBAC, structured filters instead of free-text query generation, auditable schema-change workflows, and indexed discovery/search.

## Platform Alignment
- Configuration: `cloud_dog_config`
- Logging and audit: `cloud_dog_logging`
- API/Web runtime: `cloud_dog_api_kit`
- Identity, users, groups, API keys, RBAC: `cloud_dog_idam`
- Jobs and workers: `cloud_dog_jobs`
- Metadata/audit persistence: `cloud_dog_db`
- Static asset and local path access: `cloud_dog_storage`
- Design principle: structured filters replace LLM-generated database queries for executable operations

## CR — Core Requirements
### CR-01 (P1)
The system shall use the standard four-server Cloud-Dog pattern with API (`8086`), Web (`8087`), MCP (`8088`), and A2A (`8089`) surfaces.
Acceptance criteria:
- All four server roles are documented and reserved
- Each surface has a planned health endpoint and auth model

### CR-02 (P1)
The system shall expose public health/readiness endpoints and authenticated operational status endpoints.
Acceptance criteria:
- `GET /health` is defined for each runtime surface
- authenticated status endpoints are documented for queue, connector, and profile state

### CR-03 (P1)
The system shall use `cloud_dog_config`, `cloud_dog_logging`, `cloud_dog_api_kit`, `cloud_dog_idam`, `cloud_dog_jobs`, `cloud_dog_db`, and `cloud_dog_storage`.
Acceptance criteria:
- platform package usage is documented in README and architecture
- no bespoke alternatives are planned for those concerns

## CD — Catalogue & Discovery
### CD-01 (P1)
The system shall list connection profiles and their enabled source types.
Acceptance criteria:
- MCP/API/Web/A2A list flows are defined
- RBAC scope is documented per profile

### CD-02 (P1)
The system shall browse namespaces, databases, collections, indices, and analogous source objects for each connector.
Acceptance criteria:
- namespace browsing is documented for all Phase 1 sources
- results include source metadata and access context

### CD-03 (P1)
The system shall support metadata search across profiles, namespaces, entities, fields, and relationships.
Acceptance criteria:
- keyword and filtered metadata discovery flows are defined
- search is profile-scoped and auditable

### CD-04 (P2)
The system shall cache and index discovery metadata for fast cross-source lookup.
Acceptance criteria:
- indexing pipeline stages are defined
- refresh and invalidation are job-backed

## SC — Schema Requirements
### SC-01 (P1)
The system shall inspect entity schemas, fields, types, constraints, and indices for each source.
Acceptance criteria:
- schema introspection tool families are defined
- output model includes source-specific and normalised views

### SC-02 (P1)
The system shall create schema change plans before any source mutation.
Acceptance criteria:
- validate -> plan -> approve -> execute workflow is documented
- dry-run output includes impact summary and rollback notes

### SC-03 (P2)
The system shall apply approved schema changes through auditable jobs.
Acceptance criteria:
- job execution and audit trail requirements are defined
- role requirements for approval and execution are documented

### SC-04 (P2)
The system shall refresh discovery metadata after schema changes.
Acceptance criteria:
- post-change refresh is part of the planned workflow
- stale schema detection is documented

## CO — Content Operations
### CO-01 (P1)
The system shall support structured read operations using an explicit filter model.
Acceptance criteria:
- filter grammar is documented
- sort, paging, projection, and field masking are included

### CO-02 (P1)
The system shall support structured create, update, and delete operations subject to profile policy and RBAC.
Acceptance criteria:
- write operations are profile-scoped and auditable
- mutation requests use declarative payloads rather than free-text instructions

### CO-03 (P2)
The system shall support bulk operations with dry-run previews and job execution.
Acceptance criteria:
- bulk read/write planning is documented
- safety controls and approval gates are defined

### CO-04 (P2)
The system shall support content masking and field suppression based on role, group, and profile policy.
Acceptance criteria:
- masking policy model is documented
- read and write paths both honour field-level restrictions

### CO-05 (P1)
The system shall support a documented structured-filter operator grammar for content reads, counts, existence checks, updates, and deletes.
Acceptance criteria:
- CO-01 filter grammar explicitly enumerates `eq`, `neq`, `gt`, `gte`, `lt`, `lte`, `in`, `not_in`, `contains`, `starts_with`, `ends_with`, `exists`, `not_exists`, `regex`, `is_null`, and `is_not_null`
- logical grouping explicitly supports `and`, `or`, and `not`
- MongoDB, CouchDB, OpenSearch, and Elasticsearch document support for the full 16-operator grammar; Cassandra documents support for `eq` within `and` groups only

### CO-06 (P1)
The system shall support binary/blob content fields for MongoDB using JSON-safe binary envelopes on write and hex serialisation on read.
Acceptance criteria:
- create and update requests accept `{"__type__":"binary","encoding":"hex"|"base64","data":"..."}` for binary field values
- read responses serialise binary field values as hex strings and schema introspection reports the field type as `binary`
- MongoDB shall support at least 50 KiB insert/read verification and 500 KiB update/read verification in ST coverage; other Phase 1 connectors do not advertise binary-field serialisation support in this release

## SI — Search & Indexing
### SI-01 (P1)
The system shall index source metadata and selected content for discovery search.
Acceptance criteria:
- indexing pipeline is documented
- profile-level include/exclude rules are defined

### SI-02 (P1)
The system shall support keyword, phrase, filtered, and proximity-style search where source capabilities allow.
Acceptance criteria:
- capability variance across connectors is documented
- fallback behaviour is explicit and non-deceptive

### SI-03 (P2)
The system shall rank search results using deterministic scoring and optional LLM-generated explanations.
Acceptance criteria:
- LLM use is limited to explanation/summarisation, not executable query generation
- ranking inputs are auditable

### SI-04 (P2)
The system shall run indexing and refresh work as jobs via `cloud_dog_jobs`.
Acceptance criteria:
- queue/job lifecycle is documented
- health and retry expectations are defined

## RL — Relationship Management
### RL-01 (P1)
The system shall list declared, curated, and inferred relationships between entities.
Acceptance criteria:
- relationship types and provenance are documented
- relationship browsing is profile-scoped

### RL-02 (P2)
The system shall create and update curated relationship definitions.
Acceptance criteria:
- create/update/delete flows are documented
- approval and audit requirements are defined

### RL-03 (P2)
The system shall infer candidate relationships from metadata and indexed content.
Acceptance criteria:
- inference inputs and confidence metadata are documented
- review workflow is required before curated promotion

## CN — Connector Requirements
### CN-01 (P1)
MongoDB connector shall support profile validation, namespace discovery, schema sampling, structured filters, and index metadata.
Acceptance criteria:
- MongoDB adapter responsibilities are documented
- CRUD/search/schema tool families are mapped

### CN-02 (P1)
CouchDB connector shall support database discovery, document metadata browsing, view/index awareness, and structured operations.
Acceptance criteria:
- CouchDB-specific capability notes are documented
- write safety rules are defined

### CN-03 (P1)
OpenSearch connector shall support index discovery, mappings, structured search, and schema-change planning.
Acceptance criteria:
- OpenSearch capability coverage is documented
- search and index settings workflows are identified

### CN-04 (P1)
Elasticsearch connector shall support index discovery, mappings, structured search, and schema-change planning.
Acceptance criteria:
- Elasticsearch adapter scope is documented separately from OpenSearch where capability differs
- audit expectations are defined

### CN-05 (P1)
Cassandra connector shall support keyspace/table discovery, schema inspection, structured reads, and safe change planning.
Acceptance criteria:
- Cassandra-specific partition/key considerations are documented
- mutation safeguards are defined

## AC — Access Control
### AC-01 (P1)
The system shall use profile-based connection definitions with RBAC at profile, namespace, entity, and field scope.
Acceptance criteria:
- profile model and permission boundaries are documented
- users, groups, and API keys are managed via `cloud_dog_idam`

### AC-02 (P1)
The system shall enforce audit logging for all profile access, discovery, content, schema, and relationship operations.
Acceptance criteria:
- audit events are defined for read and write operations
- actor, profile, source, and outcome metadata are included

### AC-03 (P2)
The system shall support field masking and sensitive-field suppression by role and policy.
Acceptance criteria:
- masking rules are documented
- policy enforcement point is the service layer

### AC-04 (P1)
The system shall provide the five built-in RBAC roles `admin`, `data_steward`, `developer`, `analyst`, and `auditor` with documented default permission sets.
Acceptance criteria:
- `admin` grants `*`
- `data_steward` grants `catalog.read`, `schema.read`, `schema.change`, `relationship.read`, `relationship.change`, `content.search`, `data.read`, `data.create`, `data.update`, `data.delete`, `index.manage`, `profile.manage`, and `audit.read`
- `developer` grants `catalog.read`, `schema.read`, `schema.change`, `relationship.read`, `content.search`, `data.read`, `data.create`, `data.update`, and `index.manage`
- `analyst` grants `catalog.read`, `schema.read`, `relationship.read`, `content.search`, and `data.read`
- `auditor` grants `catalog.read`, `schema.read`, `relationship.read`, `audit.read`, and `data.read`

### AC-05 (P1)
The system shall support admin-only CRUD management for users and user lifecycle state through `cloud_dog_idam`.
Acceptance criteria:
- admin-authenticated API, Web, MCP, and A2A flows support create, read, update, disable, enable, and delete operations for users
- user records include role assignments and audit metadata

### AC-06 (P1)
The system shall support admin-only CRUD management for groups, group membership, and profile-scoped API keys through `cloud_dog_idam`.
Acceptance criteria:
- admin-authenticated flows support create, read, update, and delete operations for groups plus add/remove user membership changes
- API keys can be created, listed, and revoked with explicit scopes and assigned profile IDs
- group and API-key operations emit audit events and enforce admin role checks

## CFG — Configuration
### CFG-01 (P1)
The system shall manage profiles via API, MCP, A2A, Web UI, and config storage.
Acceptance criteria:
- create/read/update/delete profile flows are documented
- config precedence and Vault integration are documented

### CFG-02 (P1)
The system shall provide connector templates for MongoDB, CouchDB, OpenSearch, Elasticsearch, and Cassandra.
Acceptance criteria:
- template fields are documented in defaults and env reference
- validation expectations are defined

### CFG-03 (P2)
The system shall support staging and production deployment overlays with secret-store-backed credentials.
Acceptance criteria:
- staging documentation skeleton exists
- operator/test overlay expectations are documented

## NF — Non-Functional Requirements
### NF-01 (P1)
The system shall remain deterministic and auditable for executable operations by using structured filters and explicit plans.
Acceptance criteria:
- executable operations do not depend on free-text query generation
- plan/apply/audit chain is documented

### NF-02 (P1)
The system shall support job-backed retries, timeout controls, and connector health tracking.
Acceptance criteria:
- timeout and retry concerns are documented for each execution plane
- health monitoring points are identified

### NF-03 (P2)
The system shall scale across multiple profiles and large discovery/indexing workloads.
Acceptance criteria:
- queue-based scaling model is documented
- background worker role is defined in architecture

### NF-04 (P2)
The system shall be maintainable through connector isolation, platform package reuse, and explicit backlog decomposition.
Acceptance criteria:
- connector-per-source isolation is documented
- implementation backlog is split into sequenced follow-up tasks

## W28A-871 Spec Merge — Source-Verified Requirement Matrix

This section merges the W28A-871 sections `a` through `g` into the published requirements set. Each merged requirement is marked `EXISTING` when it is already materially covered by the earlier requirements above, or `NEW` when W28A-871 adds a concrete requirement that was not previously stated with sufficient specificity.

| ID | Section | Status | Requirement | Existing anchors |
|----|---------|--------|-------------|------------------|
| A1 | Profile Configuration | EXISTING | The system shall provide CRUD management for connection profiles across API, MCP, A2A, and Web UI surfaces. | CFG-01, AC-01, AC-05, AC-06 |
| A2 | Profile Configuration | NEW | The system shall publish connector profile templates and validation guidance for all seven Phase 1 connectors: MongoDB, PostgreSQL, MariaDB, CouchDB, OpenSearch, Elasticsearch, and Cassandra. | CFG-02, CN-01..CN-05 |
| A3 | Profile Configuration | EXISTING | Profiles shall remain scope boundaries for namespaces, entities, API keys, and allowed permissions, with role-aware access checks and audit events. | AC-01, AC-02, AC-04, AC-06 |
| A4 | Profile Configuration | NEW | Per-tool RBAC coverage shall be documented and kept aligned with the built-in five-role permission model, including explicit review of any tool/role naming mismatches. | AC-04 |
| B1 | Catalogue | EXISTING | The system shall browse namespaces and entities per profile and per connector using auditable discovery flows. | CD-01, CD-02 |
| B2 | Catalogue | NEW | Catalogue views shall expose profile-scoped navigation from namespace browsing to entity detail and data browser flows without losing profile context. | CD-02, SC-01 |
| C1 | Entity Detail | EXISTING | Entity detail shall expose schema, fields, indexes, relationship metadata, and sample-shape introspection for the selected entity. | SC-01, RL-01 |
| C2 | Entity Detail | NEW | Entity detail shall distinguish source-specific metadata from normalised summaries and show relationship provenance and sample data evidence where available. | SC-01, RL-01 |
| D1 | Data Browser | EXISTING | The service shall support structured filter-builder driven reads, counts, existence checks, projection, sorting, and paging. | CO-01, CO-05 |
| D2 | Data Browser | NEW | The Web UI data browser shall present queryable results with pagination, dynamic columns, and explicit empty/error/loading states rather than raw JSON-only result cards. | CO-01, CO-05 |
| D3 | Data Browser | EXISTING | Data browser access shall be profile-scoped, RBAC-enforced, and auditable for read and mutation flows. | CO-02, CO-04, AC-01, AC-02 |
| E1 | Search | EXISTING | The system shall support profile-scoped metadata discovery across profiles, namespaces, entities, fields, and relationships. | CD-03, SI-01, SI-02 |
| E2 | Search | EXISTING | The system shall support content search plus explain-style search result interpretation where connector capabilities allow. | SI-02, SI-03 |
| E3 | Search | NEW | Search and indexing requirements shall explicitly cover deterministic explain/debug output, refresh expectations, and audit visibility for discovery-index maintenance. | SI-01, SI-04, AC-02 |
| F1 | Relationships | EXISTING | The system shall list declared, curated, and inferred relationships with provenance and profile scoping. | RL-01 |
| F2 | Relationships | EXISTING | The system shall support curated relationship create/update/delete flows and candidate inference with review before promotion. | RL-02, RL-03 |
| G1 | Multi-Connector Verification | NEW | The published requirements shall include a seven-connector verification matrix covering MongoDB, PostgreSQL, MariaDB, CouchDB, OpenSearch, Elasticsearch, and Cassandra. | CN-01..CN-05 |
| G2 | Multi-Connector Verification | NEW | The published requirements shall identify the staging/runtime overlay inputs required to exercise each connector safely in ST/IT/AT tiers. | CFG-03, NF-02 |
| G3 | Multi-Connector Verification | NEW | Each connector shall have a minimum lifecycle verification path: create profile, discover namespaces/entities, run a representative query, and verify the result through the service interfaces. | CD-01, CD-02, CO-01, SI-02 |

## W28A-871 Source-Verified Notes

- Source tree currently contains connector adapters for `mongodb`, `postgresql`, `mariadb`, `couchdb`, `opensearch`, `elasticsearch`, and `cassandra`.
- The current MCP source defines 45 `ToolContract` tools. `docs/MCP_DOCUMENTATION.md` still states 46 tools because the runtime also enables a legacy alias path; there is no source evidence in this repo for the 56-tool count cited in the W28A-871 context paragraph.
- The current db-mcp WebUI exposes 18 routed pages excluding redirects: dashboard, profiles, users, groups, API keys, RBAC, catalogue, entity detail, data browser, search, relationships, schema planner, audit, jobs, MCP console, A2A console, API docs, and settings.


## W28A-883 PS-78 Cross-Platform File Handling Addendum

### Verified current state

- Current source evidence shows binary-envelope handling in MCP content tools, but no standard service file lifecycle API.
- `cloud_dog_storage` is currently used for SPA/static file serving and common local path helpers, not for end-user file lifecycle features.
- No dedicated WebUI file upload/download/browser surface was found.

### Required additions to satisfy PS-78

- Add a `cloud_dog_storage`-backed file lifecycle module with `/files/upload`, `/files/upload_base64`, `/files`, `/files/{id}`, `DELETE /files/{id}`, and `/files/{id}/download`.
- Add MCP `file_upload` and `file_download` tools using base64 payloads instead of relying only on generic binary envelopes.
- Add A2A file transfer conventions for connector-bound data artifacts.
- Add WebUI file upload/download/browser surfaces for connector exports and operator-provided files.
- Add chat/delegated file handling requirements for downstream consumers.

### Required PS-78 test plan

- API: upload, list, metadata, download, delete.
- MCP: base64 upload/download and URI-source import.
- A2A: transfer file-bearing database artifacts between agents.
- WebUI: upload control, browser/inventory, download, delete.
- Connector flow: verify a connector-generated artifact can be stored, listed, downloaded, and deleted through the standard file lifecycle.

## PS-40 / W28A-619 Logging and Audit Requirements

The service MUST use `cloud_dog_logging` as the only application and audit logging implementation. Raw stdlib logging setup, direct `logging.getLogger()` calls, bespoke audit emitters, and print-based operational logging are not compliant except inside the platform logging package itself.

Every auditable event MUST emit a PS-40/NIST AU-3 audit record with: `event_type`, `action`, `timestamp`, `service`, `component`, `service_instance`, `environment`, `source_host`, `source_process`, `source_application`, `source_address` where available, `destination_address` where available, `outcome`, actor identity including user/service/system plus account/process/device identifiers where available, `target`, `process_id`, `affected_files` where relevant, `correlation_id`, `trace_id`, and `request_id`.

Auditable events MUST include authentication and authorisation decisions, user/group/API-key/RBAC changes, profile/connection/entity/data-browser operations, MCP/A2A/API calls, job lifecycle changes, configuration changes, data access and mutation, denials, failures, and privileged operations. Secrets MUST be redacted before persistence. Tests MUST cover schema fields, event coverage, redaction, append-only audit persistence, retention/integrity, and WebUI observability rendering/filtering.

## 5. Cyber Security & Negative Flows

Mandatory schema per PS-REQ-TEST-TRACE v1.0 §3.4. Every project covers anon-denied, wrong-role-denied, missing-param-error per declared surface. The CS rows below are platform-baseline; project-specific extensions append in §5.1.

| ID | Threat / negative scenario | Surface | Role(s) attempted | Expected | Tests |
|---|---|---|---|---|---|
| `CS-001` | Anon attempts data read | `api`, `mcp`, `a2a`, `webui` | `anon` | `401` | `UT1.52_FlatLoginContract` |
| `CS-002` | read-only attempts write | `api`, `mcp` | `read-only` | `403` | `UT1.22_TestDataSeed` |
| `CS-003` | Missing required param | `api` | `admin` | `422` | `UT1.22_TestDataSeed` |
| `CS-004` | Wrong-role privileged op | `mcp` | `read-write` | `403` | `UT1.22_TestDataSeed` |


<!-- W28C-1710b design-delta additions (2026-06-14T18:01:23Z); SHA chain in working/W28C-1710b/KNOWLEDGE-PRESERVATION-DELTA.md -->

## PS-REQ-TEST-TRACE schema completion (W28C-1710b)

Per the binding contract (`docs/standards/PS-REQ-TEST-TRACE.md` §2 + §3), every FR-NNN row in this file declares the following schema (default values; operator amends per row in W28C-1711):

```yaml
surface: ['api', 'mcp', 'a2a', 'webui']  # programme default for db-mcp-server
priority: must  # default; operator amends per FR
since: 2026-06-14  # carried forward unless older anchor known
last-verified: 2026-06-14
tests: []  # populated by W28C-1711 binding
crud: N/A  # default; operator amends per FR
```

## Baseline CS-NNN rows (PS-REQ-TEST-TRACE §3.4 — added by W28C-1710b)

Every project MUST have CS-NNN rows for `anon-denied`, `wrong-role-denied`, `missing-param-error` per surface. Programme baseline:

| CS-NNN | Scenario | Surface | Expected | Roles |
|---|---|---|---|---|
| `CS-005` | anon-denied | `api` | `401` | `anon` |
| `CS-006` | anon-denied | `mcp` | `401` | `anon` |
| `CS-007` | anon-denied | `a2a` | `401` | `anon` |
| `CS-008` | anon-denied | `webui` | `401` | `anon` |
| `CS-009` | wrong-role-denied | `api` | `403` | `read-only` |
| `CS-010` | wrong-role-denied | `mcp` | `403` | `read-only` |
| `CS-011` | wrong-role-denied | `a2a` | `403` | `read-only` |
| `CS-012` | wrong-role-denied | `webui` | `403` | `read-only` |
| `CS-013` | missing-param-error | `api` | `422` | `*` |
| `CS-014` | missing-param-error | `mcp` | `422` | `*` |
| `CS-015` | missing-param-error | `a2a` | `422` | `*` |
| `CS-016` | missing-param-error | `webui` | `422` | `*` |

_W28E-1808A: every CS-NNN row above is bound to a `@pytest.mark.req("CS-NNN")` negative test. `CS-001`/`CS-005`-`CS-008` (anon-denied) and `CS-012`/`CS-016` bind to `tests/unit/UT1.52_FlatLoginContract`; `CS-002`-`CS-004` and `CS-009`-`CS-011`/`CS-013`-`CS-015` (wrong-role-denied + missing-param) bind to `tests/unit/UT1.22_TestDataSeed`. See `docs/REQ-COVERAGE.md` for the generated binding matrix._


<!--
W28E-1808A Stream-A canonical-FR re-author (2026-06-17).
This section SUPERSEDES the W28C-1711-R3 mechanical tier-bucket FR rows
(FR-001=R2, FR-003=unit-cluster, FR-006=system-cluster, FR-009=integration-cluster, ...),
which were derived from pytest *tier* clusters rather than service capabilities and are
the PS-CLOSEOUT-WARRANTY §6 "probe-cluster ADD-REQ stub" pattern. Each FR-NNN below is a
real db-mcp capability sourced from `src/` + the detailed CR/CD/SC/CO/SI/RL/CN/AC/CFG
requirements above, and is bound to specific capability tests (semantic
`@pytest.mark.req("FR-NNN")`, replacing all mechanical bindings + residual probes).
The FR-NNN -> old-binding migration is recorded in
working/evidence/W28E-1808A/current/03-requirements-map.tsv.
-->

## Functional Requirements (W28E-1808A canonical capability map)

Per PS-REQ-TEST-TRACE §2 every test `@pytest.mark.req()` references a backtick-wrapped
FR/CS/NF-NNN row here, and every FR-NNN binds to >=1 capability test. `since` is the git
short-sha that introduced the capability on `main` (`2d11a0c` = W28A-871-R2 forward-port;
`d064aa1` = W28C-1711-R3 baseline). Detailed acceptance criteria live in the
CR/CD/SC/CO/SI/RL/CN/AC/CFG/NF sections above (the `domain anchor` column).

| ID | Capability | Surfaces | Priority | Since | Domain anchor + source_evidence | Semantic test binding |
|---|---|---|---|---|---|---|
| `FR-001` | Flat-login authentication contract: admin / read-write / read-only cookie login; authed-non-admin and anon gate (`401`) | `api`, `webui` | `must` | `2d11a0c` | AC-01, AC-05; `src/core/access_control/service.py` (flat demo roles), `src/servers/web/` | `UT1.50_UnauthAuthGate`, `UT1.51_AuthedNonAdminGate`, `UT1.52_FlatLoginContract` |
| `FR-002` | Auth middleware and cookie<->API-key secure proxy bridge | `api`, `a2a` | `must` | `d064aa1` | AC-01; `src/core/access_control`, `cloud_dog_api_kit` middleware | `UT1.2_AuthMiddleware` |
| `FR-003` | Access-control service and shared `cloud_dog_idam` RBAC (users / groups / API-keys / roles), profile-scoped permission rebuild | `api`, `mcp`, `webui` | `must` | `2d11a0c` | AC-04, AC-05, AC-06; `src/core/access_control/service.py`, `src/servers/api/access_control.py` | `UT1.3_AccessControlService`, `ST1.2_AccessControlApi`, `IT1.1_AccessControlLifecycle` |
| `FR-004` | Source-connection registry and connection-profile CRUD + profile scope enforcement | `api`, `mcp`, `webui` | `must` | `2d11a0c` | CFG-01, AC-01; `src/servers/api/source_connections.py`, `src/core/access_control` | `IT1.11_SourceConnections`, `UT1.21_ProfileScopeAndSchemaApproval` |
| `FR-005` | Catalogue and metadata discovery (namespaces / entities / fields), cached discovery API | `api`, `mcp` | `must` | `d064aa1` | CD-01, CD-02, CD-03, CD-04; `src/core/catalog`, `src/core/discovery`, `src/servers/api/discovery.py` | `UT1.6_CatalogTools`, `UT1.20_DiscoveryApi`, `ST1.4_CatalogApi`, `IT1.3_FullDiscoveryFlow` |
| `FR-006` | Structured content CRUD operations (declarative payloads, profile/RBAC scoped) | `api`, `mcp` | `must` | `d064aa1` | CO-01, CO-02, CO-06; `src/core/content`, `src/servers/mcp/content_tools.py` | `UT1.7_ContentTools`, `ST1.5_ContentApi`, `IT1.4_ContentCRUDLifecycle` |
| `FR-007` | Structured-filter operator grammar and filter model (16-operator grammar, and/or/not grouping) | `api`, `mcp` | `must` | `d064aa1` | CO-01, CO-05; `src/core/filters` | `UT1.5_FilterModel` |
| `FR-008` | Relationship management: list declared/curated/inferred, curate CRUD, candidate inference | `api`, `mcp` | `should` | `d064aa1` | RL-01, RL-02, RL-03; `src/core/relationships`, `src/servers/mcp/relationship_tools.py` | `UT1.8_RelationshipTools`, `IT1.5_RelationshipLifecycle` |
| `FR-009` | Schema introspection and validate->plan->approve->execute schema-change workflow | `api`, `mcp` | `must` | `d064aa1` | SC-01, SC-02, SC-03, SC-04; `src/core/schema`, `src/servers/api/schema_changes.py` | `UT1.12_SchemaChangeService`, `ST1.6_SchemaApi`, `IT1.7_SchemaChangeLifecycle` |
| `FR-010` | Search and discovery indexing (keyword/phrase/filtered search, deterministic scoring) | `api`, `mcp` | `must` | `d064aa1` | SI-01, SI-02, SI-03, SI-04; `src/core/search` | `UT1.9_SearchIndexer`, `UT1.10_SearchService`, `ST1.7_SearchApi`, `IT1.6_SearchIndexingLifecycle` |
| `FR-011` | Saved-query persistence and replay | `api`, `mcp` | `should` | `2d11a0c` | CO-01; `src/servers/api/saved_queries.py` | `IT1.12_SavedQueries` |
| `FR-012` | Gated test-data seeding (allowed-runtime-profile guard) | `api` | `should` | `2d11a0c` | CO-02; `src/core/test_data`, `src/servers/api/test_data.py` | `fixtures/test_seed_data` (positive), `UT1.22_TestDataSeed` (RBAC negatives, `CS-*`) |
| `FR-013` | MongoDB connector: validation, namespace discovery, schema sampling, structured filters, binary envelopes | `internal`, `mcp` | `must` | `d064aa1` | CN-01, CO-06; `src/core/connectors/mongodb` | `UT1.4_MongoDBConnector`, `UT1.15_MongoConfig`, `ST1.3_MongoDBConnector`, `IT1.2_MongoDbMcpTools` |
| `FR-014` | CouchDB connector: database discovery, document metadata, view/index awareness | `internal`, `mcp` | `must` | `d064aa1` | CN-02; `src/core/connectors/couchdb` | `UT1.13_CouchDBConnector`, `ST1.9_CouchDBConnector`, `IT1.8_CouchDbMcpTools` |
| `FR-015` | OpenSearch connector: index discovery, mappings, structured search, change planning | `internal`, `mcp` | `must` | `d064aa1` | CN-03; `src/core/connectors/opensearch` | `UT1.14_OpenSearchConnector`, `ST1.10_OpenSearchConnector`, `IT1.9_OpenSearchMcpTools` |
| `FR-016` | Elasticsearch connector: index discovery, mappings, structured search, change planning | `internal` | `must` | `d064aa1` | CN-04; `src/core/connectors/elasticsearch` | `UT1.16_ElasticsearchConnector`, `ST1.12_ElasticsearchConnector` |
| `FR-017` | Cassandra connector: keyspace/table discovery, schema inspection, safe reads/change planning | `internal` | `must` | `d064aa1` | CN-05; `src/core/connectors/cassandra` | `UT1.17_CassandraConnector`, `ST1.13_CassandraConnector` |
| `FR-018` | Relational connector dispatch (PostgreSQL + MariaDB adapters) | `internal` | `must` | `d064aa1` | CN-01..CN-05 (relational), CFG-02; `src/core/connectors` relational dispatch | `UT1.18_RelationalConnectorDispatch`, `ST1.14_PostgreSQLConnector`, `ST1.15_MariaDBConnector` |
| `FR-019` | Multi-backend connector matrix: uniform lifecycle across all seven connectors | `internal`, `mcp` | `must` | `d064aa1` | G1, G3, CN-01..CN-05; `src/core/connectors` | `IT1.10_BackendConnectorMatrix` |
| `FR-020` | MCP server and tool registry (catalog/content/relationship/schema/search/mongodb/audit tools + legacy alias) | `mcp` | `must` | `d064aa1` | CR-01; `src/servers/mcp` | `UT1.20_McpServer` |
| `FR-021` | A2A server and agent-card / skill surface with API-key auth | `a2a` | `must` | `d064aa1` | CR-01; `src/servers/a2a/app.py` | `UT1.15_A2AServer` |
| `FR-022` | WebUI serving: SPA shell and the canonical admin/developer/system page set | `webui` | `must` | `2d11a0c` | CR-01; `src/servers/web`, `ui/dist` | `UT1.11_WebUiServing`, `ST1.8_WebUiServing`, `AT_WEBUI_E2E` |
| `FR-023` | Configuration loading and masked effective-config provenance (`cloud_dog_config` + Vault precedence) | `internal`, `api` | `must` | `d064aa1` | CR-03, CFG-01, CFG-03; `src/common/runtime.py`, config-provenance | `UT1.1_ConfigLoading` |
| `FR-024` | Async job lifecycle (`cloud_dog_jobs`) for indexing, schema-change and bulk operations | `api`, `mcp` | `should` | `d064aa1` | SI-04, SC-03, CO-03, NF-02; `cloud_dog_jobs` wiring | `UT1.19_JobLifecycle` |
| `FR-025` | Four-surface server startup and `GET /health` readiness | `api` | `must` | `d064aa1` | CR-01, CR-02; `src/servers/*` health endpoints | `ST1.1_ServerStartup` |
| `FR-026` | Project-structure / packaging quality: required platform-package declarations and W28A-118C doc-package-test map | `internal` | `should` | `d064aa1` | CR-03, NF-04; `pyproject.toml`, package layout | `QT1.1_ProjectStructure` |
| `FR-027` | Live preprod deployment contract: b-method IDAM consumer (T0-T3) + live API/MCP/A2A/WebUI contract on `dbmcpserver0` | `api`, `a2a` | `must` | `2d11a0c` | CR-02, AC-01; `tests/e2e`, `tests/smoke` against deployed digest | `e2e/test_w28a746_live_preprod_contract`, `smoke/test_w28a746_b_method_idam` |
| `FR-028` | Audit logging: NIST AU-3 audit-event capture (`event_type`/`actor`/`outcome`) and MCP audit query tools (`list_events`/`get_event`) | `api`, `mcp` | `must` | `d064aa1` | AC-02, PS-40; `src/core/audit/service.py`, `src/servers/mcp/audit_tools.py` | `ST1.2_AccessControlApi` (asserts `audit.log.jsonl` event_types + `denied` outcome) |

> **Audit-emission gap (Stream-B target, do not mark closed here):** the live deployment
> currently fails to populate the full NIST AU-3 actor/client/correlation fields for every
> surface (WebUI observation `DM-AL-09`). `FR-028` is design-bound and asserted at the
> service-layer (`ST1.2`); end-to-end populated-field emission across API/MCP/A2A/WebUI is a
> Stream-B (`W28E-1808B`) implementation target. See the TEST-DESIGN-TODO rows in `docs/TESTS.md`.

## 6. WebUI Observation Traceability (DM-* -> requirement)

Every atomic db-mcp WebUI Feedback Capture observation from `GarysWorkingNotes.md`
(operator canonical checkout, db-mcp section ~L2577-2712) maps to an existing requirement
row below. Observations are predominantly Stream-C (WebUI/E2E) drive-out targets; this
table is the design-time binding so Stream-B/C have an explicit requirement anchor. No new
backtick FR-IDs are minted for un-tested observations — they become TEST-DESIGN-TODO /
AT-design rows in `docs/TESTS.md`. `[ui]` = present on the W28A-871 UI delta now on main.

| Observation group | Codes | Requirement anchor | Stream |
|---|---|---|---|
| Dashboard layout + activity table | `DM-D-07`, `DM-D-08`, `DM-D-12`, `DM-D-13` | `FR-022` (WebUI), `FR-028` (AU-3 fields) | C / B |
| Profiles dialog (rename, numeric field, help, USE semantics) | `DM-P-18`, `DM-P-22`, `DM-P-23`, `DM-P-24` | `FR-004` (profiles), `FR-022` | C |
| Catalogue master/detail layout | `DM-CAT-02` | `FR-005` | C |
| Data Browser (filter preview, button styling, role widget, dedup) | `DM-DB-05`, `DM-DB-06`, `DM-DB-07`, `DM-DB-08` | `FR-006`, `FR-007` | C |
| Search page title | `DM-SR-07` | `FR-010` | C |
| Relationships action labels | `DM-RE-04` | `FR-008` | C |
| Schema page/nav labels | `DM-S-06`, `DM-S-07` | `FR-009` | C |
| Audit & Log surface (width, metrics, NIST AU-3, filter, multi-select) | `DM-AL-06`, `DM-AL-08`..`DM-AL-12` | `FR-028`, `FR-022` | B / C |
| Admin Users (add placement, uniqueness, roles/groups multiselect, created-time) | `DM-U-03`..`DM-U-06`, `DM-U-09`, `DM-U-11` | `FR-003` (idam users), `FR-022` | C |
| Admin Groups (seed + styling) | `DM-G-01`, `DM-G-04` | `FR-003` (idam groups), `FR-022` | C |
| Admin API Keys (rename, status placement, prefix clarity) | `DM-AK-08`, `DM-AK-09`, `DM-AK-10` | `FR-003` (idam api-keys), `FR-022` | C |
| Admin RBAC (seed, resource-RBAC, CRUD spec, GUID->username) | `DM-RB-01`, `DM-RB-02`, `DM-RB-08`, `DM-RB-09` | `FR-003` (idam RBAC), `FR-022` | C |
| Admin Roles (code-defined vs data-defined decision) | `DM-RL-02`, `DM-RL-03` | `FR-003` (idam roles) | C (decision) |
| API Docs (reference widget, README, MCP/A2A param+schema columns, safety guide) | `DM-AD-01`, `DM-AD-04`, `DM-AD-06`..`DM-AD-09` | `FR-020` (MCP), `FR-021` (A2A), `FR-022` | C |
| MCP Console (admin pre-filter, history collapse, download/copy) | `DM-MC-01`, `DM-MC-06`, `DM-MC-07` | `FR-020` | C |
| A2A Console (agent-card formatting, skill pick-list) | `DM-AC-04`, `DM-AC-05` | `FR-021` | C |
| Jobs (filters, thinking tab, keep/remove `/jobs` decision) | `DM-J-01`, `DM-J-02`, `DM-J-08`, `DM-J-11` | `FR-024`, `FR-022` | C (decision) |
| Settings (value-column justify) | `DM-SET-01` | `FR-022`, `FR-023` | C |
| Cross-cutting WebUI (button placement, title-case, activity label, confirm modal, help-tips, column picker overlay, status placement, NIST AU-3 ruling, shared multiselect) | `DM-X-04`, `DM-X-05`, `DM-X-08`, `DM-X-11`, `DM-X-15`..`DM-X-19` | `FR-022` + W28E-1825 PS-WEBUI-STYLE-COMPONENTS (cross-svc); `DM-X-19` -> `FR-028` | C / cross-cutting |

Cross-cutting observations `DM-X-16`/`DM-X-17`/`DM-X-18` (column-picker overlay, shared
`<StructuredMultiSelect>` / `<HelpTip>` primitives, status-column-left invariant) apply to
every service WebUI and are routed to W28E-1825 (PS-WEBUI-STYLE-COMPONENTS); they are
recorded here for traceability but owned by the cross-cutting lane.

## W28E-1808A source-verified note

- The canonical FR-NNN set (FR-001..FR-028) is source-verified against `src/core/`
  (access_control, audit, catalog, connectors, content, discovery, filters, relationships,
  schema, search, test_data) and `src/servers/` (api, mcp, a2a, web).
- Connector adapters present on `main`: `mongodb`, `postgresql`, `mariadb`, `couchdb`,
  `opensearch`, `elasticsearch`, `cassandra` (seven).
- The W28C-1711-R3 mechanical FR rows (tier-cluster derivations) are superseded by this
  capability map; the FR-id migration is recorded in
  `working/evidence/W28E-1808A/current/03-requirements-map.tsv`.
- The 2026-06-16 W28C-1711 knowledge SUPPLEMENT dump file (`E2E db-mcp-server.md`) is
  un-triaged by the operator (no NEW-REQ/NEW-AT/DUPLICATE/SUPERSEDED/DEFER decision); per
  template T-W28E-A it is recorded as DEFER and NOT authored against in this lane.
