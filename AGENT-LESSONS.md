# Agent lessons — db-mcp-server

Last reviewed: 2026-07-15
Scope: durable project-specific knowledge only.

## Authority and use

The binding programme rules and cross-programme lessons are in
`../cloud-dog-ai-platform-standards/RULES.md` and
`../cloud-dog-ai-platform-standards/AGENT-LESSONS.md`. This file is an overlay:
central authority wins on conflict. Read current project source, canonical docs, the
exact instruction and SSOT before acting.

Mutable versions, ports, endpoints, credentials, counts and lane states are not
authority here; resolve them from current configuration, manifests and source.

## Current project knowledge

- **DB-PROFILE-001 — Provider profiles.** Database providers, credentials and profile
  permissions come from current common configuration/Vault authority. Never infer
  connector availability from an old provider count or provision an unauthorised local
  database.
- **DB-CONNECTOR-001 — Connector truth.** A configured provider is not an implemented
  adapter. Prove the connector module, profile validation and real functional operations
  before claiming support.
- **DB-CORE-001 — Four surfaces.** API, Web, MCP and A2A share the
  catalogue/content/schema/search/relationship/access-control core; changes to a core
  contract need proof through every applicable adapter.
- **DB-SEARCH-001 — Discovery index.** Metadata discovery indexing and content search
  are distinct. Full and incremental index operations use the common job lifecycle,
  while content search queries the selected data provider.
- **DB-ERROR-001 — Observable contracts.** Preserve connector error taxonomy and
  translate provider-specific failures at the service boundary so API/MCP consumers
  receive stable errors.
- **DB-UI-001 — UI ownership.** Editable WebUI source and Playwright coverage live in
  the db-mcp monorepo app; the service ships only the exact synced distribution.
- **DB-RBAC-001 — Role configuration.** Read built-in and custom roles from current
  configuration. Tests must prove each permission and negative path rather than relying
  on role names or counts.
- **DB-JOB-001 — Durability claims.** Do not call an inline or memory-backed job path
  durable. Persistent retry/recovery claims require restart and authoritative-store
  proof.

## Historical provenance

The complete pre-refresh document is preserved at commit `88b1ad0e643d05c9c7549c3dfdc97b658bb1a893`, path `AGENT-LESSONS.md`, SHA-256 `ff78a07339b298d536e71e2157f9c7abe030e3c27cdc95c79856ebc8f2aa3a30`. Its 47 addressable units, including 34 historical, mutable, duplicate or heading-only units omitted from the active body, are mapped individually in the central `lesson-unit-migration.tsv` ledger.
