# Tests

## Service Scope
Multi-backend database and search control plane for discovery, CRUD, relationships, search indexing, schema planning, and PS-30 Web UI administration.

## Test Inventory
| Tier | Present | Notes |
|------|---------|-------|
| `quality` | Yes | Repository contains the `quality` test tier. |
| `unit` | Yes | Repository contains the `unit` test tier. |
| `system` | Yes | Repository contains the `system` test tier. |
| `integration` | Yes | Repository contains the `integration` test tier. |
| `application` | Yes | Repository contains the `application` test tier. |
| `fixtures` | Yes | Repository contains the `fixtures` test tier. |
| `helpers` | Yes | Repository contains the `helpers` test tier. |

## Current Evidence Model
- The repository keeps execution evidence in repo-local working reports and rerunnable pytest suites.
- Before release, rerun the relevant `QT`, `UT`, `ST`, `IT`, and `AT` tiers against the intended environment overlays.
- This document records the current catalogue rather than claiming a release verdict.

## Standard Commands
```bash
python3 -m pytest tests/quality --env tests/env-QT -q
python3 -m pytest tests/unit --env tests/env-UT -q
python3 -m pytest tests/system --env tests/env-ST -q
python3 -m pytest tests/integration --env tests/env-IT -q
python3 -m pytest tests/application --env tests/env-AT -q
python3 -m pytest tests/system/ST1.14_PostgreSQLConnector --env tests/env-ST --env tests/env-postgresql -q
python3 -m pytest tests/system/ST1.15_MariaDBConnector --env tests/env-ST --env tests/env-mariadb -q
```

## Notes
- Top-level test directories present: `__pycache__`, `application`, `fixtures`, `helpers`, `integration`, `quality`, `system`, `unit`.
- Connector-specific real-runtime overlays are published for PostgreSQL (`tests/env-postgresql`) and MariaDB (`tests/env-mariadb`) and rely on `cloud_dog_config`/Vault resolution at runtime.
