# db-mcp-server — RULES.md

## Common Rules

This project follows the [Cloud-Dog AI Platform Common Rules](../cloud-dog-ai-platform-standards/RULES.md) v2.7+.
Common rules are NOT restated here; consult central for: integrity (§1), environment+config (§2),
server+process management (§3), code+change management (§4), testing (§5), documentation (§6),
repo structure (§7), operational controls (§8), security boundaries (§9), infrastructure
protection (§10), Vault path verification (§11), implementation truthfulness (§12),
sandbox dispatch preconditions (§13 once landed), mandatory reading (§14 once renumbered).

Mandatory reading before any work in this repo (in addition to central RULES.md):
- `cloud-dog-ai-platform-standards/AGENT-LESSONS.md` (cross-platform knowledge)
- `cloud-dog-ai-platform-standards/working/AGENT-BOOTSTRAP-DIRECTIVE.md` (platform orientation)
- This file (project-specific rules below)

## Project-Specific Rules

### 1. Verified Port Assignments

Verified against [tests/env-ST](/opt/iac/Development/cloud-dog-ai/db-mcp-server/tests/env-ST):
- API server: `8086`
- Web server: `8087`
- MCP server: `8088`
- A2A server: `8089`

Do not change these without an explicit dispatch-table update and matching config/test evidence.

### 2. Server Architecture

This repository follows the four-server pattern:
- API server for REST/admin/CRUD flows
- Web server for browser UI and authenticated proxying
- MCP server for tool calls and JSON-RPC transports
- A2A server for agent-card/task and event-style agent integrations

All server lifecycle operations must go through `server_control.sh`.
Direct `python3 start_*.py`, `pkill`, and other ad-hoc process control is forbidden.

### 3. Standard Env Files

- `tests/env-UT`
- `tests/env-ST`
- `tests/env-IT`
- `tests/env-AT`
- `tests/env-QT`

All server start/stop/status and all pytest runs must use `--env`.

### 4. Query and Operation Rules

- Do not use free-text query generation as the primary execution model.
- Use a structured filter model for catalogue, content, search, and schema operations.
- LLMs may assist summarisation, discovery ranking, and explanation, but must not replace structured execution planning.
- Query planning, schema exploration, and mutation proposals must remain auditable.
- Every write-capable operation must distinguish dry-run from execute mode.

### 5. Connector Rules

Phase 1 connectors (5):
- MongoDB
- CouchDB
- OpenSearch
- Elasticsearch
- Cassandra

(Programme connector matrix per W28A-881 §5 enumerates 8 connectors total — postgres / mysql / mssql / sqlite are SQL-side and reach db-mcp through `cloud_dog_db`; the five listed above are the NoSQL/search adapters owned directly by this service.)

Connector constraints:
- Each source must have exactly one adapter module under `src/core/connectors/<source>/`
- Business logic may not import third-party source clients directly
- Connector-specific secrets must come from config/Vault, never hardcoded
- Source-specific result shaping belongs in the adapter layer, not the UI
- Connector health/status claims require evidence from real config or real tests

### 6. Schema Change Safety

- Schema changes must follow `validate → plan → review → approve → execute → audit`
- Plan/apply flows must be job-backed and auditable
- Dry-run support is mandatory before execution support is considered complete
- Never present an execution path as safe if the dry-run and approval gates are missing
- Migration and relationship-maintenance jobs must emit auditable state transitions
- Destructive SQL/NoSQL verbs (DROP, TRUNCATE, DELETE-without-filter, collection-drop, index-drop) MUST be blocked by the connector adapter unless the explicit execute-mode + approval token is supplied; dry-run must surface every destructive verb to the reviewer.

### 7. Security Model — Profile-Scoped RBAC

- Profile-based access is mandatory; db-mcp RBAC is profile-scoped (a principal's access set is scoped to the connection profile, not just the global role).
- Users / groups / API keys / RBAC must come from `cloud_dog_idam`.
- Field masking and sensitive-field suppression must be enforced at the service layer, not only in UI consumers.
- Reader/writer/admin distinctions must be enforced in backend code, not only hidden in the UI.
- Any denied action must return a real `403` and be reported honestly in evidence.

### 8. Testing Expectations (db-mcp-specific addenda to central §5)

- UT may use isolated/local test doubles where appropriate.
- ST/IT/AT must use real database/search systems for each enabled connector.
- No mocked connectors in ST/IT/AT.
- Test env files must use Vault expressions for real credentials in IT/AT.
- Playwright, when used, must run with `--workers=1`.
- Do not weaken tests to make them pass; fix the implementation or document a genuine expectation error with the governing standard.

#### 8.1 Verification discipline
- Report exact test counts, not paraphrases.
- Separate code-adoption status from harness/environment failures.
- If a connector backend is unavailable, report BLOCKED rather than inventing a substitute.

#### 8.2 RBAC denial proofs
- Any RBAC/compliance fix must include a real denial proof, not just scanner-zero output.
- If a scanner passes but runtime denial is wrong, the fix is incomplete.

### 9. Platform Incidents Especially Relevant Here

These are central RULES.md / AGENT-LESSONS.md incidents whose causes recur in db-mcp work — consult the central record for each:
- Central §1.1 Falsification — relevant to all db-mcp evidence files, grep outputs, line-count claims, completion reports.
- Central §1.3 Fabrication — relevant to all connector names, hostnames, ports, model names, query capabilities, and report claims.
- Central §1.5 Production firewall — relevant to all Docker/Terraform deployment work for this service.

## Incident Records

### Local incident record placeholder
- No db-mcp-specific incident record is documented here yet.
- If a db-mcp-specific incident occurs, record the date, exact failure, violated rule, and prevention rule added (see central RULES.md §1.1 / §1.3 / §1.5 for the established format).
