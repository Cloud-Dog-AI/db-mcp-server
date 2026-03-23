# db-mcp-server — Deploy

## Deployment model
Planned all-in-one Docker deployment with four server surfaces and a background worker.

## Planned runtime surfaces
- API: `8086`
- Web: `8087`
- MCP: `8088`
- A2A: `8089`

## Planned dependencies
- metadata/audit store via `cloud_dog_db`
- Vault-backed connector credentials
- job backend via `cloud_dog_jobs`
- source systems: MongoDB, CouchDB, OpenSearch, Elasticsearch, Cassandra

## Preprod
See [PREPROD.md](PREPROD.md).
