---
template-id: T-WUI
template-version: 1.0
applies-to: docs/WEBUI-REFERENCE.md
registry: service
required: conditional
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

# db-mcp-server — WEBUI-REFERENCE

> **Template version:** T-WUI v1.0 — conditional: service has a WebUI panel.

## 1. Panel structure

The db-mcp WebUI is a React SPA served from `ui/dist/` on port 8087. All routes are browser-history entry paths served by the SPA shell. Backend proxy routes forward requests to the API (8086), MCP (8088), and A2A (8089) servers with cookie-session authentication.

| Route | Panel | Roles | Backend route |
|---|---|---|---|
| `/` | Dashboard / Home | All authenticated | — |
| `/login` | Login form (username/password) | Unauthenticated | `POST /auth/login` |
| `/admin/profiles` | Profile management | admin | `/webapi/v1/profiles` |
| `/admin/users` | User management | admin | `/webapi/v1/users` |
| `/admin/roles` | Role/group management | admin | `/webapi/v1/groups` |
| `/catalogue` | Namespace + entity browser | All authenticated | `/webmcp` → `catalog.*` tools |
| `/catalogue/*` | Entity detail | All authenticated | `/webmcp` → `catalog.get_entity` |
| `/data/*` | Data browser | All authenticated | `/webmcp` → `data.read` |
| `/search` | Discovery search | All authenticated | `/webmcp` → `search.*` tools |
| `/relationships` | Relationship explorer | All authenticated | `/webmcp` → `relationship.*` tools |
| `/schema` | Schema inspector | All authenticated | `/webmcp` → `schema.*` tools |
| `/audit` | Audit event log | All authenticated | `/webmcp` → `audit.*` tools |
| `/mcp-console` | MCP JSON-RPC console | All authenticated | `/webmcp` |
| `/a2a-console` | A2A task console | All authenticated | `/weba2a` |
| `/settings` | Service settings | admin | `/webapi/v1/config` |
| `/api-docs` | Swagger UI proxy | All authenticated | `/webapi-docs` |

Source: `src/servers/web/ui_spa.py` (`_SPA_ENTRY_ROUTES`)

---

## 2. Login

**Auth flow:** username/password cookie (always). The SPA reads `AUTH_MODE: "cookie"` from `/runtime-config.js` and renders a username/password form.

**Session lifetime:** 3600 seconds (in-memory `_sessions` dict; server restart clears sessions).

**Cookie:** `db_web_session` — `HttpOnly`, `SameSite=lax`, `Max-Age=3600`, path=web base path.

**Login endpoint:** `POST /auth/login` — body `{"username": "...", "password": "..."}`. Returns `{"user": {id, displayName, email, roles, permissions}}`.

**Logout:** `POST /auth/logout` — clears cookie; deletes session from memory.

**Current user:** `GET /auth/me` — returns session user or validates `X-API-Key` header directly.

**IDAM principal forwarding (W28A-889-B-R2):** Authenticated sessions inject `X-Request-Source: webui` and `X-Request-User: <idam_username>` headers on API proxy requests. The API tier resolves that user's own RBAC, not the service key's RBAC.

**Flat accounts (W28A-732-R5):**

| Username | Default password | Flat role | IDAM principal |
|----------|-----------------|-----------|---------------|
| `admin` | From `CLOUD_DOG__WEB_LOGIN__PASSWORD` (Vault) | admin | `flat-admin` |
| `read-write` | `BlueRiverChair` (estate default) | read-write | `flat-read-write` |
| `read-only` | `GreenRiverDesk` (estate default) | read-only | `flat-read-only` |

Source: `src/servers/web/app.py` (`_flat_accounts`, `auth_login`)

---

## 3. RBAC visibility matrix

**You MUST include:** what each role sees / can do per panel.

| Panel | admin | read-write | read-only |
|---|---|---|---|
| Dashboard | Full view | Full view | Full view |
| Login | N/A (redirect to `/`) | N/A | N/A |
| /admin/profiles | Full CRUD | Denied (403) | Denied (403) |
| /admin/users | Full CRUD | Denied (403) | Denied (403) |
| /admin/roles | Full CRUD | Denied (403) | Denied (403) |
| /catalogue | Browse all namespaces/entities | Browse allowed namespaces/entities | Browse allowed namespaces/entities |
| /search | Full search | Full search | Full search |
| /schema | View + change.apply | View only | View only |
| /relationships | Create/update/delete | Create/update/delete | View only |
| /audit | View | View | View |
| /mcp-console | All 45 tools | Read + write tools | Read-only tools |
| /a2a-console | All skills | All skills | View only |
| /settings | Full view | Denied | Denied |
| /api-docs | Full view | Full view | Full view |

Write methods (`POST`, `PUT`, `PATCH`, `DELETE`) from a read-only session are blocked at the web tier with `403 {"detail": "read-only role: write operations are not permitted", "role": "read-only"}` before the request reaches the API server.

MCP and A2A proxy requests carry the session role's seeded flat demo API key (`data/flat_role_keys/<role>.key`) so the MCP/A2A tiers enforce per-role RBAC natively. A missing read-only key yields an empty key (downstream 401 — fail-closed); admin/read-write fall back to the service key.

Source: `src/servers/web/app.py` (`_read_only_write_block`, `_session_downstream_key`, `_role_can_write`)

---

## 4. Static routes

SPA entry routes registered in `_SPA_ENTRY_ROUTES` (served by `serve_spa_index()`):

```
/
/login
/admin/profiles
/admin/users
/admin/roles
/catalogue
/search
/relationships
/schema
/audit
/mcp-console
/a2a-console
/settings
```

Additionally, paths starting with `/catalogue/` or `/data/` are treated as SPA entry paths. Any path without a file extension in the last segment is also served as an SPA entry (browser-history route).

Source: `src/servers/web/ui_spa.py` (`_SPA_ENTRY_ROUTES`, `is_spa_entry_path`)

---

## 5. Cross-references
- [API-REFERENCE.md](API-REFERENCE.md)
- [ROLES-AND-USECASES.md](ROLES-AND-USECASES.md)
- [MCP-REFERENCE.md](MCP-REFERENCE.md)
- PS-77-webui-comprehensive.md
- PS-30-ui.md

## 6. Project-specific notes

The WebUI SPA is built from `cloud-dog-ai-ui-monorepo/apps/db-mcp` and vendored into `ui/dist/`. The service serves `ui/dist/` via `cloud_dog_storage.LocalStorage` (PS-85 storage abstraction). If `ui/dist/index.html` is missing, all SPA routes return `503 {"detail": "UI dist is missing..."}`.

Proxy paths summary:
- `/api/*`, `/webapi/*` → API server (8086) via `api_session_proxy` with `X-Request-User` identity header
- `/mcp/*`, `/webmcp/*` → MCP server (8088) with session role API key
- `/weba2a/*` → A2A server (8089) with session role API key
- `/webapi-docs` → API Swagger UI proxy
- `/webapi-openapi.json` → API OpenAPI JSON proxy
