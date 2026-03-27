# API Documentation

## Base URLs

| Surface | Default Port | Local URL |
|---------|-------------|-----------|
| API Server | 8086 | `http://localhost:8086` |
| Web Server | 8087 | `http://localhost:8087` |
| MCP Server | 8088 | `http://localhost:8088` |
| A2A Server | 8089 | `http://localhost:8089` |

Deployed: `https://dbmcp.your-domain.com`

## Authentication

- **Cookie session:** `POST /auth/login` with `{"username": "...", "password": "..."}`
- **API Key:** `X-API-Key: <your-api-key>` or `Authorization: Bearer <your-api-key>`

Exempt paths (no auth required): `/health`, `/ready`, `/live`, `/status`, `/docs`, `/redoc`, `/openapi.json`

## Endpoints

### Health

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | /health | No | Service health check (metadata DB, audit DB, jobs) |
| GET | /ready | No | Readiness probe |
| GET | /live | No | Liveness probe |
| GET | /status | No | Extended status |

### Auth (Web Server)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | /auth/login | No | Login with username/password |
| GET | /auth/me | Session | Current authenticated user |
| POST | /auth/logout | Session | Destroy session |

### API Server (port 8086)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | /api/v1/ping | API Key | Authenticated runtime summary |
| GET | /api/v1/jobs/health | API Key | Job queue health and counters |

### Access Control - Profiles

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | /api/v1/profiles | API Key | List all profiles |
| POST | /api/v1/profiles | API Key | Create a profile |
| GET | /api/v1/profiles/{profile_id} | API Key | Get a profile |
| PUT | /api/v1/profiles/{profile_id} | API Key | Update a profile |
| DELETE | /api/v1/profiles/{profile_id} | API Key | Delete a profile |
| POST | /api/v1/profiles/{profile_id}/mask-preview | API Key | Preview data masking for a profile |
| GET | /api/v1/profiles/{profile_id}/authorise/{permission} | API Key | Check profile authorisation |

### Access Control - Users

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | /api/v1/users | API Key | List all users |
| POST | /api/v1/users | API Key | Create a user |
| GET | /api/v1/users/{user_id} | API Key | Get a user |
| PUT | /api/v1/users/{user_id} | API Key | Update a user |
| DELETE | /api/v1/users/{user_id} | API Key | Delete a user |

### Access Control - Groups

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | /api/v1/groups | API Key | List all groups |
| POST | /api/v1/groups | API Key | Create a group |
| GET | /api/v1/groups/{group_id} | API Key | Get a group |
| PUT | /api/v1/groups/{group_id} | API Key | Update a group |
| DELETE | /api/v1/groups/{group_id} | API Key | Delete a group |

### Access Control - API Keys

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | /api/v1/api-keys | API Key | List all API keys |
| POST | /api/v1/api-keys | API Key | Create an API key |
| POST | /api/v1/api-keys/{api_key_id}/revoke | API Key | Revoke an API key |

### MCP Server (port 8088)

The MCP server registers tools via the standard MCP contract. Transport modes: `streamable_http`, `http_jsonrpc`, `legacy_sse`.

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | / | API Key | MCP server metadata and tool list |
| POST | /mcp | API Key | Streamable HTTP MCP endpoint |
| GET | /mcp/tools | API Key | List MCP tools |
| POST | /mcp/tools/{tool_name} | API Key | Call an MCP tool |

### MCP Tools (via MCP protocol)

#### Catalog

| Tool | Description |
|------|-------------|
| catalog_list_databases | List connected databases |
| catalog_describe_database | Describe a database |

#### Schema

| Tool | Description |
|------|-------------|
| schema_list_collections | List collections/tables |
| schema_describe_collection | Describe a collection |
| schema_change_apply | Apply a schema change |

#### Content

| Tool | Description |
|------|-------------|
| content_read | Read documents/rows |
| content_create | Create documents/rows |
| content_update | Update documents/rows |
| content_delete | Delete documents/rows |
| content_search | Full-text search |

#### Relationships

| Tool | Description |
|------|-------------|
| relationship_list | List relationships |
| relationship_create | Create a relationship |
| relationship_delete | Delete a relationship |

#### Audit

| Tool | Description |
|------|-------------|
| audit_list_events | List audit events |

#### Search

| Tool | Description |
|------|-------------|
| search_discovery | Cross-database discovery search |

#### Access Control (via MCP)

| Tool | Description |
|------|-------------|
| access_control_list_profiles | List profiles |
| access_control_create_profile | Create a profile |

### A2A Server (port 8089)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | / | API Key | A2A metadata (status, websocket path) |
| WS | /a2a/ws | API Key | WebSocket (health topic, echo) |

### Web Server Proxy (port 8087)

The web server proxies API and MCP requests to their respective backends and serves the SPA.

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| ALL | /api/* | Session | Proxy to API server |
| ALL | /mcp/* | Session | Proxy to MCP server |
| GET | / | No | SPA entrypoint |
| GET | /runtime-config.js | No | SPA runtime config |
| GET | /{path} | No | SPA client-side routing fallback |
