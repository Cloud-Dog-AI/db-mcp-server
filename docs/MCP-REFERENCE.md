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
doc-last-updated: 2026-06-12
doc-git-commit: ee5979008dace594f92b45315bdf687fb1aa00df
doc-git-branch: main
doc-source-shas: []
doc-age-policy: 90d
doc-conformance-stamp: 2026-06-12T12:00:00Z
---

# db-mcp-server — MCP-REFERENCE

> **Template version:** T-MCP v1.0 — MCP tool surface (JSON-RPC 2.0 at `/mcp`).

## 1. Auth model
MCP auth mode (`api_key` typically); header form; how RBAC maps from API key to MCP tool visibility.

## 2. Tools

**You MUST include:** every tool exposed by `tools/list`. One section per tool.

### 2.1 `<tool_name>`
- **Description:** <one line>
- **RBAC:** roles allowed (admin / read-write / read-only / ...)
- **Input schema:**
  ```json
  { "type": "object", "properties": { ... } }
  ```
- **Output schema:**
  ```json
  { "type": "object", "properties": { ... } }
  ```
- **Errors:** <typed error catalogue>
- **Example call:**
  ```bash
  curl -X POST https://<host>/mcp \
    -H "Accept: application/json, text/event-stream" \
    -H "X-API-Key: ${API_KEY}" \
    -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"<tool_name>","arguments":{...}},"id":1}'
  ```

## 3. Cross-references
- [API-REFERENCE.md](API-REFERENCE.md)
- [A2A-REFERENCE.md](A2A-REFERENCE.md)
- PS-72-mcp-a2a-webui.md

## 4. Project-specific notes



<!-- W28C-1710a recovery: full content from archive/2026-06-12/MCP_DOCUMENTATION.md (archived sha256=4b3e128ca32d, 88 lines) -->

## Recovered domain content — `archive/2026-06-12/MCP_DOCUMENTATION.md` (88 lines)

_This section carries forward the full content of the archived predecessor doc verbatim. Topic checklist + SHA256 chain in `cloud-dog-ai-platform-standards/working/evidence/W28C-1710a/per-doc/db-mcp-server/MCP_DOCUMENTATION.md.topics.tsv`. Archive contents are unchanged (sha256 stable)._

# MCP Server Documentation

## Transport
Primary transport: Streamable HTTP at `/mcp` unless the service documents an alternative mode in its runtime configuration.

## Authentication
Use `Authorization: Bearer <your-api-key>` for API, MCP, and A2A requests; web access uses the configured admin login flow.

## Verification Basis
- Source files reviewed: `start_a2a_server.py`, `start_api_server.py`, `start_mcp_server.py`, `start_web_server.py`
- Tool inventory size: 46

## Tools
| Tool | Notes |
|------|-------|
| `_documents` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `api_keys.create` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `api_keys.list` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `api_keys.revoke` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `audit.get_event` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `audit.list_events` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `catalog.get_entity` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `catalog.list_entities` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `catalog.list_namespaces` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `catalog.search` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `data.count` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `data.create` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `data.delete` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `data.exists` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `data.read` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `data.update` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `groups.create` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `groups.list` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `index.rebuild` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `index.status` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `index.sync_entity` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `index.sync_profile` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `profiles.create` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `profiles.delete` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `profiles.get` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `profiles.list` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `profiles.update` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `relationship.create` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `relationship.delete` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `relationship.get` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `relationship.infer` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `relationship.list` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `relationship.update` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `schema.change.apply` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `schema.change.history` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `schema.change.plan` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `schema.describe_entity` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `schema.describe_fields` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `schema.list_indexes` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `schema.sample_shapes` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `search.content` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `search.explain_match` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `search.metadata` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `search.related` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `users.create` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `users.list` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |

## Example Call
```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "method": "tools/list",
  "params": {}
}
```

## Example Response
```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "result": {
    "tools": [
      {
        "name": "tool_name",
        "description": "What the tool does",
        "inputSchema": {"type": "object"}
      }
    ]
  }
}
```
