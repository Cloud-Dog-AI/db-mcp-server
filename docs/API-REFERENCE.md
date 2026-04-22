# db-mcp-server — API Reference

**Generated from source:** 2026-04-21 | **Surfaces:** API (8086), Web (8087), MCP (8088), A2A (8089)

---

## 1. REST API Server (port 8086)

### 1.1 Health Endpoints (unauthenticated)

| Method | Path | Description | Reqs |
|--------|------|-------------|------|
| GET | `/health` | Health check with sub-checks (metadata_store, audit_store, jobs, search) | CR-02 |
| GET | `/ready` | Readiness probe | CR-02 |
| GET | `/live` | Liveness probe | CR-02 |
| GET | `/status` | Status summary | CR-02 |

Source: `src/common/runtime.py` via `build_health_router` / `create_health_router`
Tests: ST1.1

### 1.2 Operational Endpoints (prefix `/api/v1`, API-key authenticated)

| Method | Path | Description | Reqs | Tests |
|--------|------|-------------|------|-------|
| GET | `/api/v1/ping` | Authenticated runtime summary | CR-02 | ST1.1 |
| GET | `/api/v1/jobs/status` | Queue status counters | NF-02 | ST1.1 |
| GET | `/api/v1/metrics` | Resource metrics (uptime, memory, CPU, disk) | NF-02 | ST1.1 |
| GET | `/api/v1/config` | Effective runtime config (secrets masked) | CFG-01 | ST1.1 |
| GET | `/api/v1/logs` | Parsed JSON log entries. Params: `surface`, `limit` | AC-02 | ST1.1 |
| GET | `/api/v1/jobs` | List recent platform jobs. Params: `limit`, `job_type` | NF-02 | ST1.1 |
| GET | `/api/v1/jobs/{job_id}` | Get single platform job | NF-02 | ST1.1 |
| POST | `/api/v1/jobs/{job_id}/cancel` | Cancel a running/queued job | NF-02 | ST1.1 |

Source: `src/servers/api/app.py`

### 1.3 Access Control Endpoints (prefix `/api/v1`, API-key + RBAC)

#### Profiles

| Method | Path | Auth | Reqs | Tests |
|--------|------|------|------|-------|
| GET | `/api/v1/profiles` | `profile.manage` | AC-01, CFG-01 | ST1.2, IT1.1 |
| POST | `/api/v1/profiles` | `profile.manage` | AC-01, CFG-01 | ST1.2, IT1.1 |
| GET | `/api/v1/profiles/{profile_id}` | `profile.manage` | AC-01 | ST1.2, IT1.1 |
| PUT | `/api/v1/profiles/{profile_id}` | `profile.manage` | AC-01, CFG-01 | ST1.2, IT1.1 |
| DELETE | `/api/v1/profiles/{profile_id}` | `profile.manage` | AC-01 | ST1.2, IT1.1 |
| POST | `/api/v1/profiles/{profile_id}/mask-preview` | `data.read` | AC-03, CO-04 | ST1.2 |
| GET | `/api/v1/profiles/{profile_id}/authorise/{permission}` | RBAC | AC-01, AC-04 | ST1.2 |

#### Users, Groups, API Keys

| Method | Path | Auth | Reqs | Tests |
|--------|------|------|------|-------|
| GET | `/api/v1/users` | admin | AC-05 | ST1.2, IT1.1 |
| POST | `/api/v1/users` | admin | AC-05 | ST1.2, IT1.1 |
| GET | `/api/v1/users/{user_id}` | admin | AC-05 | ST1.2, IT1.1 |
| PUT | `/api/v1/users/{user_id}` | admin | AC-05 | ST1.2, IT1.1 |
| DELETE | `/api/v1/users/{user_id}` | admin | AC-05 | ST1.2, IT1.1 |
| GET | `/api/v1/groups` | admin | AC-06 | ST1.2, IT1.1 |
| POST | `/api/v1/groups` | admin | AC-06 | ST1.2, IT1.1 |
| GET | `/api/v1/groups/{group_id}` | admin | AC-06 | ST1.2, IT1.1 |
| PUT | `/api/v1/groups/{group_id}` | admin | AC-06 | ST1.2, IT1.1 |
| DELETE | `/api/v1/groups/{group_id}` | admin | AC-06 | ST1.2, IT1.1 |
| GET | `/api/v1/api-keys` | admin | AC-06 | ST1.2, IT1.1 |
| POST | `/api/v1/api-keys` | admin | AC-06 | ST1.2, IT1.1 |
| POST | `/api/v1/api-keys/{api_key_id}/revoke` | admin | AC-06 | ST1.2, IT1.1 |

