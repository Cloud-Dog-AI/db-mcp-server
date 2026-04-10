# Agent Lessons Learned — db-mcp-server

**Purpose:** Lessons from recent agent work on this service. Read before making changes.

---

## Code

### IDAM Compliance (W28A-705)
- APIKeyAuthoriser wrapper class was eliminated. Replaced with a simple `verify_api_key()` function in `common/auth.py` that delegates directly to `AccessControlService.verify_api_key()`.
- AccessControlService in `core/access_control/service.py` already uses `cloud_dog_idam.api_keys.hashing.hash_api_key` and `key_matches` — the refactoring only removed the unnecessary wrapper class.
- `common/runtime.py` uses a thin `_AuthBridge` class to maintain the `runtime.auth.verify_api_key(key)` call pattern expected by route handlers.
- Custom domain models (AccessUser, AccessGroup, AccessApiKey) in `core/access_control/models.py` are project-specific extensions — they were flagged by the IDAM scanner but serve a legitimate purpose (DB provider roles, profile-scoped access).

### WebUI (W28A-715)
- UsersPage.tsx and ApiKeysPage.tsx: Added Badge status colours (active=default/green, other=destructive/red).
- GroupsPage.tsx already had all required columns (Name, Description, Roles, Members).
- RbacPage.tsx already present with role definitions and assignments. Uses AdminRbacPage pattern wrapper.
- SettingsPage.tsx: All 7 PS-73 sections present including Health with Badge and Disable/Enable toggle.
- ApiDocsPage.tsx: Tab navigation (API/MCP/A2A) + DocumentViewer for service documentation.

## Test Environment

- 50 passed, 0 failed baseline for unit tests.
- Tests require `--env tests/env-UT` flag.
- IDAM scanner shows 7 violations (3 bespoke models + 4 RBAC gaps) — the bespoke models are project-specific extensions, not pure replacements.

## Infrastructure

- Ports: API 8086, Web 8087, MCP 8088, A2A 8089.
- Preprod: dbmcpserver0.cloud-dog.net.
- 5 RBAC roles: admin, data_steward, developer, analyst, auditor.

## Architecture

- AccessControlService is the auth orchestrator — bootstraps admin user and API key at startup.
- Uses `RBACEngine` from cloud_dog_idam with `DEFAULT_ROLE_PERMISSIONS` configuration.
- Job types: discovery.rebuild, discovery.sync_profile, discovery.sync_entity.
- Multi-provider database connectivity: MongoDB, PostgreSQL, MySQL, CouchDB, OpenSearch, Elasticsearch, Cassandra.

## Related Projects

- cloud-dog-ai-ui-monorepo: app at apps/db-mcp/. Has comprehensive admin pages (Users, Groups, ApiKeys, Rbac, Catalogue, DataBrowser, Schema, Relationships, Search).
- cloud_dog_idam: Uses RBACEngine, hash_api_key, key_matches for authentication.
- cloud_dog_jobs: Job types for discovery operations with SQL backend.
