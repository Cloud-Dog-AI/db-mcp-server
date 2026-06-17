---
doc-id: WARRANTY-1.0RC01
project: db-mcp-server
generated: 2026-06-17T11:58:09Z
generator: scripts/build-warranty-table.py v1.0
standard: PS-CLOSEOUT-WARRANTY v1.0
---

# db-mcp-server — 1.0RC01 Release Warranty Table

Per PS-CLOSEOUT-WARRANTY: every row must reach `verdict=PASS` before the lane may close.
`PENDING` columns are filled by Stream-B (Section B) and Stream-C (Section C).

## Section A — Requirements + UseCases + Test-Design coverage

_W28E-1808A Stream-A finalised: every Section-A row PASS. `cross_surface_covered` = YES (multi-surface design rows present) or `internal-only` (not surface-bound); `webui_observation_bound` cites the DM-* WebUI observation(s) the row closes or `none`. `binding_row_present` = YES (FR/CS have @pytest.mark.req tests; UC bound via their FR/CS tests). Section B/C remain PENDING for Stream-B/C._

| id | kind | title | since | source_evidence | design_row_present | binding_row_present | cross_surface_covered | webui_observation_bound | verdict |
|---|---|---|---|---|---|---|---|---|---|
| `FR-001` | FR | Flat-login authentication contract (admin/read-write/read-only; anon 401) | `2d11a0c` | docs/REQUIREMENTS.md (W28E-1808A canonical capability map) | YES | YES | YES | none | **PASS** |
| `FR-002` | FR | Auth middleware + cookie<->api-key bridge | `d064aa1` | docs/REQUIREMENTS.md (W28E-1808A canonical capability map) | YES | YES | YES | none | **PASS** |
| `FR-003` | FR | Access-control service + shared cloud_dog_idam RBAC | `2d11a0c` | docs/REQUIREMENTS.md (W28E-1808A canonical capability map) | YES | YES | YES | DM-U-03..06/09/11, DM-G-01/04, DM-AK-08..10, DM-RB-01/02/08/09, DM-RL-02/03 | **PASS** |
| `FR-004` | FR | Source-connection registry + connection-profile CRUD + scope | `2d11a0c` | docs/REQUIREMENTS.md (W28E-1808A canonical capability map) | YES | YES | YES | DM-P-18/22/23/24 | **PASS** |
| `FR-005` | FR | Catalogue + metadata discovery | `d064aa1` | docs/REQUIREMENTS.md (W28E-1808A canonical capability map) | YES | YES | YES | DM-CAT-02 | **PASS** |
| `FR-006` | FR | Structured content CRUD operations | `d064aa1` | docs/REQUIREMENTS.md (W28E-1808A canonical capability map) | YES | YES | YES | DM-DB-06/07/08 | **PASS** |
| `FR-007` | FR | Structured-filter operator grammar + filter model | `d064aa1` | docs/REQUIREMENTS.md (W28E-1808A canonical capability map) | YES | YES | YES | DM-DB-05/08 | **PASS** |
| `FR-008` | FR | Relationship management (list/curate/infer) | `d064aa1` | docs/REQUIREMENTS.md (W28E-1808A canonical capability map) | YES | YES | YES | DM-RE-04 | **PASS** |
| `FR-009` | FR | Schema introspection + change workflow | `d064aa1` | docs/REQUIREMENTS.md (W28E-1808A canonical capability map) | YES | YES | YES | DM-S-06/07 | **PASS** |
| `FR-010` | FR | Search + discovery indexing | `d064aa1` | docs/REQUIREMENTS.md (W28E-1808A canonical capability map) | YES | YES | YES | DM-SR-07 | **PASS** |
| `FR-011` | FR | Saved-query persistence + replay | `2d11a0c` | docs/REQUIREMENTS.md (W28E-1808A canonical capability map) | YES | YES | YES | none | **PASS** |
| `FR-012` | FR | Gated test-data seeding | `2d11a0c` | docs/REQUIREMENTS.md (W28E-1808A canonical capability map) | YES | YES | YES | none | **PASS** |
| `FR-013` | FR | MongoDB connector | `d064aa1` | docs/REQUIREMENTS.md (W28E-1808A canonical capability map) | YES | YES | internal-only | none | **PASS** |
| `FR-014` | FR | CouchDB connector | `d064aa1` | docs/REQUIREMENTS.md (W28E-1808A canonical capability map) | YES | YES | internal-only | none | **PASS** |
| `FR-015` | FR | OpenSearch connector | `d064aa1` | docs/REQUIREMENTS.md (W28E-1808A canonical capability map) | YES | YES | internal-only | none | **PASS** |
| `FR-016` | FR | Elasticsearch connector | `d064aa1` | docs/REQUIREMENTS.md (W28E-1808A canonical capability map) | YES | YES | internal-only | none | **PASS** |
| `FR-017` | FR | Cassandra connector | `d064aa1` | docs/REQUIREMENTS.md (W28E-1808A canonical capability map) | YES | YES | internal-only | none | **PASS** |
| `FR-018` | FR | Relational connector dispatch (PostgreSQL/MariaDB) | `d064aa1` | docs/REQUIREMENTS.md (W28E-1808A canonical capability map) | YES | YES | internal-only | none | **PASS** |
| `FR-019` | FR | Multi-backend connector matrix | `d064aa1` | docs/REQUIREMENTS.md (W28E-1808A canonical capability map) | YES | YES | internal-only | none | **PASS** |
| `FR-020` | FR | MCP server + tool registry | `d064aa1` | docs/REQUIREMENTS.md (W28E-1808A canonical capability map) | YES | YES | YES | DM-MC-01/06/07, DM-AD-06/07 | **PASS** |
| `FR-021` | FR | A2A server + agent card | `d064aa1` | docs/REQUIREMENTS.md (W28E-1808A canonical capability map) | YES | YES | YES | DM-AC-04/05, DM-AD-08 | **PASS** |
| `FR-022` | FR | WebUI serving (SPA + canonical pages) | `2d11a0c` | docs/REQUIREMENTS.md (W28E-1808A canonical capability map) | YES | YES | YES | DM-D-07/08/12/13, DM-X-04/05/08/11/15/16, DM-SET-01 | **PASS** |
| `FR-023` | FR | Configuration loading + masked provenance | `d064aa1` | docs/REQUIREMENTS.md (W28E-1808A canonical capability map) | YES | YES | YES | DM-SET-01 | **PASS** |
| `FR-024` | FR | Async job lifecycle (cloud_dog_jobs) | `d064aa1` | docs/REQUIREMENTS.md (W28E-1808A canonical capability map) | YES | YES | YES | DM-J-01/02/08/11 | **PASS** |
| `FR-025` | FR | Four-surface server startup + health | `d064aa1` | docs/REQUIREMENTS.md (W28E-1808A canonical capability map) | YES | YES | YES | none | **PASS** |
| `FR-026` | FR | Project-structure / packaging quality | `d064aa1` | docs/REQUIREMENTS.md (W28E-1808A canonical capability map) | YES | YES | internal-only | none | **PASS** |
| `FR-027` | FR | Live preprod deployment contract (b-method IDAM) | `2d11a0c` | docs/REQUIREMENTS.md (W28E-1808A canonical capability map) | YES | YES | YES | none | **PASS** |
| `FR-028` | FR | Audit logging (NIST AU-3 capture + query) | `d064aa1` | docs/REQUIREMENTS.md (W28E-1808A canonical capability map) | YES | YES | YES | DM-AL-06/08..12, DM-D-12, DM-X-19 | **PASS** |
| `CS-001` | CS | Anon attempts data read (401) | `d064aa1` | docs/REQUIREMENTS.md (W28E-1808A canonical capability map) | YES | YES | YES | none | **PASS** |
| `CS-002` | CS | read-only attempts write (403) | `d064aa1` | docs/REQUIREMENTS.md (W28E-1808A canonical capability map) | YES | YES | YES | none | **PASS** |
| `CS-003` | CS | Missing required param (422) | `d064aa1` | docs/REQUIREMENTS.md (W28E-1808A canonical capability map) | YES | YES | YES | none | **PASS** |
| `CS-004` | CS | Wrong-role privileged op (403) | `d064aa1` | docs/REQUIREMENTS.md (W28E-1808A canonical capability map) | YES | YES | YES | none | **PASS** |
| `CS-005` | CS | anon-denied api (401) | `d064aa1` | docs/REQUIREMENTS.md (W28E-1808A canonical capability map) | YES | YES | YES | none | **PASS** |
| `CS-006` | CS | anon-denied mcp (401) | `d064aa1` | docs/REQUIREMENTS.md (W28E-1808A canonical capability map) | YES | YES | YES | none | **PASS** |
| `CS-007` | CS | anon-denied a2a (401) | `d064aa1` | docs/REQUIREMENTS.md (W28E-1808A canonical capability map) | YES | YES | YES | none | **PASS** |
| `CS-008` | CS | anon-denied webui (401) | `d064aa1` | docs/REQUIREMENTS.md (W28E-1808A canonical capability map) | YES | YES | YES | none | **PASS** |
| `CS-009` | CS | wrong-role-denied api (403) | `d064aa1` | docs/REQUIREMENTS.md (W28E-1808A canonical capability map) | YES | YES | YES | none | **PASS** |
| `CS-010` | CS | wrong-role-denied mcp (403) | `d064aa1` | docs/REQUIREMENTS.md (W28E-1808A canonical capability map) | YES | YES | YES | none | **PASS** |
| `CS-011` | CS | wrong-role-denied a2a (403) | `d064aa1` | docs/REQUIREMENTS.md (W28E-1808A canonical capability map) | YES | YES | YES | none | **PASS** |
| `CS-012` | CS | wrong-role-denied webui (403) | `d064aa1` | docs/REQUIREMENTS.md (W28E-1808A canonical capability map) | YES | YES | YES | none | **PASS** |
| `CS-013` | CS | missing-param-error api (422) | `d064aa1` | docs/REQUIREMENTS.md (W28E-1808A canonical capability map) | YES | YES | YES | none | **PASS** |
| `CS-014` | CS | missing-param-error mcp (422) | `d064aa1` | docs/REQUIREMENTS.md (W28E-1808A canonical capability map) | YES | YES | YES | none | **PASS** |
| `CS-015` | CS | missing-param-error a2a (422) | `d064aa1` | docs/REQUIREMENTS.md (W28E-1808A canonical capability map) | YES | YES | YES | none | **PASS** |
| `CS-016` | CS | missing-param-error webui (422) | `d064aa1` | docs/REQUIREMENTS.md (W28E-1808A canonical capability map) | YES | YES | YES | none | **PASS** |
| `UC-001` | UC | Admin manages connection profiles + source connections | `d064aa1` | docs/ROLES-AND-USECASES.md §8 (UC inventory) | YES | YES | YES | DM-P-18/22/23/24 | **PASS** |
| `UC-002` | UC | Analyst/developer browses catalogue | `d064aa1` | docs/ROLES-AND-USECASES.md §8 (UC inventory) | YES | YES | YES | DM-CAT-02 | **PASS** |
| `UC-003` | UC | Analyst reads content via structured filter | `d064aa1` | docs/ROLES-AND-USECASES.md §8 (UC inventory) | YES | YES | YES | DM-DB-05/08 | **PASS** |
| `UC-004` | UC | Developer creates/updates/deletes content | `d064aa1` | docs/ROLES-AND-USECASES.md §8 (UC inventory) | YES | YES | YES | DM-DB-06 | **PASS** |
| `UC-005` | UC | Developer lists/curates/infers relationships | `d064aa1` | docs/ROLES-AND-USECASES.md §8 (UC inventory) | YES | YES | YES | DM-RE-04 | **PASS** |
| `UC-006` | UC | Data steward plans+approves schema change | `d064aa1` | docs/ROLES-AND-USECASES.md §8 (UC inventory) | YES | YES | YES | DM-S-06/07 | **PASS** |
| `UC-007` | UC | Analyst searches indexed metadata/content | `d064aa1` | docs/ROLES-AND-USECASES.md §8 (UC inventory) | YES | YES | YES | DM-SR-07 | **PASS** |
| `UC-008` | UC | Developer saves+replays a query | `d064aa1` | docs/ROLES-AND-USECASES.md §8 (UC inventory) | YES | YES | YES | none | **PASS** |
| `UC-009` | UC | Admin seeds gated test data | `d064aa1` | docs/ROLES-AND-USECASES.md §8 (UC inventory) | YES | YES | YES | none | **PASS** |
| `UC-010` | UC | Developer operates a MongoDB source | `d064aa1` | docs/ROLES-AND-USECASES.md §8 (UC inventory) | YES | YES | internal-only | none | **PASS** |
| `UC-011` | UC | Developer operates a CouchDB source | `d064aa1` | docs/ROLES-AND-USECASES.md §8 (UC inventory) | YES | YES | internal-only | none | **PASS** |
| `UC-012` | UC | Developer operates an OpenSearch source | `d064aa1` | docs/ROLES-AND-USECASES.md §8 (UC inventory) | YES | YES | internal-only | none | **PASS** |
| `UC-013` | UC | Developer operates an Elasticsearch source | `d064aa1` | docs/ROLES-AND-USECASES.md §8 (UC inventory) | YES | YES | internal-only | none | **PASS** |
| `UC-014` | UC | Developer operates a Cassandra source | `d064aa1` | docs/ROLES-AND-USECASES.md §8 (UC inventory) | YES | YES | internal-only | none | **PASS** |
| `UC-015` | UC | Developer operates a relational source | `d064aa1` | docs/ROLES-AND-USECASES.md §8 (UC inventory) | YES | YES | internal-only | none | **PASS** |
| `UC-016` | UC | Operator verifies seven-connector matrix | `d064aa1` | docs/ROLES-AND-USECASES.md §8 (UC inventory) | YES | YES | internal-only | none | **PASS** |
| `UC-017` | UC | MCP client invokes registered tools | `d064aa1` | docs/ROLES-AND-USECASES.md §8 (UC inventory) | YES | YES | YES | DM-MC-01/06/07 | **PASS** |
| `UC-018` | UC | Peer agent invokes A2A skills | `d064aa1` | docs/ROLES-AND-USECASES.md §8 (UC inventory) | YES | YES | YES | DM-AC-04/05 | **PASS** |
| `UC-019` | UC | User operates the WebUI page set | `d064aa1` | docs/ROLES-AND-USECASES.md §8 (UC inventory) | YES | YES | YES | DM-D-07/08, DM-X-04/05/08/11 | **PASS** |
| `UC-020` | UC | Admin reads masked effective config | `d064aa1` | docs/ROLES-AND-USECASES.md §8 (UC inventory) | YES | YES | YES | DM-SET-01 | **PASS** |
| `UC-021` | UC | Operator runs indexing/schema jobs | `d064aa1` | docs/ROLES-AND-USECASES.md §8 (UC inventory) | YES | YES | YES | DM-J-01/02/08/11 | **PASS** |
| `UC-022` | UC | Any role checks four-surface health | `d064aa1` | docs/ROLES-AND-USECASES.md §8 (UC inventory) | YES | YES | YES | none | **PASS** |
| `UC-023` | UC | Admin/rw/ro authenticate via flat-login | `d064aa1` | docs/ROLES-AND-USECASES.md §8 (UC inventory) | YES | YES | YES | none | **PASS** |
| `UC-024` | UC | Admin manages users/groups/api-keys/RBAC via idam | `d064aa1` | docs/ROLES-AND-USECASES.md §8 (UC inventory) | YES | YES | YES | DM-U/G/AK/RB-* | **PASS** |
| `UC-025` | UC | Auditor reviews NIST AU-3 audit events | `d064aa1` | docs/ROLES-AND-USECASES.md §8 (UC inventory) | YES | YES | YES | DM-AL-09/10/11 | **PASS** |
| `UC-026` | UC | System validates live preprod contract | `d064aa1` | docs/ROLES-AND-USECASES.md §8 (UC inventory) | YES | YES | YES | none | **PASS** |
| `UC-027` | UC | Auditor verifies platform-package quality | `d064aa1` | docs/ROLES-AND-USECASES.md §8 (UC inventory) | YES | YES | internal-only | none | **PASS** |
| `UC-028` | UC | Anonymous visitor denied (401) | `d064aa1` | docs/ROLES-AND-USECASES.md §8 (UC inventory) | YES | YES | YES | none | **PASS** |
| `UC-029` | UC | Read-only user denied write (403) | `d064aa1` | docs/ROLES-AND-USECASES.md §8 (UC inventory) | YES | YES | YES | none | **PASS** |
| `UC-030` | UC | Missing/invalid param rejected (422) | `d064aa1` | docs/ROLES-AND-USECASES.md §8 (UC inventory) | YES | YES | YES | none | **PASS** |
| `UC-031` | UC | Wrong-role privileged op denied + audited (403) | `d064aa1` | docs/ROLES-AND-USECASES.md §8 (UC inventory) | YES | YES | YES | none | **PASS** |

