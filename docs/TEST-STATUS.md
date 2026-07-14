---
template-id: T-TSS
template-version: 1.0
project: db-mcp-server
doc-last-updated: 2026-07-14T12:39:24Z
doc-git-commit: e308bec871dbef170ecfbf73c7eb725b1845e05b
doc-git-branch: main
doc-age-policy: 30d
doc-conformance-stamp: 2026-07-14T12:39:24Z
---

# db-mcp-server — TEST-STATUS

> **Template version:** T-TSS v1.0 — overwritten by `scripts/update-test-state.py`. Do not hand-edit.

## 1. Latest run

- **Run timestamp:** 2026-07-14T12:39:24Z
- **Commit:** `e308bec871dbef170ecfbf73c7eb725b1845e05b` (`main`)
- **Runtime:** N/A (Node/Playwright)
- **Lane:** `W28R-3011`
- **Environment:** `deployed https://dbmcpserver0.cloud-dog.net; effective credentials resolved in-process from deployed runtime config and not logged; UI harness 04ddb4da435e796b99662f52c8e3232c53f087ce`
- **Command:** `pnpm exec playwright test tests/e2e/w28a-230b-forensic.spec.ts --reporter=line,junit --workers=1 --retries=0 against https://dbmcpserver0.cloud-dog.net (effective credentials resolved in-process from deployed runtime config; values not logged)`
- **Evidence:** `origin/w28r-3011-evidence@74eb15529b10387fc945b4bf9b504494cce4109b:working/evidence/W28R-3011/current/raw/r6/webui/deployed/deployed-forensic.junit.xml + adjacent .log + raw/r6/drift/r6-drift-preflight-final.log (PROVISIONAL / LANE NOT ACCEPTED)`
- **Totals:** 18 tests | 18 passed | 0 failed | 0 errors | 0 skipped

## 2. Per-test status

| Test ID | Tier | Status | Last run | Commit | Known issue |
|---|---|---|---|---|---|
| `e2e/w28a-230b-forensic.spec.ts::W28A-230B Forensic Evidence › A2A — A2A Console labels` | UNCLASSIFIED | pass | 2026-07-14 | `e308bec8` | |
| `e2e/w28a-230b-forensic.spec.ts::W28A-230B Forensic Evidence › AUD — Audit labels` | UNCLASSIFIED | pass | 2026-07-14 | `e308bec8` | |
| `e2e/w28a-230b-forensic.spec.ts::W28A-230B Forensic Evidence › CAT — Catalogue labels` | UNCLASSIFIED | pass | 2026-07-14 | `e308bec8` | |
| `e2e/w28a-230b-forensic.spec.ts::W28A-230B Forensic Evidence › DASH — Dashboard labels` | UNCLASSIFIED | pass | 2026-07-14 | `e308bec8` | |
| `e2e/w28a-230b-forensic.spec.ts::W28A-230B Forensic Evidence › DBR — Data Browser labels` | UNCLASSIFIED | pass | 2026-07-14 | `e308bec8` | |
| `e2e/w28a-230b-forensic.spec.ts::W28A-230B Forensic Evidence › DOC — API Docs labels` | UNCLASSIFIED | pass | 2026-07-14 | `e308bec8` | |
| `e2e/w28a-230b-forensic.spec.ts::W28A-230B Forensic Evidence › ENT — Entity Detail labels` | UNCLASSIFIED | pass | 2026-07-14 | `e308bec8` | |
| `e2e/w28a-230b-forensic.spec.ts::W28A-230B Forensic Evidence › GRP — Groups labels` | UNCLASSIFIED | pass | 2026-07-14 | `e308bec8` | |
| `e2e/w28a-230b-forensic.spec.ts::W28A-230B Forensic Evidence › JOB — Jobs labels` | UNCLASSIFIED | pass | 2026-07-14 | `e308bec8` | |
| `e2e/w28a-230b-forensic.spec.ts::W28A-230B Forensic Evidence › KEY — API Keys labels` | UNCLASSIFIED | pass | 2026-07-14 | `e308bec8` | |
| `e2e/w28a-230b-forensic.spec.ts::W28A-230B Forensic Evidence › MCP — MCP Console labels` | UNCLASSIFIED | pass | 2026-07-14 | `e308bec8` | |
| `e2e/w28a-230b-forensic.spec.ts::W28A-230B Forensic Evidence › PROF — Profiles labels` | UNCLASSIFIED | pass | 2026-07-14 | `e308bec8` | |
| `e2e/w28a-230b-forensic.spec.ts::W28A-230B Forensic Evidence › RBAC — RBAC labels` | UNCLASSIFIED | pass | 2026-07-14 | `e308bec8` | |
| `e2e/w28a-230b-forensic.spec.ts::W28A-230B Forensic Evidence › REL — Relationships labels` | UNCLASSIFIED | pass | 2026-07-14 | `e308bec8` | |
| `e2e/w28a-230b-forensic.spec.ts::W28A-230B Forensic Evidence › SCH — Schema labels` | UNCLASSIFIED | pass | 2026-07-14 | `e308bec8` | |
| `e2e/w28a-230b-forensic.spec.ts::W28A-230B Forensic Evidence › SET — Settings labels` | UNCLASSIFIED | pass | 2026-07-14 | `e308bec8` | |
| `e2e/w28a-230b-forensic.spec.ts::W28A-230B Forensic Evidence › SRC — Search labels` | UNCLASSIFIED | pass | 2026-07-14 | `e308bec8` | |
| `e2e/w28a-230b-forensic.spec.ts::W28A-230B Forensic Evidence › USR — Users labels` | UNCLASSIFIED | pass | 2026-07-14 | `e308bec8` | |

## 3. Failures (detail)

_None._
