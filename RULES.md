# db-mcp-server — Agent & Engineer Rules

**Version:** 3.0
**Date:** 2026-04-13
**Extends:** `cloud-dog-ai-platform-standards/RULES.md` v2.3 (2026-03-31)

> **PRIME DIRECTIVE — BINDING ON ALL AGENTS WORKING IN THIS REPOSITORY:**
> I WILL NEVER: LIE, FUDGE, HACK, FALSIFY, STUB, FAKE, HIDE, PRETEND, SKIP, BYPASS, FABRICATE, SUBSTITUTE, INVENT.
> IF I CANNOT GUARANTEE 100% COMPLIANCE, I WILL STOP AND SAY SO.
> IF TESTS FAIL, I WILL REPORT FAILURES HONESTLY.
> IF I DON'T KNOW, I WILL ASK, NOT GUESS.
>
> **§1.2 — The programme coordinator MUST independently verify ALL agent claims.**
> Every claim requires: independent grep/command execution, cross-reference evidence against source,
> spot-check fixes, reject on ANY discrepancy.

## Mandatory Reading Before ANY Work
1. Platform RULES.md — `cloud-dog-ai-platform-standards/RULES.md` (binding contract)
2. AGENT-LESSONS.md — `cloud-dog-ai-platform-standards/AGENT-LESSONS.md` (cross-platform knowledge, PC1-PC25)
3. This file — project-specific rules below
4. AGENT-BOOTSTRAP-DIRECTIVE.md — `cloud-dog-ai-platform-standards/working/AGENT-BOOTSTRAP-DIRECTIVE.md` (platform orientation)

## Relevant Platform Incidents
- §1.1 Falsification incident — relevant to all db-mcp work and all evidence files
- §1.3 Fabrication incident — relevant to all connector names, query modes, schema-change claims, ports, and report claims
- §1.5 Production firewall incident — relevant to all Docker/Terraform deployment work for this service

---

## Section 1 — Platform Rules (Inherited)

All rules from `cloud-dog-ai-platform-standards/RULES.md` v2.3 apply without exception:
- **§ 1** Integrity and honesty (non-negotiable)
- **§ 1.2** Coordinator verification mandate
- **§ 1.3** Fabrication incident record
- **§ 1.5** Production firewall incident protections
- **§ 2** Configuration precedence: `os.environ → env file → config.yaml → defaults.yaml`
- **§ 2.3** Credential management: Vault primary; `private/` only for credentials not yet in Vault
- **§ 2.4** Zero hardcoded values (zero tolerance)
- **§ 3** Server and process management (server_control.sh, Docker rules)
- **§ 4** Code and change management
- **§ 5** Testing rules (UT/ST/IT/AT hierarchy, real systems, forensic validation)
- **§ 6** Documentation standards (REQUIREMENTS, ARCHITECTURE, TESTS, TASKS, etc.)
- **§ 8.8** Coordinator forensic verification of agent claims
- **Mandatory Completion Warranty** required on every task completion

## Section 2 — Environment and Configuration

### 2.1 Configuration precedence
- Preserve the full chain: `os.environ → env file → config.yaml → defaults.yaml`
- All server start/stop/status and all pytest runs must use `--env`
- Never bypass the config package with ad-hoc shell exports or temporary resolvers

### 2.2 Vault and secret handling
- Source Vault before any Vault-dependent operation:
  `set -a; source /opt/iac/Development/cloud-dog-ai/env-vault; set +a`
- Credentials belong in Vault or gitignored `private/` overlays only
- Never commit real database passwords, API keys, TLS keys, or connector tokens

### 2.3 Standard env files
- `tests/env-UT`
- `tests/env-ST`
- `tests/env-IT`
- `tests/env-AT`
- `tests/env-QT`

## Section 3 — Verified Port Assignments

Verified against [tests/env-ST](/opt/iac/Development/cloud-dog-ai/db-mcp-server/tests/env-ST):
- API server: `8086`
- Web server: `8087`
- MCP server: `8088`
- A2A server: `8089`

Do not change these without an explicit dispatch-table update and matching config/test evidence.

## Section 4 — Platform Package Rules

The project must use:
- `cloud_dog_config` for layered config and Vault resolution
- `cloud_dog_logging` for logging and audit output
- `cloud_dog_api_kit` for API/web server bootstrap
- `cloud_dog_idam` for users, groups, API keys, RBAC, and profile access rules
- `cloud_dog_jobs` for indexing, schema-change, and relationship-maintenance jobs
- `cloud_dog_db` for metadata store, audit persistence, and application state

Never introduce bespoke alternatives for these concerns.

## Section 5 — Server Architecture

This repository follows the four-server pattern:
- API server for REST/admin/CRUD flows
- Web server for browser UI and authenticated proxying
- MCP server for tool calls and JSON-RPC transports
- A2A server for agent-card/task and event-style agent integrations

