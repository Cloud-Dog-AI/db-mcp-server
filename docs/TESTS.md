# db-mcp-server — Tests

## Status
No test implementations exist yet. This document defines the planned test structure and expected coverage areas for follow-up implementation work.

## Planned test tiers
### QT — Quality
- Project structure and documentation compliance
- Config/env precedence checks
- Dependency and marker registration checks

### UT — Unit
- Structured filter parsing and validation
- Connector contract compliance using unit doubles only
- RBAC and masking policy logic
- Schema plan builder logic
- Relationship inference heuristics

### ST — System
- Local server startup and health endpoints
- Metadata store initialisation
- Job worker lifecycle
- Connector validation against local real systems where practical

### IT — Integration
- Real API/MCP/A2A flows against real MongoDB, CouchDB, OpenSearch, Elasticsearch, and Cassandra targets
- Profile CRUD and validation
- Discovery and schema introspection
- Structured content reads and writes
- Index refresh and relationship workflows

### AT — Application
- End-to-end operator scenarios through real server surfaces
- Profile onboarding -> discovery -> schema plan -> approval -> execution -> audit
- Cross-profile discovery search and relationship review flows

## Env file plan
- `tests/env-QT`
- `tests/env-UT`
- `tests/env-ST`
- `tests/env-IT`
- `tests/env-AT`

## Initial numbering reservation
- QT1.x — quality and compliance
- UT1.x — filter, policy, planning, connector contracts
- ST1.x — startup, health, worker, local connector checks
- IT1.x — profile/discovery/schema/content/search integration
- AT1.x — operator end-to-end scenarios
