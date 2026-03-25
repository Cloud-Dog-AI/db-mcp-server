# W28A-274-J — db-mcp-server WebUI Report

## Verdict
PASS

## Scope
- Backend: `/opt/iac/Development/cloud-dog-ai/db-mcp-server`
- Monorepo app: `/opt/iac/Development/cloud-dog-ai/cloud-dog-ai-ui-monorepo/apps/db-mcp`

## Delivered
- PS-30 web surface serving built SPA assets from `ui/dist` with `/runtime-config.js` and browser-history route support.
- Same-origin `/api` and `/mcp` proxying from the web surface to the dedicated API and MCP servers.
- New db-mcp monorepo app using shared `@cloud-dog/auth`, `@cloud-dog/shell`, `@cloud-dog/tokens`, and `@cloud-dog/ui` packages.
- Implemented pages for login, dashboard, profiles, users, catalogue, entity detail, data browser, search, relationships, schema changes, audit, and settings.
- Visual filter builder with JSON preview and live query execution.
- Playwright E2E + axe accessibility coverage.
- Backend QT/UT/ST coverage for WebUI serving.

## Key fixes during validation
1. Same-origin web proxy paths were initially wrong.
   - `/api` and `/mcp` were being stripped incorrectly before upstream forwarding.
   - Fixed in `src/servers/web/app.py` by preserving the full routed path for both proxy surfaces.
2. Deep-link login recovery was incomplete.
   - Direct navigation to routes like `/catalogue/...` and `/data/...` bounced users to `/login` and then back to `/`.
   - Fixed in `apps/db-mcp/src/routes/App.tsx` with pending-path session storage and post-login resume.
3. One real accessibility defect existed.
   - The destructive action styling on the filter builder failed WCAG AA contrast.
   - Fixed in `apps/db-mcp/src/styles.css` by darkening the app-local destructive token.
4. One UI navigation ambiguity existed.
   - The sidebar `Schema` item conflicted with the catalogue row `Schema` action in Playwright.
   - Fixed by renaming the sidebar item to `Schema Planner` while retaining route `/schema`.
5. Full Playwright and backend ST cannot be run in parallel on this host.
   - Both workflows manage the same real ports `8086-8089`.
   - Parallel execution caused real `ERR_CONNECTION_REFUSED` failures when one workflow stopped shared services.
   - Final validation was rerun serially.

## Primary files changed
### Backend
- `src/servers/web/app.py`
- `src/servers/web/ui_spa.py`
- `scripts/sync-ui-dist.sh`
- `scripts/prepare_ui_test_env.py`
- `tests/env-ST-WEBUI`
- `tests/unit/UT1.11_WebUiServing/test_web_ui_serving.py`
- `tests/system/ST1.1_ServerStartup/test_server_startup.py`
- `tests/system/ST1.2_AccessControlApi/test_access_control_api.py`
- `tests/system/ST1.8_WebUiServing/test_web_ui_system_serving.py`
- `tests/helpers/core_tools_runtime.py`
- `docs/TESTS.md`
- `CONTEXT-SUMMARY.md`

### Frontend
- `apps/db-mcp/package.json`
- `apps/db-mcp/vite.config.ts`
- `apps/db-mcp/public/runtime-config.js`
- `apps/db-mcp/public/runtime-config.example.js`
- `apps/db-mcp/index.html`
- `apps/db-mcp/eslint.config.js`
- `apps/db-mcp/tailwind.config.ts`
- `apps/db-mcp/src/main.tsx`
- `apps/db-mcp/src/styles.css`
- `apps/db-mcp/src/routes/App.tsx`
- `apps/db-mcp/src/routes/manifest.ts`
- `apps/db-mcp/src/state/AppState.tsx`
- `apps/db-mcp/src/lib/api.ts`
- `apps/db-mcp/src/lib/filter.ts`
- `apps/db-mcp/src/lib/types.ts`
- `apps/db-mcp/src/components/ProfileSelect.tsx`
- `apps/db-mcp/src/components/JsonPanel.tsx`
- `apps/db-mcp/src/components/FilterBuilder.tsx`
- `apps/db-mcp/src/views/*.tsx`
- `apps/db-mcp/playwright.config.ts`
- `apps/db-mcp/tests/fixtures.ts`
- `apps/db-mcp/tests/a11y.spec.ts`
- `apps/db-mcp/tests/e2e/auth.spec.ts`
- `apps/db-mcp/tests/e2e/discovery.spec.ts`

## Commands run
```bash
cd /opt/iac/Development/cloud-dog-ai/cloud-dog-ai-ui-monorepo
npm --prefix apps/db-mcp run typecheck
npm --prefix apps/db-mcp run lint
npm --prefix apps/db-mcp run build

cd /opt/iac/Development/cloud-dog-ai/db-mcp-server
venv/bin/python -m pytest tests/quality tests/unit --env tests/env-QT --env tests/env-UT -v --tb=short
./server_control.sh --env tests/env-ST-WEBUI stop all >/dev/null 2>&1 || true
venv/bin/python -m pytest tests/system --env tests/env-ST-WEBUI -v --tb=short

cd /opt/iac/Development/cloud-dog-ai/db-mcp-server
./server_control.sh --env tests/env-ST-WEBUI stop all >/dev/null 2>&1 || true
cd /opt/iac/Development/cloud-dog-ai/cloud-dog-ai-ui-monorepo/apps/db-mcp
npm run e2e -- --reporter=line
```

## Results
- Frontend typecheck: PASS
- Frontend lint: PASS
- Frontend build: PASS
- Frontend Playwright + axe: `9 passed in 31.0s`
- Backend QT + UT: `24 passed in 3.62s`
- Backend ST: `8 passed in 506.53s`

## Evidence
- Typecheck: `working/w28a-274j-ui-typecheck.log`
- Lint: `working/w28a-274j-ui-lint.log`
- Build: `working/w28a-274j-ui-build.log`
- Playwright + axe: `working/w28a-274j-ui-e2e.log`
- QT + UT: `working/w28a-274j-qt-ut.log`
- ST: `working/w28a-274j-st.log`

## Compliance notes
- Only `apps/db-mcp/` and shared package usage were touched on the monorepo side; no other app sources were modified.
- Validation used real local services and real Playwright browser execution.
- No stubs, skips, or allowlist padding were introduced.
