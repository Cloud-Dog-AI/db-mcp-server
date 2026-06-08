# Parameters

This reference is generated from `defaults.yaml`. Each key can be overridden by the corresponding environment variable.

## `a2a_server`

| Key | Default | Environment Override | Description |
|-----|---------|----------------------|-------------|
| `a2a_server.enabled` | `true` | `CLOUD_DOG__A2A_SERVER__ENABLED` | Toggle for a2a server. |
| `a2a_server.host` | `0.0.0.0` | `CLOUD_DOG__A2A_SERVER__HOST` | Host binding or upstream host for a2a server. |
| `a2a_server.port` | `8089` | `CLOUD_DOG__A2A_SERVER__PORT` | Port for a2a server connections. |
| `a2a_server.websocket_path` | `/a2a/ws` | `CLOUD_DOG__A2A_SERVER__WEBSOCKET_PATH` | Configuration value for a2a server websocket path. |

## `access_control`

| Key | Default | Environment Override | Description |
|-----|---------|----------------------|-------------|
| `access_control.bootstrap_admin.user_id` | `bootstrap-admin` | `CLOUD_DOG__ACCESS_CONTROL__BOOTSTRAP_ADMIN__USER_ID` | Configuration value for access control bootstrap admin user id. |
| `access_control.bootstrap_admin.username` | `bootstrap-admin` | `CLOUD_DOG__ACCESS_CONTROL__BOOTSTRAP_ADMIN__USERNAME` | Configuration value for access control bootstrap admin username. |
| `access_control.bootstrap_admin.display_name` | `Bootstrap Admin` | `CLOUD_DOG__ACCESS_CONTROL__BOOTSTRAP_ADMIN__DISPLAY_NAME` | Configuration value for access control bootstrap admin display name. |
| `access_control.bootstrap_admin.api_key_name` | `<secret>` | `CLOUD_DOG__ACCESS_CONTROL__BOOTSTRAP_ADMIN__API_KEY_NAME` | Credential or authentication setting for the related subsystem. |
| `access_control.roles.admin` | `["*"]` | `CLOUD_DOG__ACCESS_CONTROL__ROLES__ADMIN` | Configuration value for access control roles admin. |
| `access_control.roles.data_steward` | `["catalog.read", "schema.read", "schema.change", "relationship.read", "relationship.change", "content.search", "data.rea...` | `CLOUD_DOG__ACCESS_CONTROL__ROLES__DATA_STEWARD` | Configuration value for access control roles data steward. |
| `access_control.roles.developer` | `["catalog.read", "schema.read", "schema.change", "relationship.read", "content.search", "data.read", "data.create", "dat...` | `CLOUD_DOG__ACCESS_CONTROL__ROLES__DEVELOPER` | Configuration value for access control roles developer. |
| `access_control.roles.analyst` | `["catalog.read", "schema.read", "relationship.read", "content.search", "data.read"]` | `CLOUD_DOG__ACCESS_CONTROL__ROLES__ANALYST` | Configuration value for access control roles analyst. |
| `access_control.roles.auditor` | `["catalog.read", "schema.read", "relationship.read", "audit.read", "data.read"]` | `CLOUD_DOG__ACCESS_CONTROL__ROLES__AUDITOR` | Configuration value for access control roles auditor. |

## `api_server`

| Key | Default | Environment Override | Description |
|-----|---------|----------------------|-------------|
| `api_server.enabled` | `true` | `CLOUD_DOG__API_SERVER__ENABLED` | Credential or authentication setting for the related subsystem. |
| `api_server.host` | `0.0.0.0` | `CLOUD_DOG__API_SERVER__HOST` | Host binding or upstream host for api server. |
| `api_server.port` | `8086` | `CLOUD_DOG__API_SERVER__PORT` | Port for api server connections. |
| `api_server.cors_origins` | `[]` | `CLOUD_DOG__API_SERVER__CORS_ORIGINS` | Credential or authentication setting for the related subsystem. |

## `app`

| Key | Default | Environment Override | Description |
|-----|---------|----------------------|-------------|
| `app.name` | `db-mcp-server` | `CLOUD_DOG__APP__NAME` | Configuration value for app name. |
| `app.version` | `0.1.0` | `CLOUD_DOG__APP__VERSION` | Configuration value for app version. |
| `app.environment` | `${CLOUD_DOG_ENVIRONMENT || 'dev'}` | `CLOUD_DOG__APP__ENVIRONMENT` | Configuration value for app environment. |
| `app.url` | `<set per environment>` | `CLOUD_DOG__APP__URL` | Endpoint or connection URL for app. |

## `audit_store`

| Key | Default | Environment Override | Description |
|-----|---------|----------------------|-------------|
| `audit_store.uri` | `""` (set per deployment, e.g. `sqlite:///./data/dbmcp_audit.db`) | `CLOUD_DOG__AUDIT_STORE__URI` | Endpoint or connection URL for audit store. |

## `auth`

