---
template-id: T-MCP
template-version: 1.0
applies-to: docs/MCP-REFERENCE.md
registry: service
required: must-have
when-applicable: ""
template-last-updated: 2026-06-12
template-owner: platform-standards

project: db-mcp-server
doc-last-updated: 2026-06-18T00:00:00Z
doc-git-commit: 58fb399bb2ba144e262f97293103a7a0a19ba05d
doc-git-branch: main
doc-source-shas: []
doc-age-policy: 90d
doc-conformance-stamp: 2026-06-18T00:00:00Z
---

# db-mcp-server — MCP-REFERENCE

> **Template version:** T-MCP v1.0 — MCP tool surface (JSON-RPC 2.0 at `/mcp`).

## 1. Auth model

MCP auth mode: `api_key` (default). All tool calls must supply a valid API key via `X-API-Key` header or `Authorization: Bearer <key>`.

RBAC is resolved per-tool. Each tool declares a required IDAM permission (e.g. `db:catalog:read`, `db:data:write`, `db:admin:*`). The platform `RBACEngine` (cloud_dog_idam) evaluates whether the API key's roles satisfy that permission. Roles map to permissions as follows:

| Role | Permission scope |
|------|-----------------|
| admin | `db:admin:*` (all tools) |
| read-write | `db:data:write`, `db:data:delete`, `db:catalog:read`, `db:schema:read`, `db:search:read`, `db:index:write`, `db:relationship:write`, `db:profile:read`, `db:audit:read` |
| read-only | `db:data:read`, `db:catalog:read`, `db:schema:read`, `db:search:read`, `db:index:read`, `db:relationship:read`, `db:profile:read`, `db:audit:read` |

Health endpoints (`/health`, `/ready`, `/live`) are unauthenticated.

Source: `src/servers/mcp/app.py`, `src/servers/mcp/tool_rbac_audit.py`

---

## 2. Tools

**45 registered tools** across 7 registries. All tools share the same JSON-RPC 2.0 envelope at `/mcp`. Each tool call wraps its arguments in a `ToolContract` and emits a full NIST AU-3 audit event (actor/ip/roles/target/outcome/duration).

### 2.1 `profiles.list`
- **Description:** List all access profiles (connection configurations).
- **RBAC:** `db:profile:read` — admin, read-write, read-only
- **Input schema:**
  ```json
  { "type": "object", "properties": {} }
  ```
- **Output schema:**
  ```json
  { "type": "object", "properties": { "items": { "type": "array" } } }
  ```
- **Errors:** `401 Unauthorized` (missing/invalid key), `403 Forbidden` (insufficient role)
- **Example call:**
  ```bash
  curl -X POST https://<host>/mcp \
    -H "Content-Type: application/json" \
    -H "X-API-Key: ${API_KEY}" \
    -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"profiles.list","arguments":{}},"id":1}'
  ```

### 2.2 `profiles.create`
- **Description:** Create an access profile (connection configuration with RBAC scope).
- **RBAC:** `db:admin:*` — admin only
- **Input schema:**
  ```json
  { "type": "object", "properties": { "name": { "type": "string" }, "connector": { "type": "string" }, "connection": { "type": "object" } }, "required": ["name", "connector"] }
  ```
- **Output schema:**
  ```json
  { "type": "object", "properties": { "profile_id": { "type": "string" }, "name": { "type": "string" } } }
  ```
- **Errors:** `401`, `403`, `422` (validation)

### 2.3 `profiles.get`
- **Description:** Get a single profile by ID.
- **RBAC:** `db:profile:read` — admin, read-write, read-only
- **Input schema:**
  ```json
  { "type": "object", "properties": { "profile_id": { "type": "string" } }, "required": ["profile_id"] }
  ```
- **Output schema:**
  ```json
  { "type": "object", "properties": { "profile_id": { "type": "string" }, "name": { "type": "string" }, "connector": { "type": "string" } } }
  ```
