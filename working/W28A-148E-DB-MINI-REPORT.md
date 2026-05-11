# W28A-148E DB Mini Report

Date: 2026-05-11

## Classification

- Root cause fixed: `/config` no longer fails JSON serialization on non-plain mapping values, and `/jobs/queue/status` now exists for the WebUI jobs dashboard.
- Root cause fixed in UI auth path: API-key validation now falls back from `/api/v1/ping` to `/webapi/v1/ping` and sends both bearer and `x-api-key` headers.
- Harness evidence fixed: Playwright failures now retain trace/video, a redacted screenshot, current spec metadata, and last console/network errors.

## Focused Results

- `npx --no-install playwright test tests/e2e/auth.spec.ts tests/e2e/sections.spec.ts -g "E2E-DBMCP-001|E2E-DBMCP-119B|E2E-DBMCP-002" --reporter=list`: `3 passed (42.8s)`.
- `venv/bin/python -m pytest tests/unit/UT1.1_ConfigLoading/test_config_loading.py tests/unit/UT1.11_WebUiServing/test_web_ui_serving.py --env tests/env-ST-WEBUI -q`: `7 passed`.

## Full Shard

- `npx --no-install playwright test --reporter=list`: `12 passed (1.1m)`.
- Full DB service shard is green.
