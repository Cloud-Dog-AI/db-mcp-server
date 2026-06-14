---
template-id: T-RUC
template-version: 1.0
applies-to: docs/ROLES-AND-USECASES.md
registry: service
required: must-have
when-applicable: ""
template-last-updated: 2026-06-12
template-owner: platform-standards

project: db-mcp-server
doc-last-updated: 2026-06-12
doc-git-commit: ee5979008dace594f92b45315bdf687fb1aa00df
doc-git-branch: main
doc-source-shas: []
doc-age-policy: indefinite
doc-conformance-stamp: 2026-06-12T12:00:00Z
---

# db-mcp-server - ROLES-AND-USECASES

> **Template version:** T-RUC v1.0

This document is the W28A-746 b-method traceability matrix for db-mcp. It maps requirements to entity/action, use case, role, surface, and test evidence. Use-case text is taken from [REQUIREMENTS.md](REQUIREMENTS.md) and the W28A-871 source-verified merge section in that file.

## 1. Roles

| Role | From | Permissions and purpose | Reconciliation |
|---|---|---|---|
| admin | platform/db-mcp | `*`; full profile, user, group, API-key, schema, content, relationship, audit, and job control | Matches platform `admin`; seeded as bootstrap and flat-login role. |
| group-admin | platform | manages owned groups and group membership/resource bindings | Present in platform role seed; db-mcp currently uses admin-managed group membership plus group role inheritance for the cascade path. |
| user | platform | shared baseline: WebUI/MCP/A2A/API-doc access, own API-key access, config/log/profile reads, and in-scope domain reads | Platform baseline exists in `cloud_dog_idam`; db-mcp flat roles map user-facing access to `read-only` and `read-write`. |
| restricted | platform | no baseline grants; explicit grants only | Present in platform role seed; used as deny-by-default reference. |
| job-control | platform grant | `jobs.read` and `jobs.control` | Present in platform role seed; db-mcp job mutations also require `index.manage` until the shared grant is consumed everywhere. |
| audit-log | platform grant | `logs.read.all` and `idam.audit.read` | Present in platform role seed; db-mcp local `auditor` grants `audit.read`. |
| read-only | db-mcp flat role | baseline WebUI/MCP/A2A/API-doc access plus `catalog.read`, `schema.read`, `relationship.read`, `content.search`, `data.read`, `audit.read` | Local read role mapped to platform `user` read behaviour. |
| read-write | db-mcp flat role | read-only permissions plus `schema.change`, `relationship.change`, `data.create`, `data.update`, `data.delete`, `index.manage`, `profile.manage` | Local write role for WebUI and API/MCP/A2A mutation paths. |
| data_steward | db-mcp business role | data/schema/relationship/profile/index/audit stewardship | Source-defined in `DEFAULT_ROLE_PERMISSIONS` and REQUIREMENTS AC-04. |
| developer | db-mcp business role | schema, relationship, content, data, and index work without full admin | Source-defined in `DEFAULT_ROLE_PERMISSIONS` and REQUIREMENTS AC-04. |
| analyst | db-mcp business role | catalogue, schema, relationship, search, and data reads | Source-defined in `DEFAULT_ROLE_PERMISSIONS` and REQUIREMENTS AC-04. |
| auditor | db-mcp business role | catalogue/schema/relationship/audit/data reads | Source-defined in `DEFAULT_ROLE_PERMISSIONS` and REQUIREMENTS AC-04. |

## 2. Personas

| Persona | Description | Roles |
|---|---|---|
| Service administrator | Operates db-mcp, manages profiles, users, groups, API keys, source connections, and settings. | `admin` |
| Data steward | Creates connection profiles, reviews schema changes, manages relationships, and audits governed data access. | `data_steward`, `read-write` |
| Developer | Builds and tests connector-backed data flows, schema plans, and indexed discovery operations. | `developer`, `read-write` |
| Analyst | Browses catalogue/entity/data/search surfaces and reads permitted data through profile scope. | `analyst`, `read-only`, `user` |
| Auditor | Reviews access, audit, schema, relationship, and data-read evidence without mutation authority. | `auditor`, `audit-log`, `read-only` |
| Group member | Receives access through group membership; membership add/remove changes effective permissions. | `analyst` or other group-assigned local role |

## 3. Traceability Matrix