- **Errors:** `401`, `403`, `404` (profile not found)

### 2.4 `profiles.update`
- **Description:** Update a profile's connection configuration or RBAC scope.
- **RBAC:** `db:admin:*` — admin only
- **Input schema:**
  ```json
  { "type": "object", "properties": { "profile_id": { "type": "string" } }, "required": ["profile_id"] }
  ```
- **Output schema:**
  ```json
  { "type": "object", "properties": { "profile_id": { "type": "string" }, "updated": { "type": "boolean" } } }
  ```
- **Errors:** `401`, `403`, `404`

### 2.5 `profiles.delete`
- **Description:** Delete a profile.
- **RBAC:** `db:admin:*` — admin only
- **Input schema:**
  ```json
  { "type": "object", "properties": { "profile_id": { "type": "string" } }, "required": ["profile_id"] }
  ```
- **Output schema:**
  ```json
  { "type": "object", "properties": { "deleted": { "type": "boolean" }, "profile_id": { "type": "string" } } }
  ```
- **Errors:** `401`, `403`, `404`

### 2.6 `users.list`
- **Description:** List all IDAM users registered in the service.
- **RBAC:** `db:admin:*` — admin only
- **Input schema:**
  ```json
  { "type": "object", "properties": {} }
  ```
- **Output schema:**
  ```json
  { "type": "object", "properties": { "items": { "type": "array" } } }
  ```
- **Errors:** `401`, `403`

### 2.7 `users.create`
- **Description:** Create a new IDAM user.
- **RBAC:** `db:admin:*` — admin only
- **Input schema:**
  ```json
  { "type": "object", "properties": { "username": { "type": "string" }, "roles": { "type": "array", "items": { "type": "string" } } }, "required": ["username"] }
  ```
- **Output schema:**
  ```json
  { "type": "object", "properties": { "user_id": { "type": "string" }, "username": { "type": "string" } } }
  ```
- **Errors:** `401`, `403`, `422`

### 2.8 `groups.list`
- **Description:** List all IDAM groups.
- **RBAC:** `db:admin:*` — admin only
- **Input schema:**
  ```json
  { "type": "object", "properties": {} }
  ```
- **Output schema:**
  ```json
  { "type": "object", "properties": { "items": { "type": "array" } } }
  ```
- **Errors:** `401`, `403`

### 2.9 `groups.create`
- **Description:** Create a new IDAM group.
- **RBAC:** `db:admin:*` — admin only
- **Input schema:**
  ```json
  { "type": "object", "properties": { "name": { "type": "string" } }, "required": ["name"] }
  ```
- **Output schema:**
  ```json
  { "type": "object", "properties": { "group_id": { "type": "string" }, "name": { "type": "string" } } }
  ```
- **Errors:** `401`, `403`, `422`

### 2.10 `api_keys.list`
- **Description:** List API keys (optionally filtered by owner user ID).
- **RBAC:** `db:admin:*` — admin only
- **Input schema:**
  ```json
  { "type": "object", "properties": { "owner_user_id": { "type": "string" } } }
  ```
- **Output schema:**
  ```json
  { "type": "object", "properties": { "items": { "type": "array" } } }
  ```
- **Errors:** `401`, `403`

### 2.11 `api_keys.create`
- **Description:** Create a new API key for a user.
- **RBAC:** `db:admin:*` — admin only
- **Input schema:**
  ```json
  { "type": "object", "properties": { "user_id": { "type": "string" }, "name": { "type": "string" }, "roles": { "type": "array" } }, "required": ["user_id"] }
  ```
- **Output schema:**
  ```json
  { "type": "object", "properties": { "api_key_id": { "type": "string" }, "key": { "type": "string" } } }
  ```
- **Errors:** `401`, `403`, `422`

