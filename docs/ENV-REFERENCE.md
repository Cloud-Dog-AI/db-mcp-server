# Environment Reference

This reference is generated from `defaults.yaml` and the standard Cloud-Dog environment override pattern.

## `a2a_server`

| Variable | Default | Required | Example | Description |
|----------|---------|----------|---------|-------------|
| `CLOUD_DOG__A2A_SERVER__ENABLED` | `true` | Optional | `true` | Toggle for a2a server. |
| `CLOUD_DOG__A2A_SERVER__HOST` | `0.0.0.0` | Optional | `0.0.0.0` | Host binding or upstream host for a2a server. |
| `CLOUD_DOG__A2A_SERVER__PORT` | `8089` | Optional | `8089` | Port for a2a server connections. |
| `CLOUD_DOG__A2A_SERVER__WEBSOCKET_PATH` | `/a2a/ws` | Optional | `/a2a/ws` | Configuration value for a2a server websocket path. |

## `access_control`

| Variable | Default | Required | Example | Description |
|----------|---------|----------|---------|-------------|
| `CLOUD_DOG__ACCESS_CONTROL__BOOTSTRAP_ADMIN__USER_ID` | `bootstrap-admin` | Optional | `bootstrap-admin` | Configuration value for access control bootstrap admin user id. |
| `CLOUD_DOG__ACCESS_CONTROL__BOOTSTRAP_ADMIN__USERNAME` | `bootstrap-admin` | Optional | `service-admin` | Configuration value for access control bootstrap admin username. |
| `CLOUD_DOG__ACCESS_CONTROL__BOOTSTRAP_ADMIN__DISPLAY_NAME` | `Bootstrap Admin` | Optional | `Bootstrap Admin` | Configuration value for access control bootstrap admin display name. |
| `CLOUD_DOG__ACCESS_CONTROL__BOOTSTRAP_ADMIN__API_KEY_NAME` | `<secret>` | Deployment dependent | `your-api-key` | Credential or authentication setting for the related subsystem. |
| `CLOUD_DOG__ACCESS_CONTROL__ROLES__ADMIN` | `["*"]` | Optional | `<set as needed>` | Configuration value for access control roles admin. |
| `CLOUD_DOG__ACCESS_CONTROL__ROLES__DATA_STEWARD` | `["catalog.read", "schema.read", "schema.change", "relationship.read", "relationship.change", "content.search", "data.rea...` | Optional | `<set as needed>` | Configuration value for access control roles data steward. |
| `CLOUD_DOG__ACCESS_CONTROL__ROLES__DEVELOPER` | `["catalog.read", "schema.read", "schema.change", "relationship.read", "content.search", "data.read", "data.create", "dat...` | Optional | `<set as needed>` | Configuration value for access control roles developer. |
| `CLOUD_DOG__ACCESS_CONTROL__ROLES__ANALYST` | `["catalog.read", "schema.read", "relationship.read", "content.search", "data.read"]` | Optional | `<set as needed>` | Configuration value for access control roles analyst. |
| `CLOUD_DOG__ACCESS_CONTROL__ROLES__AUDITOR` | `["catalog.read", "schema.read", "relationship.read", "audit.read", "data.read"]` | Optional | `<set as needed>` | Configuration value for access control roles auditor. |

## `api_server`

| Variable | Default | Required | Example | Description |
|----------|---------|----------|---------|-------------|
| `CLOUD_DOG__API_SERVER__ENABLED` | `true` | Optional | `true` | Credential or authentication setting for the related subsystem. |
| `CLOUD_DOG__API_SERVER__HOST` | `0.0.0.0` | Optional | `0.0.0.0` | Host binding or upstream host for api server. |
| `CLOUD_DOG__API_SERVER__PORT` | `8086` | Optional | `8086` | Port for api server connections. |
| `CLOUD_DOG__API_SERVER__CORS_ORIGINS` | `[]` | Optional | `<set as needed>` | Credential or authentication setting for the related subsystem. |

## `app`

