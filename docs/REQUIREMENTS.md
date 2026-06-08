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
