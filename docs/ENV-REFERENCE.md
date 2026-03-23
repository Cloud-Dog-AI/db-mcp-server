# db-mcp-server — Environment Reference

## Precedence
`os.environ -> --env file -> config.yaml -> defaults.yaml`

## Core variables
- `CLOUD_DOG_ENVIRONMENT`
- `CLOUD_DOG__DBMCP__API_SERVER__*`
- `CLOUD_DOG__DBMCP__WEB_SERVER__*`
- `CLOUD_DOG__DBMCP__MCP_SERVER__*`
- `CLOUD_DOG__DBMCP__A2A_SERVER__*`

## Metadata store
- metadata store URI
- audit store URI

## Connector groups
- MongoDB
- CouchDB
- OpenSearch
- Elasticsearch
- Cassandra

## Security and jobs
- API key / JWT
- job backend
- profile policy settings

Refer to `defaults.yaml` for the current planning skeleton values.