### 2.12 `api_keys.revoke`
- **Description:** Revoke an API key by ID.
- **RBAC:** `db:admin:*` — admin only
- **Input schema:**
  ```json
  { "type": "object", "properties": { "api_key_id": { "type": "string" }, "reason": { "type": "string" } }, "required": ["api_key_id"] }
  ```
- **Output schema:**
  ```json
  { "type": "object", "properties": { "revoked": { "type": "boolean" }, "api_key_id": { "type": "string" } } }
  ```
- **Errors:** `401`, `403`, `404`

### 2.13 `catalog.list_namespaces`
- **Description:** List namespaces visible to a profile (e.g. databases, keyspaces, clusters).
- **RBAC:** `db:catalog:read` — admin, read-write, read-only
- **Input schema:**
  ```json
  { "type": "object", "properties": { "profile_id": { "type": "string" } }, "required": ["profile_id"] }
  ```
- **Output schema:**
  ```json
  { "type": "object", "properties": { "items": { "type": "array", "items": { "type": "object", "properties": { "name": { "type": "string" }, "type": { "type": "string" } } } } } }
  ```
- **Errors:** `401`, `403`, `404` (profile), `503` (connector unavailable)
- **Example call:**
  ```bash
  curl -X POST https://<host>/mcp \
    -H "Content-Type: application/json" \
    -H "X-API-Key: ${API_KEY}" \
    -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"catalog.list_namespaces","arguments":{"profile_id":"my-profile"}},"id":1}'
  ```

### 2.14 `catalog.list_entities`
- **Description:** List entities visible within a namespace (e.g. tables, collections, indexes).
- **RBAC:** `db:catalog:read` — admin, read-write, read-only
- **Input schema:**
  ```json
  { "type": "object", "properties": { "profile_id": { "type": "string" }, "namespace": { "type": "string" } }, "required": ["profile_id", "namespace"] }
  ```
- **Output schema:**
  ```json
  { "type": "object", "properties": { "items": { "type": "array", "items": { "type": "object", "properties": { "name": { "type": "string" }, "type": { "type": "string" } } } } } }
  ```
- **Errors:** `401`, `403`, `404`, `503`

### 2.15 `catalog.get_entity`
- **Description:** Describe an entity in detail (field count, type metadata, field list).
- **RBAC:** `db:catalog:read` — admin, read-write, read-only
- **Input schema:**
  ```json
  { "type": "object", "properties": { "profile_id": { "type": "string" }, "namespace": { "type": "string" }, "entity": { "type": "string" } }, "required": ["profile_id", "namespace", "entity"] }
  ```
- **Output schema:**
  ```json
  { "type": "object", "properties": { "name": { "type": "string" }, "type": { "type": "string" }, "field_count": { "type": "integer" }, "fields": { "type": "array" } } }
  ```
- **Errors:** `401`, `403`, `404`, `503`

### 2.16 `catalog.search`
- **Description:** Search entity and field names within a profile (substring match on namespace/entity/field names).
- **RBAC:** `db:catalog:read` — admin, read-write, read-only
- **Input schema:**
  ```json
  { "type": "object", "properties": { "profile_id": { "type": "string" }, "query": { "type": "string" } }, "required": ["profile_id"] }
  ```
- **Output schema:**
  ```json
  { "type": "object", "properties": { "items": { "type": "array", "items": { "type": "object", "properties": { "namespace": { "type": "string" }, "entity": { "type": "string" }, "entity_type": { "type": "string" }, "matched_fields": { "type": "array" } } } } } }
  ```
- **Errors:** `401`, `403`, `404`, `503`

### 2.17 `schema.describe_entity`
- **Description:** Describe an entity schema (connector-level metadata + field list).
- **RBAC:** `db:schema:read` — admin, read-write, read-only
- **Input schema:**
  ```json
  { "type": "object", "properties": { "profile_id": { "type": "string" }, "namespace": { "type": "string" }, "entity": { "type": "string" } }, "required": ["profile_id", "namespace", "entity"] }
  ```
