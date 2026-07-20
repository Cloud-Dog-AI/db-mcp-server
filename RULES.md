# db-mcp-server — Local Rules

## Common contract — binding

Read [the platform RULES](../cloud-dog-ai-platform-standards/RULES.md) and
`AGENT-LESSONS.md` in full before work. Central data, platform-package and delivery
controls apply; this file adds database-service constraints.

## Local rules

- API, Web, MCP and A2A share catalogue, schema, content, relationship, search and
  access-control core. Prove a changed shared contract through every applicable
  adapter and negative permission path.
- Provider availability, credentials, profiles and permissions come from current
  authorised configuration. A configured provider is not a supported connector:
  prove adapter validation and real operations before claiming support.
- Keep discovery indexing distinct from content search; long full/incremental work
  uses the common durable job lifecycle with restart/recovery proof.
- Translate provider failures into the service’s stable error contract. Destructive
  operations require their explicit role, approval and target-aware audit trail.
- Editable UI and browser coverage belong in the paired monorepo app; the service
  ships only the exact synchronised distribution.

Historical connector counts, ports and incident commands are retired to Git history.
