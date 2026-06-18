---
template-id: T-AUD
template-version: 1.0
applies-to: docs/AUDIT-EVENTS.md
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

# Audit Events Catalogue

Project: db-mcp-server

| event_type | action | NIST category | Trigger | severity | Example JSON |
|---|---|---|---|---|---|
| tool.call | execute | Object Access | Connector execution, schema inspection, search, or other MCP/API tool call | INFO | {"event_type":"tool.call","action":"execute","outcome":"success"} |
| relationship.create | create | Object Access | Create a relationship definition between discovered objects | INFO | {"event_type":"relationship.create","action":"create","outcome":"success"} |
| relationship.update | update | Object Access | Update an existing relationship definition | INFO | {"event_type":"relationship.update","action":"update","outcome":"success"} |
| relationship.delete | delete | Object Access | Delete an existing relationship definition | INFO | {"event_type":"relationship.delete","action":"delete","outcome":"success"} |
| access_rule.create | create | Security Management | Create an access-control rule or entitlement | INFO | {"event_type":"access_rule.create","action":"create","outcome":"success"} |
| security.api_key_validate | api_key_validate | Authentication | Validate API key or other ingress credentials | ERROR | {"event_type":"security.api_key_validate","action":"api_key_validate","outcome":"denied"} |
| admin.schema_approve | schema_approve | Privileged Use | Privileged approval or application of a schema change | WARNING | {"event_type":"admin.schema_approve","action":"schema_approve","outcome":"success"} |