All server lifecycle operations must go through `server_control.sh`.
Direct `python3 start_*.py`, `pkill`, and other ad-hoc process control is forbidden.

## Section 6 — Query And Operation Rules

- Do not use free-text query generation as the primary execution model.
- Use a structured filter model for catalogue, content, search, and schema operations.
- LLMs may assist summarisation, discovery ranking, and explanation, but must not replace structured execution planning.
- Query planning, schema exploration, and mutation proposals must remain auditable.
- Every write-capable operation must distinguish dry-run from execute mode.

## Section 7 — Connector Rules

Phase 1 connectors are:
- MongoDB
- CouchDB
- OpenSearch
- Elasticsearch
- Cassandra

Connector constraints:
- Each source must have exactly one adapter module under `src/core/connectors/<source>/`
- Business logic may not import third-party source clients directly
- Connector-specific secrets must come from config/Vault, never hardcoded
- Source-specific result shaping belongs in the adapter layer, not the UI
- Connector health/status claims require evidence from real config or real tests

## Section 8 — Schema Change Safety

- Schema changes must follow `validate → plan → review → approve → execute → audit`
- Plan/apply flows must be job-backed and auditable
- Dry-run support is mandatory before execution support is considered complete
- Never present an execution path as safe if the dry-run and approval gates are missing
- Migration and relationship-maintenance jobs must emit auditable state transitions

## Section 9 — Security Model

- Profile-based access is mandatory
- Users/groups/API keys/RBAC must come from `cloud_dog_idam`
- Field masking and sensitive-field suppression must be enforced at the service layer, not only in UI consumers
- Reader/writer/admin distinctions must be enforced in backend code, not only hidden in the UI
- Any denied action must return a real `403` and be reported honestly in evidence

## Section 10 — Testing Expectations

Platform §5 applies in full. db-mcp-specific expectations:
- UT may use isolated/local test doubles where appropriate
- ST/IT/AT must use real database/search systems for each enabled connector
- No mocked connectors in ST/IT/AT
- Test env files must use Vault expressions for real credentials in IT/AT
- Playwright, when used, must run with `--workers=1`
- Do not weaken tests to make them pass; fix the implementation or document a genuine expectation error with the governing standard

### 10.1 Verification discipline
- Report exact test counts, not paraphrases
- Separate code-adoption status from harness/environment failures
- If a connector backend is unavailable, report BLOCKED rather than inventing a substitute

### 10.2 RBAC and denial proofs
- Any RBAC/compliance fix must include a real denial proof, not just scanner-zero output
- If a scanner passes but runtime denial is wrong, the fix is incomplete

## Section 11 — Deployment and Infrastructure

- Docker image work must use `docker-build.sh`
- Do not edit running containers
- Do not use SSH for remote operations
- Do not touch firewalls, Shorewall, iptables, nftables, or Docker networking directly
- Terraform is the only approved path for deploy/network-related changes
- If a deployment is requested, follow the platform deployment flow and keep code changes separate from deploy-only instructions unless explicitly combined by the coordinator

## Section 12 — Incident Records and Local History

### 12.1 Platform incidents that matter here
- **§1.1 Falsification:** relevant to all evidence, grep outputs, line-count claims, and completion reports
- **§1.3 Fabrication:** relevant to connector names, hostnames, ports, model names, and query capabilities
- **§1.5 Firewall:** relevant to any Docker/Terraform deployment or remote validation work

### 12.2 Local incident record placeholder
- No db-mcp-specific incident record is documented here yet
- If a db-mcp-specific incident occurs, record the date, exact failure, violated rule, and prevention rule added

## Section 13 — Project-Specific Content Preserved From Prior Version

### 13.1 Original query and execution rules
- Do not use free-text query generation as the primary execution model.
- Use a structured filter model for catalogue, content, search, and schema operations.
- LLMs may assist summarisation, discovery ranking, and explanation, but not replace structured execution planning.

### 13.2 Original connector rules
- Phase 1 connectors are MongoDB, CouchDB, OpenSearch, Elasticsearch, and Cassandra.
- Each source must have exactly one adapter module under `src/core/connectors/<source>/`.
- Business logic may not import third-party source clients directly.

### 13.3 Original schema safety requirements
- Schema changes must follow validate -> plan -> review -> approve -> execute -> audit.
- Plan/apply flows must be job-backed and auditable.
- Dry-run support is mandatory before execution support is considered complete.

### 13.4 Original security model requirements
- Profile-based access is mandatory.
- Users/groups/API keys/RBAC must come from `cloud_dog_idam`.
- Field masking and sensitive-field suppression must be enforced at the service layer, not only in UI consumers.

### 13.5 Original testing expectations
- ST/IT/AT must use real database/search systems for each enabled connector.
- No mocked connectors in ST/IT/AT.
- Test env files must use Vault expressions for real credentials in IT/AT.