## Section B — Functional delivery coverage

| id | impl_committed | unit_test | integration_test | acceptance_test | surface_api | surface_mcp | surface_a2a | idam_role_negative | audit_event_emitted | ajobs_integration | preprod_deployed | preprod_smoke | sibling_regression | variation_pinned | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `FR-001` | PENDING | BOUND | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| `FR-002` | PENDING | BOUND | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| `FR-003` | PENDING | BOUND | BOUND | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| `FR-004` | PENDING | BOUND | BOUND | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| `FR-005` | PENDING | BOUND | BOUND | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| `FR-006` | PENDING | BOUND | BOUND | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| `FR-007` | PENDING | BOUND | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| `FR-008` | PENDING | BOUND | BOUND | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| `FR-009` | PENDING | BOUND | BOUND | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| `FR-010` | PENDING | BOUND | BOUND | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| `FR-011` | PENDING | PENDING | BOUND | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| `FR-012` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| `FR-013` | PENDING | BOUND | BOUND | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| `FR-014` | PENDING | BOUND | BOUND | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| `FR-015` | PENDING | BOUND | BOUND | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| `FR-016` | PENDING | BOUND | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| `FR-017` | PENDING | BOUND | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| `FR-018` | PENDING | BOUND | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| `FR-019` | PENDING | PENDING | BOUND | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| `FR-020` | PENDING | BOUND | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| `FR-021` | PENDING | BOUND | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| `FR-022` | PENDING | BOUND | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| `FR-023` | PENDING | BOUND | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| `FR-024` | PENDING | BOUND | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| `FR-025` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| `FR-026` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| `FR-027` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| `FR-028` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |

