# db-mcp-server — Local Agent Lessons

> **Common authority:** Read [Platform Rules](../cloud-dog-ai-platform-standards/RULES.md) and [Platform Lessons](../cloud-dog-ai-platform-standards/AGENT-LESSONS.md) first. This file adds local facts only; it cannot weaken common policy.

Platform Standards owns common policy. This overlay owns database-management facts.

- Use the configured database abstraction and migration path; do not add direct
  backend clients or bypass scoped database authorisation.
- Prove real CRUD/migration/query behaviour and no-auth/wrong-role/forbidden-write
  negatives on every applicable API, MCP, A2A and WebUI surface.
- Resolve database names, hosts, schemas and credentials from current config only.
- A configured provider is not an implemented connector: prove adapter implementation, profile validation and a real operation before claiming support.
- Keep metadata discovery indexing distinct from content search; run full/incremental index work through the common job lifecycle and preserve provider errors at the service boundary.
- Read roles from current configuration and prove each permission/negative path; persistent job claims require restart and authoritative-store proof.

Evidence: migration/query ledger; auth matrix; audit/persistence readback; local and
final-PREPROD Playwright proof.

- **Listener ports.** API `8086`, Web `8087`, MCP `8088` and A2A `8089` are this service's default listener allocation. Read current `defaults.yaml` and the authorised environment overlay before use; never use the retired bootstrap table or guess an override.