| Variable | Default | Required | Example | Description |
|----------|---------|----------|---------|-------------|
| `CLOUD_DOG__APP__NAME` | `db-mcp-server` | Optional | `db-mcp-server` | Configuration value for app name. |
| `CLOUD_DOG__APP__VERSION` | `0.1.0` | Optional | `0.1.0` | Configuration value for app version. |
| `CLOUD_DOG__APP__ENVIRONMENT` | `${CLOUD_DOG_ENVIRONMENT || 'dev'}` | Optional | `${CLOUD_DOG_ENVIRONMENT || 'dev'}` | Configuration value for app environment. |
| `CLOUD_DOG__APP__URL` | `<set per environment>` | Deployment dependent | `https://service.example.com` | Endpoint or connection URL for app. |

## `audit_store`

| Variable | Default | Required | Example | Description |
|----------|---------|----------|---------|-------------|
| `CLOUD_DOG__AUDIT_STORE__URI` | `${vault.dev.databases.dbmcp_audit_postgresql.uri || 'sqlite:/...` | Deployment dependent | `https://service.example.com` | Endpoint or connection URL for audit store. |

## `auth`

| Variable | Default | Required | Example | Description |
|----------|---------|----------|---------|-------------|
| `CLOUD_DOG__AUTH__MODE` | `api_key_only` | Optional | `api_key_only` | Configuration value for auth mode. |
| `CLOUD_DOG__AUTH__API_KEY` | `<secret>` | Deployment dependent | `your-api-key` | Credential or authentication setting for the related subsystem. |
| `CLOUD_DOG__AUTH__DEFAULT_ROLE` | `admin` | Optional | `admin` | Configuration value for auth default role. |
| `CLOUD_DOG__AUTH__JWT_SECRET` | `<secret>` | Deployment dependent | `your-secret-value` | Credential or authentication setting for the related subsystem. |

## `connectors`

| Variable | Default | Required | Example | Description |
|----------|---------|----------|---------|-------------|
| `CLOUD_DOG__CONNECTORS__MONGODB__ENABLED` | `true` | Optional | `true` | Toggle for connectors mongodb. |
| `CLOUD_DOG__CONNECTORS__MONGODB__DEFAULT_URI` | `${vault.dev.databases.mongodb.uri}` | Deployment dependent | `${vault.dev.databases.mongodb.uri}` | Endpoint or connection URL for connectors mongodb default. |
| `CLOUD_DOG__CONNECTORS__MONGODB__TIMEOUT_MS` | `30000` | Optional | `30000` | Configuration value for connectors mongodb timeout ms. |
| `CLOUD_DOG__CONNECTORS__COUCHDB__ENABLED` | `true` | Optional | `true` | Toggle for connectors couchdb. |
| `CLOUD_DOG__CONNECTORS__COUCHDB__DEFAULT_URI` | `${vault.dev.databases.couchdb.url || 'http://admin:cloud-dog-...` | Deployment dependent | `${vault.dev.databases.couchdb.url || 'http://admin:cloud-dog-...` | Endpoint or connection URL for connectors couchdb default. |
| `CLOUD_DOG__CONNECTORS__COUCHDB__TIMEOUT_SECONDS` | `30` | Optional | `30` | Timeout or duration control for connectors couchdb timeout. |
| `CLOUD_DOG__CONNECTORS__OPENSEARCH__ENABLED` | `true` | Optional | `true` | Toggle for connectors opensearch. |
| `CLOUD_DOG__CONNECTORS__OPENSEARCH__DEFAULT_URI` | `${vault.dev.databases.opensearch.url || ''}` | Deployment dependent | `${vault.dev.databases.opensearch.url || ''}` | Endpoint or connection URL for connectors opensearch default. |
| `CLOUD_DOG__CONNECTORS__OPENSEARCH__TIMEOUT_SECONDS` | `30` | Optional | `30` | Timeout or duration control for connectors opensearch timeout. |
| `CLOUD_DOG__CONNECTORS__ELASTICSEARCH__ENABLED` | `true` | Optional | `true` | Toggle for connectors elasticsearch. |
| `CLOUD_DOG__CONNECTORS__ELASTICSEARCH__DEFAULT_URI` | `${vault.dev.databases.elasticsearch.url || ''}` | Deployment dependent | `${vault.dev.databases.elasticsearch.url || ''}` | Endpoint or connection URL for connectors elasticsearch default. |
| `CLOUD_DOG__CONNECTORS__ELASTICSEARCH__TIMEOUT_SECONDS` | `30` | Optional | `30` | Timeout or duration control for connectors elasticsearch timeout. |
| `CLOUD_DOG__CONNECTORS__CASSANDRA__ENABLED` | `true` | Optional | `true` | Toggle for connectors cassandra. |
| `CLOUD_DOG__CONNECTORS__CASSANDRA__DEFAULT_HOST` | `${vault.dev.databases.providers.cassandra.host || ''}` | Optional | `${vault.dev.databases.providers.cassandra.host || ''}` | Host binding or upstream host for connectors cassandra default. |
| `CLOUD_DOG__CONNECTORS__CASSANDRA__DEFAULT_PORT` | `9042` | Optional | `9042` | Port for connectors cassandra default connections. |
| `CLOUD_DOG__CONNECTORS__CASSANDRA__TIMEOUT_SECONDS` | `30` | Optional | `30` | Timeout or duration control for connectors cassandra timeout. |