| Req | Entity | Action | Use case from REQUIREMENTS.md | Role | Surfaces | Test IDs |
|---|---|---|---|---|---|---|
| CR-01 | Server surface | R | The system shall use the standard four-server Cloud-Dog pattern with API (`8086`), Web (`8087`), MCP (`8088`), and A2A (`8089`) surfaces. | admin, user | API, MCP, A2A, WebUI | T0-DBMCP-HEALTH, W28A746-LIVE |
| CR-02 | Health/status | R | The system shall expose public health/readiness endpoints and authenticated operational status endpoints. | admin, user | API, MCP, A2A, WebUI | T0-DBMCP-HEALTH, ST1.1 |
| CR-03 | Platform packages | R | The system shall use `cloud_dog_config`, `cloud_dog_logging`, `cloud_dog_api_kit`, `cloud_dog_idam`, `cloud_dog_jobs`, `cloud_dog_db`, and `cloud_dog_storage`. | admin | API, MCP, A2A, WebUI | QT1.1, W28A746-GREP |
| CD-01 | Profile | R | The system shall list connection profiles and their enabled source types. | analyst, auditor, admin | API, MCP, A2A, WebUI | ST1.2, IT1.1, W28A746-LIVE |
| CD-02 | Namespace/entity | R | The system shall browse namespaces, databases, collections, indices, and analogous source objects for each connector. | analyst, developer, data_steward | API, MCP, WebUI | ST1.4, IT1.3 |
| CD-03 | Metadata search | R | The system shall support metadata search across profiles, namespaces, entities, fields, and relationships. | analyst, developer | API, MCP, WebUI | ST1.7, IT1.6 |
| CD-04 | Discovery index | C/R/U | The system shall cache and index discovery metadata for fast cross-source lookup. | developer, data_steward | API, MCP, WebUI | UT1.9, UT1.10, IT1.6 |
| SC-01 | Schema | R | The system shall inspect entity schemas, fields, types, constraints, and indices for each source. | analyst, developer, auditor | API, MCP, WebUI | ST1.6, IT1.3 |
| SC-02 | Schema change plan | C | The system shall create schema change plans before any source mutation. | developer, data_steward | API, MCP, WebUI | UT1.12, IT1.7 |
| SC-03 | Schema change apply | U | The system shall apply approved schema changes through auditable jobs. | data_steward, admin | API, MCP, WebUI | UT1.12, IT1.7 |
| SC-04 | Discovery refresh | U | The system shall refresh discovery metadata after schema changes. | developer, data_steward | API, MCP, WebUI | UT1.19, IT1.6 |
| CO-01 | Content | R | The system shall support structured read operations using an explicit filter model. | analyst, developer, data_steward | API, MCP, WebUI | UT1.5, ST1.5, IT1.4 |
| CO-02 | Content | C/U/D | The system shall support structured create, update, and delete operations subject to profile policy and RBAC. | developer, data_steward, read-write | API, MCP, WebUI | ST1.5, IT1.4, W28A746-SMOKE |
| CO-03 | Bulk operation | C/U | The system shall support bulk operations with dry-run previews and job execution. | developer, data_steward | API, MCP, WebUI | UT1.19, IT1.4 |
| CO-04 | Field policy | R/U | The system shall support content masking and field suppression based on role, group, and profile policy. | analyst, auditor, data_steward | API, MCP, WebUI | UT1.3, W28A746-SMOKE |
| CO-05 | Structured filter | R/U/D | The system shall support a documented structured-filter operator grammar for content reads, counts, existence checks, updates, and deletes. | analyst, developer | API, MCP, WebUI | UT1.5, ST1.5 |
| CO-06 | Binary content | C/R/U | The system shall support binary/blob content fields for MongoDB using JSON-safe binary envelopes on write and hex serialisation on read. | developer, data_steward | API, MCP | ST1.5 |
| SI-01 | Search index | C/R/U | The system shall index source metadata and selected content for discovery search. | developer, analyst | API, MCP, WebUI | UT1.9, IT1.6 |
| SI-02 | Search | R | The system shall support keyword, phrase, filtered, and proximity-style search where source capabilities allow. | analyst, developer | API, MCP, WebUI | ST1.7, IT1.6 |
| SI-03 | Search explanation | R | The system shall rank search results using deterministic scoring and optional LLM-generated explanations. | analyst, auditor | API, MCP, WebUI | UT1.10 |
| SI-04 | Index jobs | C/U | The system shall run indexing and refresh work as jobs via `cloud_dog_jobs`. | developer, job-control, data_steward | API, MCP, WebUI | UT1.19, IT1.6 |
| RL-01 | Relationship | R | The system shall list declared, curated, and inferred relationships between entities. | analyst, auditor, developer | API, MCP, WebUI | IT1.5 |
| RL-02 | Relationship | C/U/D | The system shall create and update curated relationship definitions. | developer, data_steward | API, MCP, WebUI | IT1.5 |
| RL-03 | Relationship inference | C/R | The system shall infer candidate relationships from metadata and indexed content. | developer, data_steward | API, MCP, WebUI | IT1.5 |
| CN-01 | MongoDB connector | C/R/U/D | MongoDB connector shall support profile validation, namespace discovery, schema sampling, structured filters, and index metadata. | developer, data_steward | API, MCP, WebUI | ST1.3, IT1.2 |
| CN-02 | CouchDB connector | C/R/U/D | CouchDB connector shall support database discovery, document metadata browsing, view/index awareness, and structured operations. | developer, data_steward | API, MCP, WebUI | ST1.9, IT1.8 |
| CN-03 | OpenSearch connector | C/R/U/D | OpenSearch connector shall support index discovery, mappings, structured search, and schema-change planning. | developer, data_steward | API, MCP, WebUI | ST1.10, IT1.9 |
| CN-04 | Elasticsearch connector | C/R/U/D | Elasticsearch connector shall support index discovery, mappings, structured search, and schema-change planning. | developer, data_steward | API, MCP, WebUI | ST1.12 |
| CN-05 | Cassandra connector | R/U | Cassandra connector shall support keyspace/table discovery, schema inspection, structured reads, and safe change planning. | developer, data_steward | API, MCP, WebUI | ST1.13 |
| AC-01 | Profile/RBAC | gate | The system shall use profile-based connection definitions with RBAC at profile, namespace, entity, and field scope. | all authenticated roles | API, MCP, A2A, WebUI | UT1.3, ST1.2, W28A746-SMOKE |
| AC-02 | Audit event | C | The system shall enforce audit logging for all profile access, discovery, content, schema, and relationship operations. | system, auditor | API, MCP, A2A, WebUI | ST1.2, IT1.1 |
| AC-03 | Masking | R | The system shall support field masking and sensitive-field suppression by role and policy. | analyst, auditor, non-admin | API, MCP, WebUI | UT1.3, W28A746-SMOKE |
| AC-04 | Role model | gate | The system shall provide the five built-in RBAC roles `admin`, `data_steward`, `developer`, `analyst`, and `auditor` with documented default permission sets. | all roles | API, MCP, A2A, WebUI | UT1.3, W28A746-SMOKE |
| AC-05 | User | CRUD | The system shall support admin-only CRUD management for users and user lifecycle state through `cloud_dog_idam`. | admin | API, MCP, A2A, WebUI | ST1.2, IT1.1 |
| AC-06 | Group/API key | CRUD | The system shall support admin-only CRUD management for groups, group membership, and profile-scoped API keys through `cloud_dog_idam`. | admin, group-admin | API, MCP, A2A, WebUI | ST1.2, IT1.1, W28A746-SMOKE |
| CFG-01 | Profile | CRUD | The system shall manage profiles via API, MCP, A2A, Web UI, and config storage. | admin, data_steward, read-write | API, MCP, A2A, WebUI | IT1.1, W28A746-LIVE |
| CFG-02 | Connector template | R | The system shall provide connector templates for MongoDB, CouchDB, OpenSearch, Elasticsearch, and Cassandra. | admin, developer | API, WebUI | UT1.18, ST connector suites |
| CFG-03 | Deployment overlay | R | The system shall support staging and production deployment overlays with secret-store-backed credentials. | admin, operator | API, WebUI | W28A746-DEPLOY |
| NF-01 | Operation plan | gate | The system shall remain deterministic and auditable for executable operations by using structured filters and explicit plans. | developer, data_steward | API, MCP, WebUI | UT1.5, IT1.4 |
| NF-02 | Jobs/health | R/U | The system shall support job-backed retries, timeout controls, and connector health tracking. | developer, job-control, admin | API, MCP, WebUI | UT1.19, ST1.1 |
| NF-03 | Scaling | R | The system shall scale across multiple profiles and large discovery/indexing workloads. | admin, developer | API, MCP, WebUI | IT1.6 |
| NF-04 | Maintainability | R | The system shall be maintainable through connector isolation, platform package reuse, and explicit backlog decomposition. | admin, developer | API, MCP, A2A, WebUI | QT1.1, W28A746-GREP |
| CFG-01 + AC-06 cascade | Group/Profile | U(add member) -> R(profile data) | Admin-authenticated flows support create, read, update, and delete operations for groups plus add/remove user membership changes; profiles shall remain scope boundaries for namespaces, entities, API keys, and allowed permissions. | admin adds; member = analyst/read-only | API, MCP, A2A, WebUI | W28A746-SMOKE, W28A746-LIVE |

