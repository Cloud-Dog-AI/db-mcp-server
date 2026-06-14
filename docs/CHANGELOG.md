---
template-id: T-CHG
template-version: 1.0
project: db-mcp-server
doc-last-updated: 2026-06-14T17:35:58Z
doc-conformance-stamp: 2026-06-14T17:35:58Z
---

# db-mcp-server — Changelog

_Created by W28C-1710a recovery to receive carry-forward content from `archive/2026-06-12/`._



<!-- W28C-1710a recovery: full content from archive/2026-06-12/BACKLOG.md (archived sha256=1e87e08c7492, 18 lines) -->

## Recovered domain content — `archive/2026-06-12/BACKLOG.md` (18 lines)

_This section carries forward the full content of the archived predecessor doc verbatim. Topic checklist + SHA256 chain in `cloud-dog-ai-platform-standards/working/evidence/W28C-1710a/per-doc/db-mcp-server/BACKLOG.md.topics.tsv`. Archive contents are unchanged (sha256 stable)._

# db-mcp-server — Backlog

| # | Task | Scope | Dependencies |
|---|---|---|---|
| 274-A | Core MCP server skeleton | 4-server pattern, health, config loading | None |
| 274-B | Access control layer | Users, groups, API keys, profiles, RBAC | 274-A |
| 274-C | MongoDB connector | Adapter implementation + tests | 274-A, 274-B |
| 274-D | CouchDB connector | Adapter implementation + tests | 274-A, 274-B |
| 274-E | OpenSearch connector | Adapter implementation + tests | 274-A, 274-B |
| 274-F | Elasticsearch connector | Adapter implementation + tests | 274-A, 274-B |
| 274-G | Cassandra connector | Adapter implementation + tests | 274-A, 274-B |
| 274-H | Catalogue & schema tools | MCP tools for discovery and schema inspection | 274-A, one connector |
| 274-I | Content operations | Structured read/create/update/delete with filter model | 274-H |
| 274-J | Search & indexing | Content indexer, discovery search, relevance | 274-H |
| 274-K | Relationship management | Declare, infer, curate relationships | 274-H |
| 274-L | Schema change tools | Plan/apply/audit workflow | 274-H |
| 274-M | WebUI admin | Profile, user, search, schema management pages | 274-B |
| 274-N | Docker & deployment | All-in-one Docker, staging deployment | All above |


<!-- W28C-1710a recovery: full content from archive/2026-06-12/TASKS.md (archived sha256=4505e515ee0e, 16 lines) -->

## Recovered domain content — `archive/2026-06-12/TASKS.md` (16 lines)

_This section carries forward the full content of the archived predecessor doc verbatim. Topic checklist + SHA256 chain in `cloud-dog-ai-platform-standards/working/evidence/W28C-1710a/per-doc/db-mcp-server/TASKS.md.topics.tsv`. Archive contents are unchanged (sha256 stable)._

# Tasks

## Current Delivery Tracks
| Workstream | Status | Notes |
|------------|--------|-------|
| Runtime surfaces | Complete | Source files detected: `start_a2a_server.py`, `start_api_server.py`, `start_mcp_server.py`, `start_web_server.py`. |
| API documentation | Complete | `docs/API_DOCUMENTATION.md` reviewed against source inventory. |
| MCP documentation | Complete | `docs/MCP_DOCUMENTATION.md` reviewed against source inventory. |
| Configuration reference | Complete | `docs/PARAMETERS.md` and `docs/ENV-REFERENCE.md` regenerated from `defaults.yaml`. |
| Deployment guidance | Complete | `docs/DEPLOY.md` and `docs/DOCKER.md` refreshed with shareable examples. |
| Test catalogue | Complete | `docs/TESTS.md` refreshed from the current repository inventory. |

## Next Review Cycle
1. Re-run the release-relevant test tiers in the intended deployment environment.
2. Update API and MCP inventories whenever routes or tool contracts change.
3. Keep any non-standard topical docs aligned with the canonical set listed in this repository.
