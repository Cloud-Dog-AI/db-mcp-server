# db-mcp-server — Agent & Engineer Rules

**Version:** 1.0
**Date:** 2026-03-21
**Parent:** `cloud-dog-ai-platform-standards/RULES.md` v1.6

> Read the parent rules in full first. All platform rules apply. This file adds db-mcp-server-specific constraints only.

## 1. Platform Rules (Inherited)
- All platform rules from `../cloud-dog-ai-platform-standards/RULES.md` apply without exception.

## 2. Four-Server Pattern
This project is allocated these ports:
- API server: `8086`
- Web server: `8087`
- MCP server: `8088`
- A2A server: `8089`

Do not change these without an explicit dispatch-table update.

## 3. Platform Package Rules
The project must use:
- `cloud_dog_config` for layered config and Vault resolution
- `cloud_dog_logging` for logging and audit output
- `cloud_dog_api_kit` for API/web server bootstrap
- `cloud_dog_idam` for users, groups, API keys, RBAC, and profile access rules
- `cloud_dog_jobs` for indexing, schema-change, and relationship-maintenance jobs
- `cloud_dog_db` for the metadata store and audit persistence

## 4. Query And Operation Rules
- Do not use free-text query generation as the primary execution model.
- Use a structured filter model for catalogue, content, search, and schema operations.
- LLMs may assist summarisation, discovery ranking, and explanation, but not replace structured execution planning.

## 5. Connector Rules
Phase 1 connectors are:
- MongoDB
- CouchDB
- OpenSearch
- Elasticsearch
- Cassandra

Each source must have exactly one adapter module under `src/core/connectors/<source>/`.
Business logic may not import third-party source clients directly.

## 6. Schema Change Safety
- Schema changes must follow validate -> plan -> review -> approve -> execute -> audit.
- Plan/apply flows must be job-backed and auditable.
- Dry-run support is mandatory before execution support is considered complete.

## 7. Security Model
- Profile-based access is mandatory.
- Users/groups/API keys/RBAC must come from `cloud_dog_idam`.
- Field masking and sensitive-field suppression must be enforced at the service layer, not only in UI consumers.

## 8. Testing Expectations
- ST/IT/AT must use real database/search systems for each enabled connector.
- No mocked connectors in ST/IT/AT.
- Test env files must use Vault expressions for real credentials in IT/AT.