## `environment`

| Variable | Default | Required | Example | Description |
|----------|---------|----------|---------|-------------|
| `CLOUD_DOG__ENVIRONMENT` | `${CLOUD_DOG_ENVIRONMENT || 'dev'}` | Optional | `${CLOUD_DOG_ENVIRONMENT || 'dev'}` | Configuration value for environment. |

## `jobs`

| Variable | Default | Required | Example | Description |
|----------|---------|----------|---------|-------------|
| `CLOUD_DOG__JOBS__BACKEND` | `memory` | Optional | `memory` | Configuration value for jobs backend. |
| `CLOUD_DOG__JOBS__PAYLOAD_MAX_BYTES` | `16384` | Optional | `16384` | Configuration value for jobs payload max bytes. |

## `log`

| Variable | Default | Required | Example | Description |
|----------|---------|----------|---------|-------------|
| `CLOUD_DOG__LOG__LEVEL` | `INFO` | Optional | `INFO` | Configuration value for log level. |
| `CLOUD_DOG__LOG__FORMAT` | `json` | Optional | `json` | Configuration value for log format. |
| `CLOUD_DOG__LOG__CONSOLE` | `true` | Optional | `true` | Configuration value for log console. |
| `CLOUD_DOG__LOG__PII_REDACTION` | `true` | Optional | `true` | Configuration value for log pii redaction. |
| `CLOUD_DOG__LOG__SERVICE_INSTANCE` | `${HOSTNAME || 'db-mcp-local'}` | Optional | `${HOSTNAME || 'db-mcp-local'}` | Configuration value for log service instance. |
| `CLOUD_DOG__LOG__ENVIRONMENT` | `${CLOUD_DOG_ENVIRONMENT || 'dev'}` | Optional | `${CLOUD_DOG_ENVIRONMENT || 'dev'}` | Configuration value for log environment. |
| `CLOUD_DOG__LOG__APP_LOG` | `logs/app.log.jsonl` | Optional | `logs/app.log.jsonl` | Configuration value for log app log. |
| `CLOUD_DOG__LOG__AUDIT_LOG` | `logs/audit.log.jsonl` | Optional | `logs/audit.log.jsonl` | Configuration value for log audit log. |
| `CLOUD_DOG__LOG__INTEGRITY__ENABLED` | `false` | Optional | `false` | Toggle for log integrity. |

## `mcp_server`

| Variable | Default | Required | Example | Description |
|----------|---------|----------|---------|-------------|
| `CLOUD_DOG__MCP_SERVER__ENABLED` | `true` | Optional | `true` | Toggle for mcp server. |
| `CLOUD_DOG__MCP_SERVER__HOST` | `0.0.0.0` | Optional | `0.0.0.0` | Host binding or upstream host for mcp server. |
| `CLOUD_DOG__MCP_SERVER__PORT` | `8088` | Optional | `8088` | Port for mcp server connections. |
| `CLOUD_DOG__MCP_SERVER__TRANSPORT_MODES` | `["streamable_http", "http_jsonrpc", "legacy_sse"]` | Optional | `<set as needed>` | Configuration value for mcp server transport modes. |

