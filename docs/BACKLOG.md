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