- **Output schema:**
  ```json
  { "type": "object", "properties": { "name": { "type": "string" }, "type": { "type": "string" }, "fields": { "type": "array" } } }
  ```
- **Errors:** `401`, `403`, `404`, `503`

### 2.18 `schema.describe_fields`
- **Description:** Describe per-field schema detail (names, types, nullability, indexes).
- **RBAC:** `db:schema:read` — admin, read-write, read-only
- **Input schema:**
  ```json
  { "type": "object", "properties": { "profile_id": { "type": "string" }, "namespace": { "type": "string" }, "entity": { "type": "string" } }, "required": ["profile_id", "namespace", "entity"] }
  ```
- **Output schema:**
  ```json
  { "type": "object", "properties": { "fields": { "type": "array", "items": { "type": "object", "properties": { "name": { "type": "string" }, "types": { "type": "array" } } } } } }
  ```
- **Errors:** `401`, `403`, `404`, `503`

### 2.19 `schema.list_indexes`
- **Description:** List entity indexes with their definitions.
- **RBAC:** `db:schema:read` — admin, read-write, read-only
- **Input schema:**
  ```json
  { "type": "object", "properties": { "profile_id": { "type": "string" }, "namespace": { "type": "string" }, "entity": { "type": "string" } }, "required": ["profile_id", "namespace", "entity"] }
  ```
- **Output schema:**
  ```json
  { "type": "object", "properties": { "items": { "type": "array", "items": { "type": "object", "properties": { "name": { "type": "string" } } } } } }
  ```
- **Errors:** `401`, `403`, `404`, `503`

### 2.20 `schema.sample_shapes`
- **Description:** Sample entity document shapes to infer field presence patterns.
- **RBAC:** `db:schema:read` — admin, read-write, read-only
- **Input schema:**
  ```json
  { "type": "object", "properties": { "profile_id": { "type": "string" }, "namespace": { "type": "string" }, "entity": { "type": "string" }, "count": { "type": "integer", "default": 5 } }, "required": ["profile_id", "namespace", "entity"] }
  ```
- **Output schema:**
  ```json
  { "type": "object", "properties": { "items": { "type": "array" } } }
  ```
- **Errors:** `401`, `403`, `404`, `503`

### 2.21 `schema.change.plan`
- **Description:** Plan a dry-run schema change (preview before applying).
- **RBAC:** `db:schema:read` — admin, read-write, read-only
- **Input schema:**
  ```json
  { "type": "object", "properties": { "profile_id": { "type": "string" }, "namespace": { "type": "string" }, "entity": { "type": "string" }, "change": { "type": "object" } }, "required": ["profile_id"] }
  ```
- **Output schema:**
  ```json
  { "type": "object", "properties": { "plan_id": { "type": "string" }, "status": { "type": "string" }, "steps": { "type": "array" } } }
  ```
- **Errors:** `401`, `403`, `404`, `422`

### 2.22 `schema.change.apply`
- **Description:** Apply a planned schema change.
- **RBAC:** `db:schema:migrate` — admin only
- **Input schema:**
  ```json
  { "type": "object", "properties": { "profile_id": { "type": "string" }, "plan_id": { "type": "string" } }, "required": ["profile_id"] }
  ```
- **Output schema:**
  ```json
  { "type": "object", "properties": { "change_id": { "type": "string" }, "status": { "type": "string" }, "applied_at": { "type": "string" } } }
  ```
- **Errors:** `401`, `403`, `404`, `422`, `409` (conflict)

### 2.23 `schema.change.history`
- **Description:** List recent schema changes with audit trail.
- **RBAC:** `db:schema:read` — admin, read-write, read-only
- **Input schema:**
  ```json
  { "type": "object", "properties": { "profile_id": { "type": "string" }, "limit": { "type": "integer", "default": 20 }, "status": { "type": "string" } } }
  ```
