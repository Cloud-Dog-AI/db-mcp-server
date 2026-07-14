---
template-id: T-TSS
template-version: 1.0
project: db-mcp
doc-last-updated: 2026-07-14T21:20:17.869Z
doc-git-commit: 39cbed348c00813df55639c41aaf70ee687965a3
doc-git-branch: main
doc-age-policy: 30d
doc-conformance-stamp: 2026-07-14T21:20:17.869Z
---

# db-mcp — TEST-STATUS

> **Template version:** T-TSS v1.0 — overwritten by `scripts/update-test-state.py`. Do not hand-edit.

## 1. Latest run

- **Run timestamp:** 2026-07-14T21:20:17.869Z
- **Commit:** `39cbed348c00813df55639c41aaf70ee687965a3` (`main`)
- **Runtime:** N/A (Node/Playwright)
- **Lane:** `W28E-1882`
- **Environment:** `deployed preprod; approved runtime/Vault credentials; service E2E_BASE_URL`
- **Command:** `bash /opt/iac/Development/cloud-dog-ai/tmp/W28E-1882/run-dbmcp.sh FINAL`
- **Evidence:** `W28E-1882-FINAL-PROOF-R2:working/evidence/W28E-1882/current/raw/db-mcp/db-mcp.FINAL.junit.xml`
- **Totals:** 140 tests | 140 passed | 0 failed | 0 errors | 0 skipped

## 2. Per-test status