| Key | Default | Environment Override | Description |
|-----|---------|----------------------|-------------|
| `auth.mode` | `api_key_only` | `CLOUD_DOG__AUTH__MODE` | Configuration value for auth mode. |
| `auth.api_key` | `<secret>` | `CLOUD_DOG__AUTH__API_KEY` | Credential or authentication setting for the related subsystem. |
| `auth.default_role` | `admin` | `CLOUD_DOG__AUTH__DEFAULT_ROLE` | Configuration value for auth default role. |
| `auth.jwt_secret` | `<secret>` | `CLOUD_DOG__AUTH__JWT_SECRET` | Credential or authentication setting for the related subsystem. |

## `connectors`

| Key | Default | Environment Override | Description |
|-----|---------|----------------------|-------------|
| `connectors.mongodb.enabled` | `true` | `CLOUD_DOG__CONNECTORS__MONGODB__ENABLED` | Toggle for connectors mongodb. |
| `connectors.mongodb.default_uri` | `""` (e.g. `mongodb://<user>:<password>@mongo.example.com:27017/<db>`) | `CLOUD_DOG__CONNECTORS__MONGODB__DEFAULT_URI` | Endpoint or connection URL for connectors mongodb default. |
| `connectors.mongodb.timeout_ms` | `30000` | `CLOUD_DOG__CONNECTORS__MONGODB__TIMEOUT_MS` | Configuration value for connectors mongodb timeout ms. |
| `connectors.couchdb.enabled` | `true` | `CLOUD_DOG__CONNECTORS__COUCHDB__ENABLED` | Toggle for connectors couchdb. |
| `connectors.couchdb.default_uri` | `""` (e.g. `http://<user>:<password>@couchdb.example.com:5984/`) | `CLOUD_DOG__CONNECTORS__COUCHDB__DEFAULT_URI` | Endpoint or connection URL for connectors couchdb default. |
| `connectors.couchdb.timeout_seconds` | `30` | `CLOUD_DOG__CONNECTORS__COUCHDB__TIMEOUT_SECONDS` | Timeout or duration control for connectors couchdb timeout. |
| `connectors.opensearch.enabled` | `true` | `CLOUD_DOG__CONNECTORS__OPENSEARCH__ENABLED` | Toggle for connectors opensearch. |
| `connectors.opensearch.default_uri` | `""` (e.g. `https://opensearch.example.com:9200`) | `CLOUD_DOG__CONNECTORS__OPENSEARCH__DEFAULT_URI` | Endpoint or connection URL for connectors opensearch default. |
| `connectors.opensearch.timeout_seconds` | `30` | `CLOUD_DOG__CONNECTORS__OPENSEARCH__TIMEOUT_SECONDS` | Timeout or duration control for connectors opensearch timeout. |
| `connectors.elasticsearch.enabled` | `true` | `CLOUD_DOG__CONNECTORS__ELASTICSEARCH__ENABLED` | Toggle for connectors elasticsearch. |
| `connectors.elasticsearch.default_uri` | `""` (e.g. `https://elasticsearch.example.com:9200`) | `CLOUD_DOG__CONNECTORS__ELASTICSEARCH__DEFAULT_URI` | Endpoint or connection URL for connectors elasticsearch default. |
| `connectors.elasticsearch.timeout_seconds` | `30` | `CLOUD_DOG__CONNECTORS__ELASTICSEARCH__TIMEOUT_SECONDS` | Timeout or duration control for connectors elasticsearch timeout. |
| `connectors.cassandra.enabled` | `true` | `CLOUD_DOG__CONNECTORS__CASSANDRA__ENABLED` | Toggle for connectors cassandra. |
| `connectors.cassandra.default_host` | `""` (e.g. `cassandra.example.com`) | `CLOUD_DOG__CONNECTORS__CASSANDRA__DEFAULT_HOST` | Host binding or upstream host for connectors cassandra default. |
| `connectors.cassandra.default_port` | `9042` | `CLOUD_DOG__CONNECTORS__CASSANDRA__DEFAULT_PORT` | Port for connectors cassandra default connections. |
| `connectors.cassandra.timeout_seconds` | `30` | `CLOUD_DOG__CONNECTORS__CASSANDRA__TIMEOUT_SECONDS` | Timeout or duration control for connectors cassandra timeout. |

## `environment`

| Key | Default | Environment Override | Description |
|-----|---------|----------------------|-------------|
| `environment` | `${CLOUD_DOG_ENVIRONMENT || 'dev'}` | `CLOUD_DOG__ENVIRONMENT` | Configuration value for environment. |

## `jobs`

| Key | Default | Environment Override | Description |
|-----|---------|----------------------|-------------|
| `jobs.backend` | `memory` | `CLOUD_DOG__JOBS__BACKEND` | Configuration value for jobs backend. |
| `jobs.payload_max_bytes` | `16384` | `CLOUD_DOG__JOBS__PAYLOAD_MAX_BYTES` | Configuration value for jobs payload max bytes. |

## `log`

