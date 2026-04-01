# db-mcp-server — REQUIREMENTS
## W28A-421 Review Status
- Reviewed for external/shareable publication during W28A-421.
- Source basis: `defaults.yaml`, 4 server source files, 31 discovered routes/endpoints, and 46 MCP tools.
- Internal-only absolute paths, environment-specific hosts, and private registries have been removed from this shareable document set.

**Version:** 0.1 • 2026-03-21
**Status:** Planning

## Executive Summary
`db-mcp-server` is a planned Cloud-Dog AI MCP and admin service for NoSQL/search platform discovery, schema inspection, structured content operations, relationship management, and discovery indexing. Phase 1 focuses on MongoDB, CouchDB, OpenSearch, Elasticsearch, and Cassandra using a profile-based connection model with RBAC, structured filters instead of free-text query generation, auditable schema-change workflows, and indexed discovery/search.

## Platform Alignment
- Configuration: `cloud_dog_config`
- Logging and audit: `cloud_dog_logging`
- API/Web runtime: `cloud_dog_api_kit`
- Identity, users, groups, API keys, RBAC: `cloud_dog_idam`
- Jobs and workers: `cloud_dog_jobs`
- Metadata/audit persistence: `cloud_dog_db`
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
The system shall use `cloud_dog_config`, `cloud_dog_logging`, `cloud_dog_api_kit`, `cloud_dog_idam`, `cloud_dog_jobs`, and `cloud_dog_db`.
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
The system shall support preprod and production deployment overlays with Vault-backed credentials.
Acceptance criteria:
- preprod documentation skeleton exists
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