Source: `src/servers/api/access_control.py`

**API total: 35 endpoints** (4 health + 8 operational + 20 access-control + 3 auto-generated docs)

---

## 2. MCP Server (port 8088)

### 2.1 MCP Protocol Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/mcp` | Streamable HTTP — MCP JSON-RPC 2.0 (`tools/list`, `tools/call`) |
| GET | `/` | MCP root — returns status + registered tool names |
| GET | `/health` | Health check |

### 2.2 MCP Tools (45 registered)

#### Access Control (12 tools) — Reqs: AC-01, AC-02, CFG-01 — Tests: IT1.1

| Tool | Description | RBAC |
|------|-------------|------|
| `profiles.list` | List connection profiles | `db:profile:read` |
| `profiles.create` | Create a profile | `db:admin:*` |
| `profiles.get` | Get profile by ID | `db:profile:read` |
| `profiles.update` | Update a profile | `db:admin:*` |
| `profiles.delete` | Delete a profile | `db:admin:*` |
| `users.list` | List users | `db:admin:*` |
| `users.create` | Create a user | `db:admin:*` |
| `groups.list` | List groups | `db:admin:*` |
| `groups.create` | Create a group | `db:admin:*` |
| `api_keys.list` | List API keys | `db:admin:*` |
| `api_keys.create` | Create an API key | `db:admin:*` |
| `api_keys.revoke` | Revoke an API key | `db:admin:*` |

#### Catalog (4 tools) — Reqs: CD-01, CD-02, CD-03, CN-01 — Tests: UT1.6, ST1.4, IT1.3

| Tool | Description | RBAC |
|------|-------------|------|
| `catalog.list_namespaces` | List namespaces for a profile | `db:catalog:read` |
| `catalog.list_entities` | List entities in a namespace | `db:catalog:read` |
| `catalog.get_entity` | Describe entity detail | `db:catalog:read` |
| `catalog.search` | Search entity/field names | `db:catalog:read` |

#### Schema (7 tools) — Reqs: SC-01, SC-02, CN-01 — Tests: ST1.6, IT1.3

| Tool | Description | RBAC |
|------|-------------|------|
| `schema.describe_entity` | Entity schema | `db:schema:read` |
| `schema.describe_fields` | Per-field schema | `db:schema:read` |
| `schema.list_indexes` | Entity indexes | `db:schema:read` |
| `schema.sample_shapes` | Sample document shapes | `db:schema:read` |
| `schema.change.plan` | Dry-run schema change | `db:schema:read` |
| `schema.change.apply` | Apply schema change | `db:schema:migrate` |
| `schema.change.history` | Schema change audit trail | `db:schema:read` |

#### Content (6 tools) — Reqs: CO-01, CO-02, CO-05, CO-06, NF-01, CN-01 — Tests: UT1.7, ST1.5, IT1.4

| Tool | Description | RBAC |
|------|-------------|------|
| `data.read` | Read content with structured filter | `db:data:read` |
| `data.create` | Insert records | `db:data:write` |
| `data.update` | Update filtered records | `db:data:write` |
| `data.delete` | Delete filtered records | `db:data:delete` |
| `data.count` | Count matching records | `db:data:read` |
| `data.exists` | Check existence | `db:data:read` |

#### Relationship (6 tools) — Reqs: RL-01, RL-02, RL-03 — Tests: UT1.8, IT1.5

