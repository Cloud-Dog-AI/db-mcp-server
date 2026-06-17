---
template-id: T-TSS
template-version: 1.0
project: db-mcp-server
doc-last-updated: 2026-06-17T11:09:50.028924+00:00
doc-git-commit: d064aa17d3a6570cb01e86bbf63e4632b37fb355
doc-git-branch: W28C-1714-100pct-fix
doc-age-policy: 30d
doc-conformance-stamp: 2026-06-17T11:09:50.028924+00:00
---

# db-mcp-server — TEST-STATUS

> **Template version:** T-TSS v1.0 — overwritten by `scripts/update-test-state.py`. Do not hand-edit.

## 1. Latest run

- **Run timestamp:** 2026-06-17T11:09:50.028924+00:00
- **Commit:** `d064aa17d3a6570cb01e86bbf63e4632b37fb355` (`W28C-1714-100pct-fix`)
- **Totals:** 17 tests | 17 passed | 0 failed | 0 skipped

## 2. Per-test status

| Test ID | Tier | Status | Last run | Commit | Known issue |
|---|---|---|---|---|---|
| `tests.unit.UT1.22_TestDataSeed.test_test_data_seed_api::test_test_data_seed_is_forbidden_outside_allowed_runtime_profiles` | UT/ST/IT | pass | 2026-06-17 | `d064aa17` | |
| `tests.unit.UT1.22_TestDataSeed.test_test_data_seed_api::test_test_data_seed_rejects_unknown_connection` | UT/ST/IT | pass | 2026-06-17 | `d064aa17` | |
| `tests.unit.UT1.22_TestDataSeed.test_test_data_seed_api::test_test_data_seed_rejects_unknown_dataset` | UT/ST/IT | pass | 2026-06-17 | `d064aa17` | |
| `tests.unit.UT1.22_TestDataSeed.test_test_data_seed_api::test_test_data_seed_runs_sqlite_fixture_when_runtime_profile_is_allowed` | UT/ST/IT | pass | 2026-06-17 | `d064aa17` | |
| `tests.unit.UT1.52_FlatLoginContract.test_flat_login_contract::test_anon_write_is_unauthorized` | UT/ST/IT | pass | 2026-06-17 | `d064aa17` | |
| `tests.unit.UT1.52_FlatLoginContract.test_flat_login_contract::test_bad_password_is_unauthorized` | UT/ST/IT | pass | 2026-06-17 | `d064aa17` | |
| `tests.unit.UT1.52_FlatLoginContract.test_flat_login_contract::test_mcp_proxy_forwards_session_role_key[creds0-admin]` | UT/ST/IT | pass | 2026-06-17 | `d064aa17` | |
| `tests.unit.UT1.52_FlatLoginContract.test_flat_login_contract::test_mcp_proxy_forwards_session_role_key[creds1-read-write]` | UT/ST/IT | pass | 2026-06-17 | `d064aa17` | |
| `tests.unit.UT1.52_FlatLoginContract.test_flat_login_contract::test_mcp_proxy_forwards_session_role_key[creds2-read-only]` | UT/ST/IT | pass | 2026-06-17 | `d064aa17` | |
| `tests.unit.UT1.52_FlatLoginContract.test_flat_login_contract::test_missing_credentials_is_bad_request` | UT/ST/IT | pass | 2026-06-17 | `d064aa17` | |
| `tests.unit.UT1.52_FlatLoginContract.test_flat_login_contract::test_read_only_can_read` | UT/ST/IT | pass | 2026-06-17 | `d064aa17` | |
| `tests.unit.UT1.52_FlatLoginContract.test_flat_login_contract::test_read_only_write_is_forbidden` | UT/ST/IT | pass | 2026-06-17 | `d064aa17` | |
| `tests.unit.UT1.52_FlatLoginContract.test_flat_login_contract::test_read_write_can_write_and_forwards_role_principal` | UT/ST/IT | pass | 2026-06-17 | `d064aa17` | |
| `tests.unit.UT1.52_FlatLoginContract.test_flat_login_contract::test_runtime_config_advertises_cookie_not_api_key` | UT/ST/IT | pass | 2026-06-17 | `d064aa17` | |
| `tests.unit.UT1.52_FlatLoginContract.test_flat_login_contract::test_three_flat_roles_login_by_username_password[creds0-admin]` | UT/ST/IT | pass | 2026-06-17 | `d064aa17` | |
| `tests.unit.UT1.52_FlatLoginContract.test_flat_login_contract::test_three_flat_roles_login_by_username_password[creds1-read-write]` | UT/ST/IT | pass | 2026-06-17 | `d064aa17` | |
| `tests.unit.UT1.52_FlatLoginContract.test_flat_login_contract::test_three_flat_roles_login_by_username_password[creds2-read-only]` | UT/ST/IT | pass | 2026-06-17 | `d064aa17` | |

## 3. Failures (detail)

_None._
