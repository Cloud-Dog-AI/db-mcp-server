# db-mcp-server — Context Summary

## Current state
- Four-server runtime skeleton delivered under W28A-274-A
- Access control layer delivered under W28A-274-B
- MongoDB connector delivered under W28A-274-C
- Structured filter model delivered under W28A-274-H-R2
- Core connector-agnostic MCP tools delivered for catalogue, schema, content, relationships, and audit
- Discovery search and indexing delivered under W28A-274-I
- PS-30 WebUI delivered under W28A-274-J
- Cross-backend canonical test data and Docker test environments delivered under W28A-274-K
- Schema change planning/apply/history with audit and discovery refresh delivered under W28A-274-L
- Requirements, architecture, test catalogue, preprod scaffolding, and backlog are in place
- Ports reserved: API 8086, Web 8087, MCP 8088, A2A 8089

## Completed in this setup pass
- Standard project layout created
- Requirements and architecture documents drafted
- Build, deploy, API, env, tests, and preprod docs scaffolded
- Project-local RULES.md drafted for db-mcp scope
- Git repository initialised
- Four server surfaces start and stop through `server_control.sh`
- Profile, user, group, and API-key management implemented with audit
- MongoDB adapter and MCP tool surface implemented with real ST/IT coverage
- Connector manager added to decouple tool execution from MongoDB-specific wiring
- Relationship metadata persistence added in the metadata database
- Audit event browsing added from the JSONL audit sink
- Real seeded multi-collection MongoDB dataset added for discovery, content, and relationship testing
- SQLite FTS5 discovery index added for metadata/content/entity discovery
- Discovery indexing job flow added using `cloud_dog_jobs` memory backend and inline execution
- Search MCP tools added: `search.metadata`, `search.content`, `search.related`, `search.explain_match`
- Index management MCP tools added: `index.status`, `index.sync_profile`, `index.sync_entity`, `index.rebuild`
- Shared-login React WebUI added in the UI monorepo under `apps/db-mcp`
- Web surface now serves `ui/dist`, `/runtime-config.js`, SPA history routes, and same-origin `/api` + `/mcp` proxying
- Playwright E2E + axe coverage added for login, catalogue, data browser, search, settings, and accessibility
- Canonical e-commerce dataset documented in `tests/fixtures/schema.md`
- Seed modules added for MongoDB, CouchDB, OpenSearch, Elasticsearch, and Cassandra
- Docker Compose test environments added under `docker/` for each backend plus an all-in-one stack
- Seed orchestration script added at `scripts/seed-test-data.sh`
- Real Mongo fixture verification added and passing
- Schema change service added with persisted plan/apply history in the metadata database
- Schema MCP tools now include `schema.change.plan`, `schema.change.apply`, and `schema.change.history`
- MongoDB schema change support expanded to collection create/drop plus index create/drop with dry-run before/after state
- Full suite green on current tree:
  - QT + UT: `27 passed`
  - ST: `8 passed`
  - IT: `7 passed`
  - Playwright + axe: `9 passed`
  - Mongo seed verification: `3 passed`

## Next actions
- 274-D through 274-G: remaining source connector implementations
- Add live verification for CouchDB, OpenSearch, Elasticsearch, and Cassandra once those connectors land
- Search result ranking/freshness hardening if Phase 2 adds larger corpora or async workers
- Broader server health/runtime hardening outside Mongo scope
