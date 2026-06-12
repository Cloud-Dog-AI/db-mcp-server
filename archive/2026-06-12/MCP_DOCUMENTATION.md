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