## 4. Negative Use Cases

| UC ID | Persona | Attempted | Expected | Test |
|---|---|---|---|---|
| NEG-001 | Anonymous visitor | `/auth/me` and `/api/v1/profiles` | 401/403 and no populated principal | UT1.50, W28A746-LIVE |
| NEG-002 | Read-only user | Profile create through `/webapi/v1/profiles` | 403 inline with `role=read-only` | UT1.52, W28A746-LIVE |
| NEG-003 | Non-admin API key | User/group/admin mutation | 403, audited denial | ST1.2, IT1.1 |
| NEG-004 | Profile-scoped key | Access a profile not in `profile_ids` | 403 profile access denied | UT1.3, W28A746-SMOKE |
| NEG-005 | Masked profile read | Read profile or masked content with embedded credential/sensitive field | Secret redacted or field omitted | UT1.3, W28A746-SMOKE |

## 5. UI Parity And Page Justification

| WebUI page | Use cases | Role |
|---|---|---|
| Dashboard | CR-01, CR-02, NF-02 | all authenticated roles |
| Profiles | CD-01, CFG-01, AC-01 | admin, data_steward, read-only for read paths |
| Catalogue | CD-02, CD-03 | analyst, developer, data_steward |
| Entity Detail | SC-01, RL-01 | analyst, developer, auditor |
| Data Browser | CO-01, CO-02, CO-04, CO-05 | analyst read; read-write/data_steward write |
| Search | CD-03, SI-01, SI-02, SI-03 | analyst, developer |
| Relationships | RL-01, RL-02, RL-03 | developer, data_steward, auditor read |
| Schema Planner | SC-02, SC-03, SC-04 | developer, data_steward |
| Audit | AC-02, audit-log/auditor duties | auditor, admin |
| Users | AC-05 | admin |
| Groups | AC-06 and cascade | admin, group-admin where central guard permits |
| API Keys | AC-06, own-key baseline | admin, user own-key flows |
| RBAC | AC-04 | admin |
| Jobs | SI-04, NF-02 | job-control, admin |
| MCP Console | CR-01 plus every MCP-mapped row | user baseline and role-specific tools |
| A2A Console | CR-01, CFG-01 proxy parity | user baseline and service agents |
| API Docs | CR-01, CR-02 | user baseline |
| Settings | CR-03, CFG-03, AC-03 masking | admin, read-only masked view |