| Tool | Description | RBAC |
|------|-------------|------|
| `relationship.list` | List relationships for entity | `db:relationship:read` |
| `relationship.get` | Get relationship by ID | `db:relationship:read` |
| `relationship.infer` | Infer candidates from data | `db:relationship:write` |
| `relationship.create` | Create relationship | `db:relationship:write` |
| `relationship.update` | Update relationship | `db:relationship:write` |
| `relationship.delete` | Delete relationship | `db:relationship:delete` |

#### Audit (2 tools) — Reqs: AC-02, NF-01 — Tests: IT1.3

| Tool | Description | RBAC |
|------|-------------|------|
| `audit.list_events` | List audit events | `db:audit:read` |
| `audit.get_event` | Get event detail | `db:audit:read` |

#### Search & Index (8 tools) — Reqs: SI-01, SI-02, SI-03, SI-04 — Tests: ST1.7, IT1.6

| Tool | Description | RBAC |
|------|-------------|------|
| `search.metadata` | Search metadata (entities, fields, namespaces) | `db:search:read` |
| `search.content` | Search indexed content | `db:search:read` |
| `search.related` | Find related entities | `db:search:read` |
| `search.explain_match` | Explain search match | `db:search:read` |
| `index.status` | Index freshness/coverage | `db:index:read` |
| `index.sync_profile` | Refresh profile index | `db:index:write` |
| `index.sync_entity` | Refresh entity index | `db:index:write` |
| `index.rebuild` | Full index rebuild | `db:index:write` |

Source: `src/servers/mcp/` (7 tool registries)

---

## 3. A2A Server (port 8089)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/.well-known/agent.json` | A2A agent card | No |
| POST | `/tasks` | A2A task submission | No (exempt) |
| POST | `/a2a/tasks` | A2A task (prefixed alias) | No (exempt) |
| WS | `/a2a/ws` | WebSocket (health + echo) | API key |
| WS | `/ws` | WebSocket alias | API key |
| GET | `/health` | Health check | No |

### A2A Skills (4)

| Skill | Description | Backed by |
|-------|-------------|-----------|
| `data_create` | Create records | `data.create` |
| `data_query` | Query data | `data.read` |
| `data_update` | Update records | `data.update` |
| `schema_list` | List schemas | `catalog.list_namespaces` |

Source: `src/servers/a2a/app.py`

---

## 4. Web Server (port 8087)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/auth/login` | Session login | Credentials |
| GET | `/auth/me` | Current user | Session |
| POST | `/auth/logout` | Destroy session | Session |
| GET | `/runtime-config.js` | SPA config | No |
| GET | `/` | SPA entrypoint (DashboardPage) | No |
| GET | `/{path:path}` | SPA catchall | No |

### Web Proxy Routes (session-authenticated, injects API key)

| Pattern | Target |
|---------|--------|
| `/api/*`, `/webapi/*` | API server (8086) |
| `/mcp/*`, `/webmcp/*` | MCP server (8088) |
| `/weba2a/*` | A2A server (8089) |

Source: `src/servers/web/app.py`

---

## Example Requests

### Health check
```bash
curl -sf https://<host>/health
```

### List profiles (authenticated)
```bash
curl -H "X-API-Key: <api-key>" https://<host>/api/v1/profiles
```

### MCP tool call (data.read)
```bash
curl -X POST https://<host>:8088/mcp \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <api-key>" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"data.read","arguments":{"profile_id":"<id>","namespace":"public","entity":"users","filter":{"limit":10}}}}'
```

---

## Cross-References

- Requirements: [REQUIREMENTS.md](REQUIREMENTS.md) — CR-01..CR-03, CD-01..CD-04, SC-01..SC-04, CO-01..CO-06, SI-01..SI-04, RL-01..RL-03, AC-01..AC-06, CFG-01..CFG-03, NF-01..NF-04
- Tests: [TESTS.md](TESTS.md) — QT1.1, UT1.1-1.19, ST1.1-1.15, IT1.1-1.9, AT_WEBUI_E2E
- Standards: PS-20 (API), PS-71 (IDAM), PS-72 (MCP/A2A), PS-77 (WebUI)
