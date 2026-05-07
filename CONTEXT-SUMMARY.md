# db-mcp-server — Context Summary

## Current state

- Repo: `/opt/iac/Development/cloud-dog-ai/db-mcp-server`
- Current date context for this summary: `2026-05-07`
- Latest completed historical instruction still referenced in this repo: `W28A-512`
- Latest attempted backend sweep: `W28A-88d`
- Latest W28A-88d report: `/opt/iac/Development/cloud-dog-ai/db-mcp-server/working/W28A-88d-REPORT.md`
- Current repo state is **not** at a fresh green backend-test baseline

## What is historically true vs currently true

- `W28A-512` was a real previously completed green baseline covering content/binary fixes and a full regression at that time.
- That historical result should **not** be treated as the current backend status after the later `W28A-88d` sweep.
- The current trustworthy status is the `W28A-88d` evidence in `working/`, which is incomplete and not green.

## Latest trustworthy backend-test status

From `W28A-88d`:

- UT:
  - `working/test-ut.log`
  - Exact summary: `============================= 54 passed in 12.93s ==============================`
- ST:
  - `working/test-st.log`
  - Exact summary: `=================== 5 failed, 11 passed in 495.99s (0:08:15) ===================`
- Targeted API/MCP ST rerun after further harness changes:
  - `working/test-st-targeted-api-mcp.log`
  - Exact summary: `=================== 6 failed, 1 passed in 132.85s (0:02:12) ====================`
- IT:
  - No fresh trustworthy `W28A-88d` IT completion was produced
- AT:
  - Historical `working/w28a-per-project-at.log` exists, but AT was not fully rerun and revalidated after the `W28A-88d` code changes

## Current main blocker

- The dominant local blocker is still restart-heavy local process orchestration during backend system tests.
- Foreground API startup is stable.
- Detached local startup via `server_control.sh` has been intermittently unstable in repeated test restart sequences.
- Some failures were caused by stale listeners / port reuse, and some by detached child startup instability.
- The latest launcher work improved cleanup and narrowed some failures, but did **not** produce a clean full ST pass.

## Latest failure shape worth knowing

From the latest full `working/test-st.log`:

- `tests/system/ST1.2_AccessControlApi/test_access_control_api.py::test_access_control_api_crud_and_audit`
- `tests/system/ST1.4_CatalogApi/test_catalog_api.py::test_catalogue_tools_against_real_mongodb`
- `tests/system/ST1.5_ContentApi/test_content_api.py::test_content_tools_support_all_documented_filter_operators`
- `tests/system/ST1.5_ContentApi/test_content_api.py::test_content_tools_round_trip_binary_fields`
- `tests/system/ST1.7_SearchApi/test_search_api.py::test_v1_7_search_metadata_finds_customer_email_field`

Observed recurring signatures:

- `api failed to start`
- `web failed to start`
- `a2a failed to start`
- `httpx.ConnectError: [Errno 111] Connection refused`
- `Timed out waiting for http://127.0.0.1:8086/health`

## Latest local fixes attempted during W28A-88d

- `tests/conftest.py`
  - Later `--env` files now override earlier env-file values while preserving the original shell environment.
- `tests/env-postgresql`
  - Added real `CLOUD_DOG__CONNECTORS__POSTGRESQL__DEFAULT_URI` and database values actually consumed by `ConnectorManager`.
- `tests/env-mariadb`
  - Added real `CLOUD_DOG__CONNECTORS__MARIADB__DEFAULT_URI` and database values actually consumed by `ConnectorManager`.
- `server_control.sh`
  - Added `/health`-based readiness waiting
  - Added port-based cleanup in `stop`
  - Reworked detached launch handling more than once during the sweep
- `tests/helpers/core_tools_runtime.py`
  - Narrowed restart-heavy MCP/API helper startup to API+MCP instead of always starting all four surfaces
- `tests/system/ST1.2_AccessControlApi/test_access_control_api.py`
  - Narrowed startup to API-only for that test

These changes improved diagnosis and removed some false-negative startup noise, but they did not finish the suite.

## Current modified files from the unfinished W28A-88d work

- `/opt/iac/Development/cloud-dog-ai/db-mcp-server/server_control.sh`
- `/opt/iac/Development/cloud-dog-ai/db-mcp-server/tests/conftest.py`
- `/opt/iac/Development/cloud-dog-ai/db-mcp-server/tests/env-postgresql`
- `/opt/iac/Development/cloud-dog-ai/db-mcp-server/tests/env-mariadb`
- `/opt/iac/Development/cloud-dog-ai/db-mcp-server/tests/helpers/core_tools_runtime.py`
- `/opt/iac/Development/cloud-dog-ai/db-mcp-server/tests/system/ST1.2_AccessControlApi/test_access_control_api.py`
- `/opt/iac/Development/cloud-dog-ai/db-mcp-server/AGENT-LESSONS.md`
- `/opt/iac/Development/cloud-dog-ai/db-mcp-server/working/W28A-88d-REPORT.md`

These changes were not committed or pushed in the last sweep.

## Historical baseline still relevant

The following from `W28A-512` remains useful background, but it is historical:

- content/binary fixes in:
  - `src/servers/mcp/content_tools.py`
  - `src/core/connectors/mongodb/adapter.py`
- requirements additions in:
  - `docs/REQUIREMENTS.md`
- historical green AT and full-regression evidence at that time in:
  - `working/W28A-512-FIX-E2E-GAPS-REPORT.md`

Use that baseline for feature history only, not as the current backend pass/fail claim.

## Important operational constraints

- Do not use SSH
- Do not touch firewall, iptables, Shorewall, Docker networking, or firewall Terraform
- Use `--env tests/env-<TIER>` for tests
- Do not bypass `cloud_dog_config`
- Treat `server_control.sh` as the intended local lifecycle entrypoint, but do not assume it is currently fully reliable under restart-heavy ST patterns

## Recommended next-agent starting point

1. Read `/opt/iac/Development/cloud-dog-ai/db-mcp-server/working/W28A-88d-REPORT.md`
2. Read `/opt/iac/Development/cloud-dog-ai/db-mcp-server/AGENT-LESSONS.md` section `2.6` and `2.7`
3. Read current diffs for:
   - `server_control.sh`
   - `tests/conftest.py`
   - `tests/helpers/core_tools_runtime.py`
   - `tests/system/ST1.2_AccessControlApi/test_access_control_api.py`
4. Do not start from the assumption that the product logic is broken first; re-establish deterministic local process lifecycle before trusting later ST failures