| Key | Default | Environment Override | Description |
|-----|---------|----------------------|-------------|
| `log.level` | `INFO` | `CLOUD_DOG__LOG__LEVEL` | Configuration value for log level. |
| `log.format` | `json` | `CLOUD_DOG__LOG__FORMAT` | Configuration value for log format. |
| `log.console` | `true` | `CLOUD_DOG__LOG__CONSOLE` | Configuration value for log console. |
| `log.pii_redaction` | `true` | `CLOUD_DOG__LOG__PII_REDACTION` | Configuration value for log pii redaction. |
| `log.service_instance` | `${HOSTNAME || 'db-mcp-local'}` | `CLOUD_DOG__LOG__SERVICE_INSTANCE` | Configuration value for log service instance. |
| `log.environment` | `${CLOUD_DOG_ENVIRONMENT || 'dev'}` | `CLOUD_DOG__LOG__ENVIRONMENT` | Configuration value for log environment. |
| `log.app_log` | `logs/app.log.jsonl` | `CLOUD_DOG__LOG__APP_LOG` | Configuration value for log app log. |
| `log.audit_log` | `logs/audit.log.jsonl` | `CLOUD_DOG__LOG__AUDIT_LOG` | Configuration value for log audit log. |
| `log.integrity.enabled` | `false` | `CLOUD_DOG__LOG__INTEGRITY__ENABLED` | Toggle for log integrity. |

## `mcp_server`

| Key | Default | Environment Override | Description |
|-----|---------|----------------------|-------------|
| `mcp_server.enabled` | `true` | `CLOUD_DOG__MCP_SERVER__ENABLED` | Toggle for mcp server. |
| `mcp_server.host` | `0.0.0.0` | `CLOUD_DOG__MCP_SERVER__HOST` | Host binding or upstream host for mcp server. |
| `mcp_server.port` | `8088` | `CLOUD_DOG__MCP_SERVER__PORT` | Port for mcp server connections. |
| `mcp_server.transport_modes` | `["streamable_http", "http_jsonrpc", "legacy_sse"]` | `CLOUD_DOG__MCP_SERVER__TRANSPORT_MODES` | Configuration value for mcp server transport modes. |

## `metadata_store`

| Key | Default | Environment Override | Description |
|-----|---------|----------------------|-------------|
| `metadata_store.uri` | `sqlite:///./data/dbmcp_webui_metadata.db` | `CLOUD_DOG__METADATA_STORE__URI` | Endpoint or connection URL for metadata store. |

## `runtime`

| Key | Default | Environment Override | Description |
|-----|---------|----------------------|-------------|
| `runtime.health_exempt_paths` | `["/health", "/ready", "/live", "/status", "/docs", "/redoc", "/openapi.json"]` | `CLOUD_DOG__RUNTIME__HEALTH_EXEMPT_PATHS` | Configuration value for runtime health exempt paths. |

## `search`

| Key | Default | Environment Override | Description |
|-----|---------|----------------------|-------------|
| `search.enabled` | `true` | `CLOUD_DOG__SEARCH__ENABLED` | Toggle for search. |
| `search.discovery_index_path` | `./data/discovery-index.db` | `CLOUD_DOG__SEARCH__DISCOVERY_INDEX_PATH` | Configuration value for search discovery index path. |
| `search.metadata_limit` | `20` | `CLOUD_DOG__SEARCH__METADATA_LIMIT` | Configuration value for search metadata limit. |
| `search.content_limit` | `20` | `CLOUD_DOG__SEARCH__CONTENT_LIMIT` | Configuration value for search content limit. |
| `search.max_documents_per_entity` | `10` | `CLOUD_DOG__SEARCH__MAX_DOCUMENTS_PER_ENTITY` | Configuration value for search max documents per entity. |
| `search.max_excerpt_chars` | `240` | `CLOUD_DOG__SEARCH__MAX_EXCERPT_CHARS` | Configuration value for search max excerpt chars. |
| `search.freshness_seconds` | `3600` | `CLOUD_DOG__SEARCH__FRESHNESS_SECONDS` | Timeout or duration control for search freshness. |
| `search.inline_sync` | `true` | `CLOUD_DOG__SEARCH__INLINE_SYNC` | Configuration value for search inline sync. |

## `service_instance`

| Key | Default | Environment Override | Description |
|-----|---------|----------------------|-------------|
| `service_instance` | `${HOSTNAME || 'db-mcp-local'}` | `CLOUD_DOG__SERVICE_INSTANCE` | Configuration value for service instance. |

## `service_name`

| Key | Default | Environment Override | Description |
|-----|---------|----------------------|-------------|
| `service_name` | `db-mcp-server` | `CLOUD_DOG__SERVICE_NAME` | Configuration value for service name. |

## `web_server`

| Key | Default | Environment Override | Description |
|-----|---------|----------------------|-------------|
| `web_server.enabled` | `true` | `CLOUD_DOG__WEB_SERVER__ENABLED` | Toggle for web server. |
| `web_server.host` | `0.0.0.0` | `CLOUD_DOG__WEB_SERVER__HOST` | Host binding or upstream host for web server. |
| `web_server.port` | `8087` | `CLOUD_DOG__WEB_SERVER__PORT` | Port for web server connections. |
| `web_server.api_base_url` | `http://127.0.0.1:8086` | `CLOUD_DOG__WEB_SERVER__API_BASE_URL` | Credential or authentication setting for the related subsystem. |
