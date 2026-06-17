---
template-id: T-SCM
template-version: 1.0
applies-to: tests/SCOPE-MAP.md
project: db-mcp-server
doc-last-updated: 2026-06-17T00:00:00Z
doc-git-commit: d064aa17d3a6570cb01e86bbf63e4632b37fb355
doc-git-branch: main
doc-age-policy: 30d
doc-conformance-stamp: 2026-06-17T00:00:00Z
stream-a-lane: W28E-1808A
---

# db-mcp-server — Test scope map

> **Template version:** T-SCM v1.0 — required by PS-REQ-TEST-TRACE §5.
> W28E-1808A Stream-A: source globs mapped to the test IDs (and FR-NNN) that cover them.

## Mapping

| Source glob | Capability (FR) | Test IDs |
|---|---|---|
| `src/core/access_control/**/*.py` | `FR-001`, `FR-002`, `FR-003` | `UT1.2`, `UT1.3`, `UT1.50`, `UT1.51`, `UT1.52`, `ST1.2`, `IT1.1` |
| `src/servers/api/access_control.py` | `FR-003` | `ST1.2`, `IT1.1` |
| `src/servers/api/source_connections.py` | `FR-004` | `UT1.21`, `IT1.11` |
| `src/core/catalog/**/*.py`, `src/core/discovery/**/*.py` | `FR-005` | `UT1.6`, `UT1.20_DiscoveryApi`, `ST1.4`, `IT1.3` |
| `src/servers/api/discovery.py` | `FR-005` | `UT1.20_DiscoveryApi`, `ST1.4` |
| `src/core/content/**/*.py`, `src/servers/mcp/content_tools.py` | `FR-006` | `UT1.7`, `ST1.5`, `IT1.4` |
| `src/core/filters/**/*.py` | `FR-007` | `UT1.5` |
| `src/core/relationships/**/*.py`, `src/servers/mcp/relationship_tools.py` | `FR-008` | `UT1.8`, `IT1.5` |
| `src/core/schema/**/*.py`, `src/servers/api/schema_changes.py` | `FR-009` | `UT1.12`, `UT1.21`, `ST1.6`, `IT1.7` |
| `src/core/search/**/*.py` | `FR-010` | `UT1.9`, `UT1.10`, `ST1.7`, `IT1.6` |
| `src/servers/api/saved_queries.py` | `FR-011` | `IT1.12` |
| `src/core/test_data/**/*.py`, `src/servers/api/test_data.py` | `FR-012` | `fixtures/test_seed_data`, `UT1.22` |
| `src/core/connectors/mongodb/**/*.py` | `FR-013` | `UT1.4`, `UT1.15_MongoConfig`, `ST1.3`, `IT1.2` |
| `src/core/connectors/couchdb/**/*.py` | `FR-014` | `UT1.13`, `ST1.9`, `IT1.8` |
| `src/core/connectors/opensearch/**/*.py` | `FR-015` | `UT1.14`, `ST1.10`, `IT1.9` |
| `src/core/connectors/elasticsearch/**/*.py` | `FR-016` | `UT1.16`, `ST1.12` |
| `src/core/connectors/cassandra/**/*.py` | `FR-017` | `UT1.17`, `ST1.13` |
| `src/core/connectors/{postgresql,mariadb}/**/*.py` | `FR-018` | `UT1.18`, `ST1.14`, `ST1.15` |
| `src/core/connectors/__init__.py` (dispatch) | `FR-019` | `IT1.10` |
| `src/servers/mcp/**/*.py` | `FR-020` | `UT1.20_McpServer` |
| `src/servers/a2a/**/*.py` | `FR-021` | `UT1.15_A2AServer` |
| `src/servers/web/**/*.py`, `ui/dist/**` | `FR-022` | `UT1.11`, `ST1.8`, `AT_WEBUI_E2E` |
| `src/common/runtime.py`, config provenance | `FR-023` | `UT1.1` |
| job lifecycle wiring (`cloud_dog_jobs`) | `FR-024` | `UT1.19` |
| `src/servers/*/` health endpoints | `FR-025` | `ST1.1` |
| `pyproject.toml`, package layout | `FR-026` | `QT1.1` |
| deployed-contract surface (`dbmcpserver0`) | `FR-027` | `e2e/test_w28a746_live_preprod_contract`, `smoke/test_w28a746_b_method_idam` |
| `src/core/audit/**/*.py`, `src/servers/mcp/audit_tools.py` | `FR-028` | `ST1.2` |

## Notes

- Helper/fixture modules under `tests/helpers/`, `tests/fixtures/` are excluded from the
  PS-REQ-TEST-TRACE marker-enforcement file scan (per `scripts/check-req-test-traceability.sh`
  §8) but `tests/fixtures/test_seed_data.py` still carries its `FR-012` binding for coverage.
- Connector real-runtime overlays live under `tests/env-<backend>/` and are layered with the
  tier env (`tests/env-ST`, `tests/env-IT`) via the `--env` plugin.

## Cross-references

- Platform standard: PS-REQ-TEST-TRACE v1.0 §5
- Tier policy: standards/TEST-POLICY-SCOPED.md
- Requirements: [../docs/REQUIREMENTS.md](../docs/REQUIREMENTS.md)
- Coverage map: [../docs/TESTS.md](../docs/TESTS.md) §2