## 6. Cross-references

- [REQUIREMENTS.md](REQUIREMENTS.md)
- [TESTS.md](TESTS.md)
- [ARCHITECTURE.md](ARCHITECTURE.md)
- [API-REFERENCE.md](API-REFERENCE.md)
- [DATA-MODEL.md](DATA-MODEL.md)
- PS-82-access-control-session-test-matrix.md
- PS-83-canonical-role-catalog.md

## 7. Project-specific notes

- The domain resource for the cascade is the db-mcp connection `Profile`.
- Current db-mcp source has no per-profile `group_id` field; group membership affects effective permissions through `AccessControlService._rebuild_rbac()` and API keys/profile scopes enforce the profile boundary.
- W28A-746 does not add a per-service FK or schema change. The central RBAC-binding model remains the cross-service direction from W28A-741.


<!-- W28C-1710b design-delta additions (2026-06-14T18:01:23Z) -->

## Cross-surface UC mappings (W28C-1710b)

Per T-RUC v1.1 + PS-REQ-TEST-TRACE §3.5, every UC-NNN maps to one OR MORE FR-NNN across surfaces.

This service's surface set: **api, mcp, a2a, webui**.

Detailed UC-by-UC operator-review pass + per-FR cross-surface mapping deferred to W28C-1711. The cross-surface declarations are enabled here.

```yaml
# Schema for every UC-NNN (default; operator amends per UC):
surfaces: ['api', 'mcp', 'a2a', 'webui']
roles: [admin, read-write, read-only, anon]
FR-mapping: []  # populated by W28C-1711
```
