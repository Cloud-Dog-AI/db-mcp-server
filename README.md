# db-mcp-server

`db-mcp-server` is the planned Cloud-Dog AI control plane for NoSQL and search database discovery, structured content operations, schema change workflows, relationship management, and discovery indexing across MongoDB, CouchDB, OpenSearch, Elasticsearch, and Cassandra.

## Quick Start

### Current status
This repository is a Phase 1 planning skeleton only. The project structure, requirements, architecture, and follow-up backlog are in place. Runtime servers and connector implementations are not yet implemented.

### Prerequisites
- Python 3.10+
- Docker
- Access to `/opt/iac/Development/cloud-dog-ai/env-vault`

### Install
```bash
cd /opt/iac/Development/cloud-dog-ai/db-mcp-server
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -e ".[dev]" --index-url https://pypi.cloud-dog.net/simple/
```

### Planned ports
- API: `8086`
- Web: `8087`
- MCP: `8088`
- A2A: `8089`

Port allocation verified against [`AGENT-DISPATCH-TABLE.md`](../cloud-dog-ai-platform-standards/AGENT-DISPATCH-TABLE.md).

### Next implementation steps
- Requirements: [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md)
- Architecture: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- Backlog: [docs/BACKLOG.md](docs/BACKLOG.md)

## Architecture Overview
The planned runtime follows the standard four-server Cloud-Dog pattern with a shared domain core, background job execution, profile-based connector adapters, and a metadata/audit store. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## API Interfaces
| Interface | Purpose | Reference |
|---|---|---|
| REST API | Admin, catalogue, schema, content, jobs | [docs/API-REFERENCE.md](docs/API-REFERENCE.md) |
| MCP | Tool-driven discovery and operations | [docs/API-REFERENCE.md](docs/API-REFERENCE.md#mcp-tool-families) |
| A2A | Agent-to-agent orchestration | [docs/API-REFERENCE.md](docs/API-REFERENCE.md#a2a-surface) |
| Web UI | Admin and review workflows | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |

## Configuration
Configuration precedence is `os.environ -> --env file -> config.yaml -> defaults.yaml` with Vault-backed resolution via `cloud_dog_config`. See [docs/ENV-REFERENCE.md](docs/ENV-REFERENCE.md) and [docs/PREPROD.md](docs/PREPROD.md).

## Platform Packages
| Package | Purpose |
|---|---|
| `cloud-dog-config` | Layered configuration and Vault resolution |
| `cloud-dog-logging` | Structured logging and audit controls |
| `cloud-dog-api-kit` | Standard API/web server bootstrap |
| `cloud-dog-idam` | Users, groups, API keys, RBAC |
| `cloud-dog-jobs` | Indexing and schema-change job orchestration |
| `cloud-dog-db` | Metadata store and audit persistence |

## Documentation Links
| Document | Link |
|---|---|
| Requirements | [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md) |
| Architecture | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| Tests | [docs/TESTS.md](docs/TESTS.md) |
| Build | [docs/BUILD.md](docs/BUILD.md) |
| Deploy | [docs/DEPLOY.md](docs/DEPLOY.md) |
| Preprod | [docs/PREPROD.md](docs/PREPROD.md) |
| API Reference | [docs/API-REFERENCE.md](docs/API-REFERENCE.md) |
| Env Reference | [docs/ENV-REFERENCE.md](docs/ENV-REFERENCE.md) |
| Backlog | [docs/BACKLOG.md](docs/BACKLOG.md) |
| Context Summary | [CONTEXT-SUMMARY.md](CONTEXT-SUMMARY.md) |
| Rules | [RULES.md](RULES.md) |

## Licence
Apache 2.0 — Copyright (c) 2026 Cloud-Dog, Viewdeck Engineering Limited