## `metadata_store`

| Variable | Default | Required | Example | Description |
|----------|---------|----------|---------|-------------|
| `CLOUD_DOG__METADATA_STORE__URI` | `${vault.dev.databases.dbmcp_metadata_postgresql.uri || 'sqlit...` | Deployment dependent | `https://service.example.com` | Endpoint or connection URL for metadata store. |

## `runtime`

| Variable | Default | Required | Example | Description |
|----------|---------|----------|---------|-------------|
| `CLOUD_DOG__RUNTIME__HEALTH_EXEMPT_PATHS` | `["/health", "/ready", "/live", "/status", "/docs", "/redoc", "/openapi.json"]` | Optional | `<set as needed>` | Configuration value for runtime health exempt paths. |

## `search`

| Variable | Default | Required | Example | Description |
|----------|---------|----------|---------|-------------|
| `CLOUD_DOG__SEARCH__ENABLED` | `true` | Optional | `true` | Toggle for search. |
| `CLOUD_DOG__SEARCH__DISCOVERY_INDEX_PATH` | `./data/discovery-index.db` | Optional | `./data/discovery-index.db` | Configuration value for search discovery index path. |
| `CLOUD_DOG__SEARCH__METADATA_LIMIT` | `20` | Optional | `20` | Configuration value for search metadata limit. |
| `CLOUD_DOG__SEARCH__CONTENT_LIMIT` | `20` | Optional | `20` | Configuration value for search content limit. |
| `CLOUD_DOG__SEARCH__MAX_DOCUMENTS_PER_ENTITY` | `10` | Optional | `10` | Configuration value for search max documents per entity. |
| `CLOUD_DOG__SEARCH__MAX_EXCERPT_CHARS` | `240` | Optional | `240` | Configuration value for search max excerpt chars. |
| `CLOUD_DOG__SEARCH__FRESHNESS_SECONDS` | `3600` | Optional | `3600` | Timeout or duration control for search freshness. |
| `CLOUD_DOG__SEARCH__INLINE_SYNC` | `true` | Optional | `true` | Configuration value for search inline sync. |

## `service_instance`

| Variable | Default | Required | Example | Description |
|----------|---------|----------|---------|-------------|
| `CLOUD_DOG__SERVICE_INSTANCE` | `${HOSTNAME || 'db-mcp-local'}` | Optional | `${HOSTNAME || 'db-mcp-local'}` | Configuration value for service instance. |

## `service_name`

| Variable | Default | Required | Example | Description |
|----------|---------|----------|---------|-------------|
| `CLOUD_DOG__SERVICE_NAME` | `db-mcp-server` | Optional | `db-mcp-server` | Configuration value for service name. |

## `web_server`

| Variable | Default | Required | Example | Description |
|----------|---------|----------|---------|-------------|
| `CLOUD_DOG__WEB_SERVER__ENABLED` | `true` | Optional | `true` | Toggle for web server. |
| `CLOUD_DOG__WEB_SERVER__HOST` | `0.0.0.0` | Optional | `0.0.0.0` | Host binding or upstream host for web server. |
| `CLOUD_DOG__WEB_SERVER__PORT` | `8087` | Optional | `8087` | Port for web server connections. |
| `CLOUD_DOG__WEB_SERVER__API_BASE_URL` | `http://127.0.0.1:8086` | Deployment dependent | `http://127.0.0.1:8086` | Credential or authentication setting for the related subsystem. |

## Vault Support

| Variable | Purpose | Example |
|----------|---------|---------|
| `VAULT_ADDR` | Vault server URL when using secret-backed config resolution. | `https://your-vault-server` |
| `VAULT_TOKEN` | Token-based authentication for Vault when applicable. | `your-vault-token` |
| `VAULT_MOUNT_POINT` | Secret mount used by your Vault deployment. | `secret` |
| `VAULT_CONFIG_PATH` | Config path holding service settings. | `services/your-service` |