## Section C — WebUI + E2E coverage

| page | role | uc_id | playwright_spec | screenshot | axe_a11y | style_conformance | url_canonical | positive_assertion | negative_assertion | webui_observation_closed | preprod_url_smoke | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Login | admin | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Login | read-write | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Login | read-only | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Login | anon | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Top-Menu | admin | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Top-Menu | read-write | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Top-Menu | read-only | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Top-Menu | anon | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Left-Menu | admin | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Left-Menu | read-write | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Left-Menu | read-only | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Left-Menu | anon | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Footer | admin | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Footer | read-write | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Footer | read-only | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Footer | anon | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Audit-Log | admin | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Audit-Log | read-write | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Audit-Log | read-only | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Audit-Log | anon | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Admin-Users | admin | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Admin-Users | read-write | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Admin-Users | read-only | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Admin-Users | anon | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Admin-Groups | admin | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Admin-Groups | read-write | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Admin-Groups | read-only | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Admin-Groups | anon | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Admin-API-Keys | admin | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Admin-API-Keys | read-write | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Admin-API-Keys | read-only | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Admin-API-Keys | anon | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Admin-Roles | admin | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Admin-Roles | read-write | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Admin-Roles | read-only | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Admin-Roles | anon | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Admin-RBAC | admin | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Admin-RBAC | read-write | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Admin-RBAC | read-only | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Admin-RBAC | anon | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Developer-API-Docs | admin | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Developer-API-Docs | read-write | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Developer-API-Docs | read-only | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Developer-API-Docs | anon | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Developer-MCP-Console | admin | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Developer-MCP-Console | read-write | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Developer-MCP-Console | read-only | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Developer-MCP-Console | anon | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Developer-A2A-Console | admin | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Developer-A2A-Console | read-write | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Developer-A2A-Console | read-only | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Developer-A2A-Console | anon | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| System-Jobs | admin | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| System-Jobs | read-write | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| System-Jobs | read-only | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| System-Jobs | anon | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| System-Settings | admin | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| System-Settings | read-write | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| System-Settings | read-only | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| System-Settings | anon | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| System-About | admin | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| System-About | read-write | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| System-About | read-only | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| System-About | anon | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | admin | `UC-001` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-write | `UC-001` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-only | `UC-001` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | anon | `UC-001` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | admin | `UC-002` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-write | `UC-002` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-only | `UC-002` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | anon | `UC-002` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | admin | `UC-003` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-write | `UC-003` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-only | `UC-003` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | anon | `UC-003` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | admin | `UC-004` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-write | `UC-004` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-only | `UC-004` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | anon | `UC-004` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | admin | `UC-005` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-write | `UC-005` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-only | `UC-005` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | anon | `UC-005` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | admin | `UC-006` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-write | `UC-006` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-only | `UC-006` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | anon | `UC-006` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | admin | `UC-007` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-write | `UC-007` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-only | `UC-007` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | anon | `UC-007` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | admin | `UC-008` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-write | `UC-008` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-only | `UC-008` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | anon | `UC-008` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | admin | `UC-009` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-write | `UC-009` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-only | `UC-009` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | anon | `UC-009` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | admin | `UC-010` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-write | `UC-010` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-only | `UC-010` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | anon | `UC-010` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | admin | `UC-011` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-write | `UC-011` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-only | `UC-011` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | anon | `UC-011` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | admin | `UC-012` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-write | `UC-012` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-only | `UC-012` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | anon | `UC-012` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | admin | `UC-013` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-write | `UC-013` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-only | `UC-013` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | anon | `UC-013` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | admin | `UC-014` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-write | `UC-014` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-only | `UC-014` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | anon | `UC-014` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | admin | `UC-015` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-write | `UC-015` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-only | `UC-015` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | anon | `UC-015` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | admin | `UC-016` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-write | `UC-016` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-only | `UC-016` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | anon | `UC-016` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | admin | `UC-017` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-write | `UC-017` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-only | `UC-017` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | anon | `UC-017` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | admin | `UC-018` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-write | `UC-018` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-only | `UC-018` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | anon | `UC-018` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | admin | `UC-019` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-write | `UC-019` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-only | `UC-019` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | anon | `UC-019` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | admin | `UC-020` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-write | `UC-020` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-only | `UC-020` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | anon | `UC-020` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | admin | `UC-021` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-write | `UC-021` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-only | `UC-021` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | anon | `UC-021` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | admin | `UC-022` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-write | `UC-022` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-only | `UC-022` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | anon | `UC-022` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | admin | `UC-023` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-write | `UC-023` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-only | `UC-023` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | anon | `UC-023` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | admin | `UC-024` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-write | `UC-024` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-only | `UC-024` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | anon | `UC-024` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | admin | `UC-025` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-write | `UC-025` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-only | `UC-025` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | anon | `UC-025` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | admin | `UC-026` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-write | `UC-026` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-only | `UC-026` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | anon | `UC-026` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | admin | `UC-027` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-write | `UC-027` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-only | `UC-027` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | anon | `UC-027` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | admin | `UC-028` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-write | `UC-028` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-only | `UC-028` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | anon | `UC-028` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | admin | `UC-029` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-write | `UC-029` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-only | `UC-029` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | anon | `UC-029` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | admin | `UC-030` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-write | `UC-030` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-only | `UC-030` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | anon | `UC-030` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | admin | `UC-031` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-write | `UC-031` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | read-only | `UC-031` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| (UC-row) | anon | `UC-031` | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |

