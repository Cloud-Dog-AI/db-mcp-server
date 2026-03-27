# Configuration Parameters

All parameters can be set via `defaults.yaml`, `config.yaml`, environment variables, or Vault.

## Application

| Parameter | Default | Env Override | Description |
|-----------|---------|-------------|-------------|
| app.name | db-mcp-server | - | Application name |
| app.version | 0.1.0 | - | Application version |
| app.environment | dev | CLOUD_DOG_ENVIRONMENT | Deployment environment |
| app.url | https://dbmcp.cloud-dog.net | - | Public URL |
| service_name | db-mcp-server | - | Service name |
| service_instance | db-mcp-local | HOSTNAME | Service instance ID |
| environment | dev | CLOUD_DOG_ENVIRONMENT | Environment name |

## Server Ports

| Parameter | Default | Env Override | Description |
|-----------|---------|-------------|-------------|
| api_server.enabled | true | - | Enable API server |
| api_server.host | 0.0.0.0 | - | API server bind address |
| api_server.port | 8086 | - | API server port |
| api_server.cors_origins | [] | - | CORS allowed origins |
| web_server.enabled | true | - | Enable web server |
| web_server.host | 0.0.0.0 | - | Web server bind address |
| web_server.port | 8087 | - | Web server port |
| web_server.api_base_url | http://127.0.0.1:8086 | - | API base URL for proxy |
| mcp_server.enabled | true | - | Enable MCP server |
| mcp_server.host | 0.0.0.0 | - | MCP server bind address |
| mcp_server.port | 8088 | - | MCP server port |
| mcp_server.transport_modes | [streamable_http, http_jsonrpc, legacy_sse] | - | MCP transport modes |
| a2a_server.enabled | true | - | Enable A2A server |
| a2a_server.host | 0.0.0.0 | - | A2A server bind address |
| a2a_server.port | 8089 | - | A2A server port |
| a2a_server.websocket_path | /a2a/ws | - | WebSocket path |

## Authentication

| Parameter | Default | Env Override | Description |
|-----------|---------|-------------|-------------|
| auth.mode | api_key_only | - | Auth mode |
| auth.api_key | (empty) | Vault | API key |
| auth.default_role | admin | - | Default role for authenticated users |
| auth.jwt_secret | (empty) | Vault | JWT signing secret |

## Access Control

| Parameter | Default | Env Override | Description |
|-----------|---------|-------------|-------------|
| access_control.bootstrap_admin.user_id | bootstrap-admin | - | Bootstrap admin user ID |
| access_control.bootstrap_admin.username | bootstrap-admin | - | Bootstrap admin username |
| access_control.bootstrap_admin.display_name | Bootstrap Admin | - | Bootstrap admin display name |
| access_control.bootstrap_admin.api_key_name | bootstrap-admin-key | - | Bootstrap admin API key name |

### Roles

| Role | Permissions |
|------|-------------|
| admin | * (all) |
| data_steward | catalog.read, schema.read, schema.change, relationship.read, relationship.change, content.search, data.read, data.create, data.update, data.delete, index.manage, profile.manage, audit.read |
| developer | catalog.read, schema.read, schema.change, relationship.read, content.search, data.read, data.create, data.update, index.manage |
| analyst | catalog.read, schema.read, relationship.read, content.search, data.read |
| auditor | catalog.read, schema.read, relationship.read, audit.read, data.read |

## Data Stores

| Parameter | Default | Env Override | Description |
|-----------|---------|-------------|-------------|
| metadata_store.uri | sqlite:///./data/dbmcp_metadata.db | Vault | Metadata database URI |
| audit_store.uri | sqlite:///./data/dbmcp_audit.db | Vault | Audit database URI |

## Jobs

| Parameter | Default | Env Override | Description |
|-----------|---------|-------------|-------------|
| jobs.backend | memory | - | Jobs backend (memory) |
| jobs.payload_max_bytes | 16384 | - | Max job payload size |

## Search (Discovery Index)

| Parameter | Default | Env Override | Description |
|-----------|---------|-------------|-------------|
| search.enabled | true | - | Enable discovery search |
| search.discovery_index_path | ./data/discovery-index.db | - | Discovery index database path |
| search.metadata_limit | 20 | - | Max metadata search results |
| search.content_limit | 20 | - | Max content search results |
| search.max_documents_per_entity | 10 | - | Max documents per entity |
| search.max_excerpt_chars | 240 | - | Max excerpt character length |
| search.freshness_seconds | 3600 | - | Cache freshness TTL |
| search.inline_sync | true | - | Enable inline index sync |

## Connectors

### MongoDB

| Parameter | Default | Env Override | Description |
|-----------|---------|-------------|-------------|
| connectors.mongodb.enabled | true | - | Enable MongoDB connector |
| connectors.mongodb.default_uri | (empty) | Vault | Default MongoDB URI |
| connectors.mongodb.timeout_ms | 30000 | - | Connection timeout (ms) |

### CouchDB

| Parameter | Default | Env Override | Description |
|-----------|---------|-------------|-------------|
| connectors.couchdb.enabled | true | - | Enable CouchDB connector |
| connectors.couchdb.default_uri | http://admin:cloud-dog-test@127.0.0.1:5984 | Vault | Default CouchDB URI |
| connectors.couchdb.timeout_seconds | 30 | - | Connection timeout |

### OpenSearch

| Parameter | Default | Env Override | Description |
|-----------|---------|-------------|-------------|
| connectors.opensearch.enabled | true | - | Enable OpenSearch connector |
| connectors.opensearch.default_uri | (empty) | Vault | Default OpenSearch URI |
| connectors.opensearch.timeout_seconds | 30 | - | Connection timeout |

### Elasticsearch

| Parameter | Default | Env Override | Description |
|-----------|---------|-------------|-------------|
| connectors.elasticsearch.enabled | true | - | Enable Elasticsearch connector |
| connectors.elasticsearch.default_uri | (empty) | Vault | Default Elasticsearch URI |
| connectors.elasticsearch.timeout_seconds | 30 | - | Connection timeout |

### Cassandra

| Parameter | Default | Env Override | Description |
|-----------|---------|-------------|-------------|
| connectors.cassandra.enabled | true | - | Enable Cassandra connector |
| connectors.cassandra.default_host | (empty) | Vault | Default Cassandra host |
| connectors.cassandra.default_port | 9042 | - | Default Cassandra port |
| connectors.cassandra.timeout_seconds | 30 | - | Connection timeout |

## Runtime

| Parameter | Default | Env Override | Description |
|-----------|---------|-------------|-------------|
| runtime.health_exempt_paths | [/health, /ready, /live, /status, /docs, /redoc, /openapi.json] | - | Paths exempt from auth |

## Logging

| Parameter | Default | Env Override | Description |
|-----------|---------|-------------|-------------|
| log.level | INFO | - | Log level |
| log.format | json | - | Log format |
| log.console | true | - | Log to console |
| log.pii_redaction | true | - | Enable PII redaction |
| log.service_instance | db-mcp-local | HOSTNAME | Service instance ID |
| log.environment | dev | CLOUD_DOG_ENVIRONMENT | Deployment environment |
| log.app_log | logs/app.log.jsonl | - | Application log file |
| log.audit_log | logs/audit.log.jsonl | - | Audit log file |
| log.integrity.enabled | false | - | Enable log integrity checks |