| Test ID | Tier | Status | Last run | Commit | Known issue |
|---|---|---|---|---|---|
| `e2e/auth.spec.ts::E2E-DBMCP-001 sign-in reaches dashboard and settings` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/auth.spec.ts::E2E-DBMCP-119B renders settings, API docs, MCP tools, and jobs evidence` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/connectors.spec.ts::E2E-DBMCP-100 cassandra connector supports catalogue, schema, data masking, and indexed search` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/connectors.spec.ts::E2E-DBMCP-100 couchdb connector supports catalogue, schema, data masking, and indexed search` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/connectors.spec.ts::E2E-DBMCP-100 elasticsearch connector supports catalogue, schema, data masking, and indexed search` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/connectors.spec.ts::E2E-DBMCP-100 mariadb connector supports catalogue, schema, data masking, and indexed search` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/connectors.spec.ts::E2E-DBMCP-100 mongodb connector supports catalogue, schema, data masking, and indexed search` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/connectors.spec.ts::E2E-DBMCP-100 opensearch connector supports catalogue, schema, data masking, and indexed search` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/connectors.spec.ts::E2E-DBMCP-100 postgresql connector supports catalogue, schema, data masking, and indexed search` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/preprod-deploy-smoke.spec.ts::PS-PREPROD-DEPLOY-SMOKE: db-mcp-server target-service smoke › PDS-002 health and version return 200` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/preprod-deploy-smoke.spec.ts::PS-PREPROD-DEPLOY-SMOKE: db-mcp-server target-service smoke › PDS-003 runtime-config + main assets + index load without 404/500` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/preprod-deploy-smoke.spec.ts::PS-PREPROD-DEPLOY-SMOKE: db-mcp-server target-service smoke › PDS-004 login page renders the shared login form (no blank/pageerror)` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/preprod-deploy-smoke.spec.ts::PS-PREPROD-DEPLOY-SMOKE: db-mcp-server target-service smoke › PDS-005 login alias /ui/login resolves without 404/5xx` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/preprod-deploy-smoke.spec.ts::PS-PREPROD-DEPLOY-SMOKE: db-mcp-server target-service smoke › PDS-006 bad credentials fail visibly without crashing` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/preprod-deploy-smoke.spec.ts::PS-PREPROD-DEPLOY-SMOKE: db-mcp-server target-service smoke › PDS-007 valid login materialises the principal via /auth/me` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/preprod-deploy-smoke.spec.ts::PS-PREPROD-DEPLOY-SMOKE: db-mcp-server target-service smoke › PDS-008 authenticated shell renders top bar, nav and account menu` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/preprod-deploy-smoke.spec.ts::PS-PREPROD-DEPLOY-SMOKE: db-mcp-server target-service smoke › PDS-009 canonical common pages render via hard navigation (no blank/pageerror)` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/preprod-deploy-smoke.spec.ts::PS-PREPROD-DEPLOY-SMOKE: db-mcp-server target-service smoke › PDS-010 service pages render via hard navigation — the crash-class guard` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/preprod-deploy-smoke.spec.ts::PS-PREPROD-DEPLOY-SMOKE: db-mcp-server target-service smoke › PDS-011 anonymous + wrong-target access does not leak protected content` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/preprod-deploy-smoke.spec.ts::PS-PREPROD-DEPLOY-SMOKE: db-mcp-server target-service smoke › PDS-012 browser cleanliness across the full journey` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/preprod-deploy-smoke.spec.ts::PS-PREPROD-DEPLOY-SMOKE: db-mcp-server target-service smoke › PDS-013 logout returns to the login gate` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/rbac.spec.ts::E2E-DBMCP-200 role RBAC grants and denials are enforced and audited across tool families` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/sections.spec.ts::E2E-DBMCP-002 profile CRUD works from the WebUI against the live service` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/sections.spec.ts::E2E-DBMCP-003 catalogue, search, and relationships › catalogue, entity detail, data browser, search, and relationships work with a real connector profile` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-230b-forensic.spec.ts::W28A-230B Forensic Evidence › A2A — A2A Console labels` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-230b-forensic.spec.ts::W28A-230B Forensic Evidence › AUD — Audit labels` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-230b-forensic.spec.ts::W28A-230B Forensic Evidence › CAT — Catalogue labels` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-230b-forensic.spec.ts::W28A-230B Forensic Evidence › DASH — Dashboard labels` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-230b-forensic.spec.ts::W28A-230B Forensic Evidence › DBR — Data Browser labels` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-230b-forensic.spec.ts::W28A-230B Forensic Evidence › DOC — API Docs labels` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-230b-forensic.spec.ts::W28A-230B Forensic Evidence › ENT — Entity Detail labels` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-230b-forensic.spec.ts::W28A-230B Forensic Evidence › GRP — Groups labels` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-230b-forensic.spec.ts::W28A-230B Forensic Evidence › JOB — Jobs labels` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-230b-forensic.spec.ts::W28A-230B Forensic Evidence › KEY — API Keys labels` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-230b-forensic.spec.ts::W28A-230B Forensic Evidence › MCP — MCP Console labels` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-230b-forensic.spec.ts::W28A-230B Forensic Evidence › PROF — Profiles labels` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-230b-forensic.spec.ts::W28A-230B Forensic Evidence › RBAC — RBAC labels` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-230b-forensic.spec.ts::W28A-230B Forensic Evidence › REL — Relationships labels` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-230b-forensic.spec.ts::W28A-230B Forensic Evidence › SCH — Schema labels` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-230b-forensic.spec.ts::W28A-230B Forensic Evidence › SET — Settings labels` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-230b-forensic.spec.ts::W28A-230B Forensic Evidence › SRC — Search labels` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-230b-forensic.spec.ts::W28A-230B Forensic Evidence › USR — Users labels` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-341-browser-proof.spec.ts::W28A-341 DB-MCP dashboard HealthWidgets + cross-page proof` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-691-jobs-conformance.spec.ts::Section A seeds current-run jobs through WebUI MCP console and source lifecycle runtime` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-691-jobs-conformance.spec.ts::Section E admin rows and Section G cross-page smoke` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-691-jobs-conformance.spec.ts::Section E non-admin RBAC rows 2 through 7` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-691-jobs-conformance.spec.ts::Sections B C D F validate DataTable lifecycle dialog filters sort pagination and bulk paths` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-722-idam-webui.spec.ts::W28A-722 WebUI IDAM RBAC, API-key lifecycle, and DOM proof` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-773-layout-audit.spec.ts::W28A-773 T.1 A2A Console PS-72 v2 layout audit › T.1.0 capture rendered A2A console (DOM + screenshot + testid presence)` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-773-layout-audit.spec.ts::W28A-773 T.1 A2A Console PS-72 v2 layout audit › T.1.1 A2A page root ([data-testid=a2a-console-page])` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-773-layout-audit.spec.ts::W28A-773 T.1 A2A Console PS-72 v2 layout audit › T.1.4 A2A submit button ([data-testid=mcp-console-submit])` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-773-layout-audit.spec.ts::W28A-773 T.1 A2A Console PS-72 v2 layout audit › T.1.6 A2A correlation_id + request_id ([data-testid=mcp-console-meta-*])` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-773-layout-audit.spec.ts::W28A-773 T.1 A2A Console PS-72 v2 layout audit › T.1.7 A2A Docs link ([data-testid=mcp-console-docs-link])` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-773-layout-audit.spec.ts::W28A-773 T.1 A2A Console PS-72 v2 layout audit › T.1.8 A2A agent card + events stream ([data-testid=a2a-console-agent-card|events-stream])` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-773-layout-audit.spec.ts::W28A-773 T.1 MCP Console PS-72 v2 layout audit › T.1.0 capture rendered MCP console (DOM + screenshot + testid presence)` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-773-layout-audit.spec.ts::W28A-773 T.1 MCP Console PS-72 v2 layout audit › T.1.1 MCP tool list panel ([data-testid=mcp-console-tool-list])` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-773-layout-audit.spec.ts::W28A-773 T.1 MCP Console PS-72 v2 layout audit › T.1.2 MCP request editor labelled 'Request' ([data-testid=mcp-console-request-label])` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-773-layout-audit.spec.ts::W28A-773 T.1 MCP Console PS-72 v2 layout audit › T.1.3 MCP API-key field auto-populated + masked override ([data-testid=mcp-console-apikey-field])` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-773-layout-audit.spec.ts::W28A-773 T.1 MCP Console PS-72 v2 layout audit › T.1.4 MCP submit button placement + label 'Submit' ([data-testid=mcp-console-submit])` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-773-layout-audit.spec.ts::W28A-773 T.1 MCP Console PS-72 v2 layout audit › T.1.5 MCP result/meta widget placement ([data-testid=mcp-console-result] + meta)` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-773-layout-audit.spec.ts::W28A-773 T.1 MCP Console PS-72 v2 layout audit › T.1.6 MCP correlation_id + request_id surfaced ([data-testid=mcp-console-meta-*])` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-773-layout-audit.spec.ts::W28A-773 T.1 MCP Console PS-72 v2 layout audit › T.1.7 MCP Docs link routes to Docs page ([data-testid=mcp-console-docs-link])` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-773-ps72-conformance.spec.ts::PS-72 v2 A2A Console Conformance › §1+§8 A2A console layout: agent card + events stream` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-773-ps72-conformance.spec.ts::PS-72 v2 A2A Console Conformance › §6 docs link present on A2A console` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-773-ps72-conformance.spec.ts::PS-72 v2 A2A Console Conformance › §7 A2A status badge is present and canonical` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-773-ps72-conformance.spec.ts::PS-72 v2 A2A Console Conformance › §8.3 no "Request failed with status 404" text anywhere` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-773-ps72-conformance.spec.ts::PS-72 v2 MCP Console Conformance › §1 canonical layout: all required elements present` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-773-ps72-conformance.spec.ts::PS-72 v2 MCP Console Conformance › §2 API-key field present with helper text` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-773-ps72-conformance.spec.ts::PS-72 v2 MCP Console Conformance › §2 admin-key override input exists and is masked` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-773-ps72-conformance.spec.ts::PS-72 v2 MCP Console Conformance › §3 clicking a tool populates request editor` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-773-ps72-conformance.spec.ts::PS-72 v2 MCP Console Conformance › §3 request editor labelled "Request"` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-773-ps72-conformance.spec.ts::PS-72 v2 MCP Console Conformance › §3 tool list scrolls and search filters` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-773-ps72-conformance.spec.ts::PS-72 v2 MCP Console Conformance › §4 submit button text is "Submit"` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-773-ps72-conformance.spec.ts::PS-72 v2 MCP Console Conformance › §4+§5 immediate tool "schema_list": submit, result inline, meta populated` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-773-ps72-conformance.spec.ts::PS-72 v2 MCP Console Conformance › §4.4 async tool "query": job ID link rendered, status badge lifecycle` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-773-ps72-conformance.spec.ts::PS-72 v2 MCP Console Conformance › §6 docs link present and navigates` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-773-ps72-conformance.spec.ts::PS-72 v2 MCP Console Conformance › §7 top-of-page status badge is canonical` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-773-ps72-conformance.spec.ts::PS-72 v2 MCP Console Conformance › §9 RBAC: locked tool is greyed, submit disabled` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-773-t2-functional.spec.ts::T.2.1 safe sync MCP ping (control-plane): real result inline + correlation_id/request_id meta` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-773-t2-functional.spec.ts::T.2.2 safe sync A2A (health skill): agent card + events stream + result` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-773-t2-functional.spec.ts::T.2.3 async index.rebuild: Job ID link to Jobs page + lifecycle status badge` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-773-t2-functional.spec.ts::T.2.4 denial surfaces inline (404 NOT_FOUND): result widget shows denial, not blank/exception` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-773-t2-functional.spec.ts::T.2.5 API-key override: override field present + masked + submit succeeds` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-803/settings/section-3-settings-conformance.spec.ts::W28A-803 — PS-73 v2 Settings conformance › 3.1 — page loads as admin, PS-81 explorer rendered, no 4xx on config surfaces (A7)` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-803/settings/section-3-settings-conformance.spec.ts::W28A-803 — PS-73 v2 Settings conformance › 3.2 — rendered key count matches the live served config exactly (A1)` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-803/settings/section-3-settings-conformance.spec.ts::W28A-803 — PS-73 v2 Settings conformance › 3.3 — random-sample keys: presence + source + value match the live truth set` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-803/settings/section-3-settings-conformance.spec.ts::W28A-803 — PS-73 v2 Settings conformance › 3.4 — secrets masked by default; admin reveal requires action and is audited (A2)` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-803/settings/section-3-settings-conformance.spec.ts::W28A-803 — PS-73 v2 Settings conformance › 3.5 — page-level search highlights matching nodes; clearing restores the tree (A5)` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-803/settings/section-3-settings-conformance.spec.ts::W28A-803 — PS-73 v2 Settings conformance › 3.6 — PS-81 interactions: expand-all, collapse-all, copy-leaf, copy-subtree` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-803/settings/section-3-settings-conformance.spec.ts::W28A-803 — PS-73 v2 Settings conformance › 3.7 — per-server segmentation: every server tab is non-empty (A4)` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-803/settings/section-3-settings-conformance.spec.ts::W28A-803 — PS-73 v2 Settings conformance › 3.x — every node carries a valid source-attribution badge (A3)` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-846/ps77-comprehensive.spec.ts::About — About dialog renders product name + version` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-846/ps77-comprehensive.spec.ts::CW-A error — invalid credentials surface an error, no crash` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-846/ps77-comprehensive.spec.ts::CW-A1 — login page renders Sign in (canonical LoginPage)` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-846/ps77-comprehensive.spec.ts::CW-A3 — session timeout countdown is present after sign-in` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-846/ps77-comprehensive.spec.ts::CW-A4 — logout via user menu clears session and returns to login` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-846/ps77-comprehensive.spec.ts::CW-A5 — auth guard redirects unauthenticated navigation to login` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-846/ps77-comprehensive.spec.ts::CW-D5 — dashboard renders service status bar + heading` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-846/ps77-comprehensive.spec.ts::CW-M1 — top navigation renders service pages + About` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-846/ps77-comprehensive.spec.ts::CW-M5 — footer shows the canonical copyright line` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-846/ps77-comprehensive.spec.ts::CW-T6/T7 — audit DataTable shows rows or a meaningful empty state` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-846/ps77-comprehensive.spec.ts::Hygiene — no console errors or failed responses on dashboard` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-846/ps77-comprehensive.spec.ts::Mobile — hamburger navigation toggle present on small viewport` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-846/ps77-comprehensive.spec.ts::Profile — user menu opens profile dialog with identity and roles` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-871-catalogue.spec.ts::W28A-871 Catalogue renders profile discovery and in-panel entity detail` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-871-data-browser.spec.ts::W28A-871 Data Browser uses scoped route, saved queries, and read-only actionable error` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-871-non-cluster.spec.ts::W28A-871 Audit & Log consumes job context and API Docs examples provide Cancel` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-871-non-cluster.spec.ts::W28A-871 Jobs links to Audit & Log and detail dialog has required controls` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-871-non-cluster.spec.ts::W28A-871 canonical /system/about renders the shared AboutPage body` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-871-non-cluster.spec.ts::W28A-871 non-cluster admin rows use the Audit Log row link and dialogs have Close plus Cancel` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-871-profiles.spec.ts::W28A-871 Profiles page uses source connection, discovery, scope test, and canonical actions` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-871-relationships.spec.ts::W28A-871 Relationships uses discovered selectors and canonical actions` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-871-schema.spec.ts::W28A-871 Schema Planner deep-links, structures plan output, approves, and applies` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-871-search.spec.ts::W28A-871 Search preloads facets, examples, loading state, and canonical actions` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-871-source-connections.spec.ts::W28A-871 Source Connections page supports CRUD controls and actionable 409` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-871-x-cross-cutting.spec.ts::W871-X-01/X-08: every db-mcp page in scope has one footer and canonical Audit & Log nav` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-871-x-cross-cutting.spec.ts::W871-X-03/X-04: dialogs use title case and expose top Close plus footer Cancel` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-871-x-cross-cutting.spec.ts::W871-X-05/X-08: destructive actions confirm and row links use Audit & Log` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-871-x-cross-cutting.spec.ts::W871-X-06/X-10/X-11: shared IDAM admin pages and job activity links are actionable` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28a-871-x-cross-cutting.spec.ts::W871-X-07/X-09/X-12: core pages render without console errors, blank bodies, or duplicate copyright` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28e-1808c-a11y.spec.ts::W28E-1808C axe a11y has zero WCAG A/AA violations on required WebUI pages` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28e-1808c-url-canonical.spec.ts::W28E-1808C MCP and A2A service endpoints are not treated as console aliases` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28e-1808c-url-canonical.spec.ts::W28E-1808C canonical routes render without route drift, console errors, or HTTP failures` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28e-1808c-url-canonical.spec.ts::W28E-1808C legacy WebUI aliases return 308 to canonical routes and preserve query strings` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28e-1808c-url-canonical.spec.ts::W28E-1808C rendered navigation emits canonical URLs only` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28e-610-xc-conformance.spec.ts::CX-101: select rows + trigger bulk Export → download blob` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28e-610-xc-conformance.spec.ts::CX-102: row actions rendered as shared ghost action buttons` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28e-610-xc-conformance.spec.ts::CX-103: first identifier column is a link (role=link)` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28e-610-xc-conformance.spec.ts::CX-104: audit deep-link param is consumed (filter context banner)` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28e-610-xc-conformance.spec.ts::CX-110: /admin/roles renders Roles page` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28e-610-xc-conformance.spec.ts::CX-120 + CX-150: /developer/api-docs has 4 reference tabs and tool table renders` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28e-610-xc-conformance.spec.ts::CX-130: MCP Console combined catalogue/detail — single tool list, click expands detail` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28e-610-xc-conformance.spec.ts::CX-131: A2A Console two-panel (agent card + task console)` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28e-610-xc-conformance.spec.ts::CX-140: Settings JsonExplorer renders Path/Type/Value table, first row not root` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28e-610-xc-conformance.spec.ts::CX-160: poll/scroll stability — scroll preserved across a Jobs refresh, stable row keys` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28e-610-xc-conformance.spec.ts::Section G smoke: raw per-route networkFailures[] + consoleMessages[] captured, zero/justified` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28e-610-xc-conformance.spec.ts::XC-001: settings header shows a live version string` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28e-610-xc-conformance.spec.ts::XC-005: sidebar audit nav is exactly 'Audit & Log'` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `e2e/w28e-610-xc-conformance.spec.ts::XC-009: /system/settings has Save header + Build/Diagnostics cards + config surface` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |
| `w28a-889b-unauth-login-gate.spec.ts::W28A-889-B unauth login-gate (clean context) › unauthenticated visitor sees the login screen, not the app` | UNCLASSIFIED | pass | 2026-07-14 | `39cbed34` | |

## 3. Failures (detail)

_None._