- **Output schema:**
  ```json
  { "type": "object", "properties": { "items": { "type": "array" } } }
  ```
- **Errors:** `401`, `403`

### 2.24 `data.read`
- **Description:** Read content using the structured filter model (not raw query — connector-translated structured filter).
- **RBAC:** `db:data:read` — admin, read-write, read-only
- **Input schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "profile_id": { "type": "string" },
      "namespace": { "type": "string" },
      "entity": { "type": "string" },
      "filter": { "type": "object", "description": "Structured filter (see PARAMETERS.md for filter grammar)" },
      "projection": { "type": "object", "description": "Field include/exclude spec" },
      "sort": { "type": "object", "description": "Sort spec" },
      "limit": { "type": "integer", "default": 50 },
      "offset": { "type": "integer", "default": 0 }
    },
    "required": ["profile_id", "namespace", "entity"]
  }
  ```
- **Output schema:**
  ```json
  { "type": "object", "properties": { "items": { "type": "array" }, "offset": { "type": "integer" }, "limit": { "type": "integer" } } }
  ```
- **Errors:** `401`, `403`, `404`, `422` (bad filter), `503`
- **Example call:**
  ```bash
  curl -X POST https://<host>/mcp \
    -H "Content-Type: application/json" \
    -H "X-API-Key: ${API_KEY}" \
    -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"data.read","arguments":{"profile_id":"prod-mongo","namespace":"mydb","entity":"users","limit":10}},"id":1}'
  ```

### 2.25 `data.create`
- **Description:** Insert one or more content records. Accepts `document` (single) or `documents` (bulk) keys.
- **RBAC:** `db:data:write` — admin, read-write
- **Input schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "profile_id": { "type": "string" },
      "namespace": { "type": "string" },
      "entity": { "type": "string" },
      "document": { "type": "object", "description": "Single document to insert" },
      "documents": { "type": "array", "description": "Bulk documents to insert" }
    },
    "required": ["profile_id", "namespace", "entity"]
  }
  ```
- **Output schema (single):**
  ```json
  { "type": "object", "properties": { "id": { "type": "string" }, "document": { "type": "object" } } }
  ```
- **Output schema (bulk):**
  ```json
  { "type": "object", "properties": { "inserted_count": { "type": "integer" }, "documents": { "type": "array" } } }
  ```
- **Notes:** Binary values may be passed using the envelope `{"__type__": "binary", "encoding": "hex"|"base64", "data": "..."}`.
- **Errors:** `401`, `403`, `404`, `422`, `503`

### 2.26 `data.update`
- **Description:** Update content records matching a structured filter.
- **RBAC:** `db:data:write` — admin, read-write
- **Input schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "profile_id": { "type": "string" },
      "namespace": { "type": "string" },
      "entity": { "type": "string" },
      "filter": { "type": "object" },
      "update": { "type": "object", "description": "Update specification" }
    },
    "required": ["profile_id", "namespace", "entity"]
  }
  ```
- **Output schema:**
  ```json
  { "type": "object", "properties": { "matched_count": { "type": "integer" }, "modified_count": { "type": "integer" } } }
  ```
- **Errors:** `401`, `403`, `404`, `422`, `503`

### 2.27 `data.delete`
- **Description:** Delete content records matching a structured filter.
- **RBAC:** `db:data:delete` — admin, read-write
- **Input schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "profile_id": { "type": "string" },
      "namespace": { "type": "string" },
      "entity": { "type": "string" },
      "filter": { "type": "object" }
    },
    "required": ["profile_id", "namespace", "entity"]
  }
  ```
- **Output schema:**
  ```json
  { "type": "object", "properties": { "deleted_count": { "type": "integer" } } }
  ```
- **Errors:** `401`, `403`, `404`, `422`, `503`

