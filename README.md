# db-mcp-server

`db-mcp-server` is the Cloud-Dog AI control plane for structured discovery and operations across database and search backends. The current tree includes the four runtime surfaces, Mongo-backed discovery/search flows, the PS-30 WebUI, and canonical cross-backend test-data/docker environments for MongoDB, CouchDB, OpenSearch, Elasticsearch, and Cassandra.

## Quick Start

### Prerequisites
- Python 3.12+
- Access to `/opt/iac/Development/cloud-dog-ai/env-vault` for Vault-backed settings when needed

### Install
```bash
cd /opt/iac/Development/cloud-dog-ai/db-mcp-server
python3 -m venv venv
. venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"
```

### Start all four servers
```bash
set -a; source /opt/iac/Development/cloud-dog-ai/env-vault; set +a
./server_control.sh --env tests/env-ST start all
```

### Health checks
```bash
curl -s http://127.0.0.1:8086/health
curl -s http://127.0.0.1:8087/health
curl -s http://127.0.0.1:8088/health
curl -s http://127.0.0.1:8089/health
```

### Stop all servers
```bash
./server_control.sh --env tests/env-ST stop all
```

### Seed canonical test databases
```bash
./scripts/seed-test-data.sh mongodb
venv/bin/python -m pytest tests/fixtures/test_seed_data.py --env tests/env-mongodb -v --tb=short
```

## Runtime Surfaces
- API: `8086`
- Web: `8087`
- MCP: `8088`
- A2A: `8089`

## Implemented In This Phase
- Layered config loading via `cloud_dog_config`
- Structured logging via `cloud_dog_logging`
- FastAPI server bootstrap via `cloud_dog_api_kit`
- API-key authentication via `cloud_dog_idam`
- Memory-backed job queue wiring via `cloud_dog_jobs`
- Metadata and audit database health probes via `cloud_dog_db`
- `server_control.sh` process management for all four server surfaces
- Canonical e-commerce test dataset plus per-backend seed modules
- Docker Compose test environments for MongoDB, CouchDB, OpenSearch, Elasticsearch, and Cassandra
- PS-30 WebUI served from `ui/dist`

## Implemented Connectors
All 7 connectors are fully implemented with adapter code, system tests, and integration tests:
- **MongoDB** — Full adapter (489 lines), system test ST1.8
- **CouchDB** — Full adapter (853 lines), system test ST1.9
- **OpenSearch** — Full adapter (615 lines), system test ST1.10
- **Elasticsearch** — Full adapter (843 lines), system test ST1.12
- **Cassandra** — Full adapter (771 lines), system test ST1.13
- **PostgreSQL** — Relational adapter via shared module, system test ST1.14
- **MariaDB** — Relational adapter via shared module, system test ST1.15

## AT Coverage
Playwright E2E test suite (AT_WEBUI_E2E) covers: login, dashboard, profile CRUD, data browser, schema, users, groups, API keys, RBAC, audit, catalogue, search, relationships, entity detail.

## Outstanding
- Real queue workers and job handlers beyond current inline/memory-backed execution
- PS-78 file lifecycle API (W28A-883)

## Documentation
- [Requirements](docs/REQUIREMENTS.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Tests](docs/TESTS.md)
- [Build](docs/BUILD.md)
- [Deploy](docs/DEPLOY.md)
- [Preprod](docs/PREPROD.md)
- [API Reference](docs/API-REFERENCE.md)
- [Env Reference](docs/ENV-REFERENCE.md)