### 2.28 `data.count`
- **Description:** Count content records matching a structured filter.
- **RBAC:** `db:data:read` — admin, read-write, read-only
- **Input schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "profile_id": { "type": "string" },
      "namespace": { "type": "string" },
      "entity": { "type": "string" },
      "filter": { "type": "object" }
    },
    "required": ["profile_id", "namespace", "entity"]
  }
  ```
- **Output schema:**
  ```json
  { "type": "object", "properties": { "count": { "type": "integer" } } }
  ```
- **Errors:** `401`, `403`, `404`, `503`

### 2.29 `data.exists`
- **Description:** Check whether any content records match a structured filter.
- **RBAC:** `db:data:read` — admin, read-write, read-only
- **Input schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "profile_id": { "type": "string" },
      "namespace": { "type": "string" },
      "entity": { "type": "string" },
      "filter": { "type": "object" }
    },
    "required": ["profile_id", "namespace", "entity"]
  }
  ```
- **Output schema:**
  ```json
  { "type": "object", "properties": { "exists": { "type": "boolean" }, "count": { "type": "integer" } } }
  ```
- **Errors:** `401`, `403`, `404`, `503`

### 2.30 `relationship.list`
- **Description:** List persisted relationships for an entity.
- **RBAC:** `db:relationship:read` — admin, read-write, read-only
- **Input schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "profile_id": { "type": "string" },
      "namespace": { "type": "string" },
      "entity": { "type": "string" }
    },
    "required": ["profile_id"]
  }
  ```
- **Output schema:**
  ```json
  { "type": "object", "properties": { "items": { "type": "array" } } }
  ```
- **Errors:** `401`, `403`, `404`

### 2.31 `relationship.get`
- **Description:** Get a single relationship by ID.
- **RBAC:** `db:relationship:read` — admin, read-write, read-only
- **Input schema:**
  ```json
  { "type": "object", "properties": { "relationship_id": { "type": "string" } }, "required": ["relationship_id"] }
  ```
- **Output schema:**
  ```json
  { "type": "object", "properties": { "relationship_id": { "type": "string" }, "source": { "type": "object" }, "target": { "type": "object" }, "type": { "type": "string" } } }
  ```
- **Errors:** `401`, `403`, `404`

### 2.32 `relationship.infer`
- **Description:** Infer relationship candidates from source data heuristics.
- **RBAC:** `db:relationship:write` — admin, read-write
- **Input schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "profile_id": { "type": "string" },
      "namespace": { "type": "string" },
      "entity": { "type": "string" }
    },
    "required": ["profile_id"]
  }
  ```
- **Output schema:**
  ```json
  { "type": "object", "properties": { "items": { "type": "array" } } }
  ```
- **Errors:** `401`, `403`, `404`

### 2.33 `relationship.create`
- **Description:** Create a curated relationship between two entities.
- **RBAC:** `db:relationship:write` — admin, read-write
- **Input schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "profile_id": { "type": "string" },
      "source": { "type": "object", "properties": { "namespace": { "type": "string" }, "entity": { "type": "string" } } },
      "target": { "type": "object", "properties": { "namespace": { "type": "string" }, "entity": { "type": "string" } } },
      "type": { "type": "string" }
    },
    "required": ["profile_id", "source", "target", "type"]
  }
  ```
- **Output schema:**
  ```json
  { "type": "object", "properties": { "relationship_id": { "type": "string" }, "created_at": { "type": "string" } } }
  ```
- **Errors:** `401`, `403`, `422`

### 2.34 `relationship.update`
- **Description:** Update relationship metadata (type, annotations).
- **RBAC:** `db:relationship:write` — admin, read-write
- **Input schema:**
  ```json
  { "type": "object", "properties": { "relationship_id": { "type": "string" } }, "required": ["relationship_id"] }
  ```
- **Output schema:**
  ```json
  { "type": "object", "properties": { "relationship_id": { "type": "string" }, "updated": { "type": "boolean" } } }
  ```
- **Errors:** `401`, `403`, `404`

### 2.35 `relationship.delete`
- **Description:** Delete a relationship by ID.
- **RBAC:** `db:relationship:delete` — admin, read-write
- **Input schema:**
  ```json
  { "type": "object", "properties": { "relationship_id": { "type": "string" } }, "required": ["relationship_id"] }
  ```
- **Output schema:**
  ```json
  { "type": "object", "properties": { "deleted": { "type": "boolean" }, "relationship_id": { "type": "string" } } }
  ```
- **Errors:** `401`, `403`, `404`

### 2.36 `audit.list_events`
- **Description:** List audit events with optional type filter and pagination.
- **RBAC:** `db:audit:read` — admin, read-write, read-only
- **Input schema:**
  ```json
  { "type": "object", "properties": { "limit": { "type": "integer", "default": 50 }, "event_type": { "type": "string" } } }
  ```
- **Output schema:**
  ```json
  { "type": "object", "properties": { "items": { "type": "array" } } }
  ```
- **Errors:** `401`, `403`

### 2.37 `audit.get_event`
- **Description:** Get detail for a single audit event by ID.
- **RBAC:** `db:audit:read` — admin, read-write, read-only
- **Input schema:**
  ```json
  { "type": "object", "properties": { "event_id": { "type": "string" } }, "required": ["event_id"] }
  ```
- **Output schema:**
  ```json
  { "type": "object", "properties": { "event_id": { "type": "string" }, "event_type": { "type": "string" }, "actor": { "type": "object" }, "target": { "type": "object" }, "outcome": { "type": "string" }, "timestamp": { "type": "string" } } }
  ```
- **Errors:** `401`, `403`, `404`

### 2.38 `search.metadata`
- **Description:** Search entity, field, namespace, and relationship metadata by keyword.
- **RBAC:** `db:search:read` — admin, read-write, read-only
- **Input schema:**
  ```json
  { "type": "object", "properties": { "profile_id": { "type": "string" }, "query": { "type": "string" }, "limit": { "type": "integer" } }, "required": ["profile_id", "query"] }
  ```
- **Output schema:**
  ```json
  { "type": "object", "properties": { "items": { "type": "array" } } }
  ```
- **Errors:** `401`, `403`, `404`

### 2.39 `search.content`
- **Description:** Search indexed content excerpts across all indexed entities in a profile.
- **RBAC:** `db:search:read` — admin, read-write, read-only
- **Input schema:**
  ```json
  { "type": "object", "properties": { "profile_id": { "type": "string" }, "query": { "type": "string" }, "limit": { "type": "integer" } }, "required": ["profile_id", "query"] }
  ```
- **Output schema:**
  ```json
  { "type": "object", "properties": { "items": { "type": "array" } } }
  ```
- **Errors:** `401`, `403`, `404`

### 2.40 `search.related`
- **Description:** Find related entities for a given entity using the discovery index.
- **RBAC:** `db:search:read` — admin, read-write, read-only
- **Input schema:**
  ```json
  { "type": "object", "properties": { "profile_id": { "type": "string" }, "namespace": { "type": "string" }, "entity": { "type": "string" }, "limit": { "type": "integer", "default": 10 } }, "required": ["profile_id", "namespace", "entity"] }
  ```
- **Output schema:**
  ```json
  { "type": "object", "properties": { "items": { "type": "array" } } }
  ```
- **Errors:** `401`, `403`, `404`

### 2.41 `search.explain_match`
- **Description:** Explain why a specific document matched a discovery search result.
- **RBAC:** `db:search:read` — admin, read-write, read-only
- **Input schema:**
  ```json
  { "type": "object", "properties": { "profile_id": { "type": "string" }, "query": { "type": "string" }, "document_id": { "type": "string" } }, "required": ["profile_id", "query", "document_id"] }
  ```
- **Output schema:**
  ```json
  { "type": "object", "properties": { "document_id": { "type": "string" }, "score": { "type": "number" }, "explanation": { "type": "object" } } }
  ```
- **Errors:** `401`, `403`, `404`

### 2.42 `index.status`
- **Description:** Show discovery index freshness and coverage for one or all profiles.
- **RBAC:** `db:index:read` — admin, read-write, read-only
- **Input schema:**
  ```json
  { "type": "object", "properties": { "profile_id": { "type": "string", "description": "Optional: scope to one profile" } } }
  ```
- **Output schema:**
  ```json
  { "type": "object", "properties": { "profiles": { "type": "array", "items": { "type": "object", "properties": { "profile_id": { "type": "string" }, "indexed_entities": { "type": "integer" }, "last_synced": { "type": "string" } } } } } }
  ```
- **Errors:** `401`, `403`

### 2.43 `index.sync_profile`
- **Description:** Queue and execute a profile discovery index refresh (all entities in profile).
- **RBAC:** `db:index:write` — admin, read-write
- **Input schema:**
  ```json
  { "type": "object", "properties": { "profile_id": { "type": "string" } }, "required": ["profile_id"] }
  ```
- **Output schema:**
  ```json
  { "type": "object", "properties": { "job_id": { "type": "string" }, "status": { "type": "string" } } }
  ```
- **Errors:** `401`, `403`, `404`

### 2.44 `index.sync_entity`
- **Description:** Queue and execute an entity discovery index refresh (one entity in profile).
- **RBAC:** `db:index:write` — admin, read-write
- **Input schema:**
  ```json
  { "type": "object", "properties": { "profile_id": { "type": "string" }, "namespace": { "type": "string" }, "entity": { "type": "string" } }, "required": ["profile_id", "namespace", "entity"] }
  ```
- **Output schema:**
  ```json
  { "type": "object", "properties": { "job_id": { "type": "string" }, "status": { "type": "string" } } }
  ```
- **Errors:** `401`, `403`, `404`

### 2.45 `index.rebuild`
- **Description:** Queue and execute a full discovery index rebuild for specified profiles (or all profiles).
- **RBAC:** `db:index:write` — admin, read-write
- **Input schema:**
  ```json
  { "type": "object", "properties": { "profile_ids": { "type": "array", "items": { "type": "string" }, "description": "Empty = all accessible profiles" } } }
  ```
- **Output schema:**
  ```json
  { "type": "object", "properties": { "job_id": { "type": "string" }, "status": { "type": "string" }, "profile_count": { "type": "integer" } } }
  ```
- **Errors:** `401`, `403`

---

## 3. Cross-references
- [API-REFERENCE.md](API-REFERENCE.md)
- [A2A-REFERENCE.md](A2A-REFERENCE.md)
- [ROLES-AND-USECASES.md](ROLES-AND-USECASES.md)
- PS-72-mcp-a2a-webui.md

## 4. Project-specific notes

All MCP tool calls are wrapped by `wrap_tool_contract` (TD-001, W28E-1808B) which emits full NIST AU-3 audit events (actor/ip/roles/target/outcome/correlation/session/duration) via the platform `AuditLogger`. Sensitive parameters (`password`, `secret`, `token`, `api_key`, `connection_string`, `documents`, `records`) are automatically redacted in audit payloads by `_redact_params`.

Source registries:
- Access control: `src/servers/mcp/access_control_tools.py` (12 tools)
- Catalog: `src/servers/mcp/catalog_tools.py` (4 tools)
- Schema: `src/servers/mcp/schema_tools.py` (7 tools)
- Content: `src/servers/mcp/content_tools.py` (6 tools)
- Relationship: `src/servers/mcp/relationship_tools.py` (6 tools)
- Audit: `src/servers/mcp/audit_tools.py` (2 tools)
- Search + Index: `src/servers/mcp/search_tools.py` (8 tools)
