---
template-id: T-TSH
template-version: 1.0
applies-to: docs/TEST-HISTORY.md
registry: service
required: must-have
when-applicable: ""
template-last-updated: 2026-06-12
template-owner: platform-standards

project: db-mcp-server
doc-last-updated: 2026-06-12
doc-git-commit: ee5979008dace594f92b45315bdf687fb1aa00df
doc-git-branch: main
doc-source-shas: []
doc-age-policy: indefinite
doc-conformance-stamp: 2026-06-12T12:00:00Z
---

# db-mcp-server — TEST-HISTORY

> **Template version:** T-TSH v1.0 — appended to by `scripts/update-test-state.py`. Roll-archive to `archive/test-history/<YYYY-MM>.md` when >500 lines.

## Runs (most recent first)

### 2026-07-14T12:39:24Z — W28R-3011
- Commit: `e308bec871dbef170ecfbf73c7eb725b1845e05b` (main)
- Runtime: N/A (Node/Playwright)
- Environment: `deployed https://dbmcpserver0.cloud-dog.net; effective credentials resolved in-process from deployed runtime config and not logged; UI harness 04ddb4da435e796b99662f52c8e3232c53f087ce`
- Command: `pnpm exec playwright test tests/e2e/w28a-230b-forensic.spec.ts --reporter=line,junit --workers=1 --retries=0 against https://dbmcpserver0.cloud-dog.net (effective credentials resolved in-process from deployed runtime config; values not logged)`
- Evidence: `origin/w28r-3011-evidence@74eb15529b10387fc945b4bf9b504494cce4109b:working/evidence/W28R-3011/current/raw/r6/webui/deployed/deployed-forensic.junit.xml + adjacent .log + raw/r6/drift/r6-drift-preflight-final.log (PROVISIONAL / LANE NOT ACCEPTED)`
- Totals: 18 / P 18 / F 0 / E 0 / S 0
- Delta: new-fails 0 | newly-green 0

### 2026-07-14T12:30:55Z — W28R-3011
- Commit: `e308bec871dbef170ecfbf73c7eb725b1845e05b` (main)
- Runtime: N/A (Node/Playwright)
- Environment: `runtime auth detection; clean managed local stack; UI harness 04ddb4da435e796b99662f52c8e3232c53f087ce`
- Command: `pnpm exec playwright test tests/e2e/w28a-230b-forensic.spec.ts --reporter=line,junit --workers=1 --retries=0 (runtime auth detection, clean managed stack)`
- Evidence: `origin/w28r-3011-evidence@74eb15529b10387fc945b4bf9b504494cce4109b:working/evidence/W28R-3011/current/raw/r6/webui/local/local-forensic.junit.xml + adjacent .log + raw/r6/drift/r6-drift-preflight-final.log (PROVISIONAL / LANE NOT ACCEPTED)`
- Totals: 18 / P 18 / F 0 / E 0 / S 0
- Delta: new-fails 0 | newly-green 0

### 2026-06-17T12:28:14.133567+00:00
- Commit: `9c5b12de8af6c1142c4401994aa3148adf2d1a6e` (W28C-1714-100pct-fix)
- Totals: 107 / P 107 / F 0 / S 0
- Delta: new-fails 0 | newly-green 0

### 2026-06-17T12:27:56.698317+00:00
- Commit: `9c5b12de8af6c1142c4401994aa3148adf2d1a6e` (W28C-1714-100pct-fix)
- Totals: 101 / P 101 / F 0 / S 0
- Delta: new-fails 0 | newly-green 0

### 2026-06-17T12:24:35.920683+00:00
- Commit: `9c5b12de8af6c1142c4401994aa3148adf2d1a6e` (W28C-1714-100pct-fix)
- Totals: 101 / P 101 / F 0 / S 0
- Delta: new-fails 0 | newly-green 0

### 2026-06-17T11:09:50.028924+00:00
- Commit: `d064aa17d3a6570cb01e86bbf63e4632b37fb355` (W28C-1714-100pct-fix)
- Totals: 17 / P 17 / F 0 / S 0
- Delta: new-fails 0 | newly-green 1

### 2026-06-13T10:59:12.425500+00:00
- Commit: `6da4df0467c7fd9cca1db0f700e6ebae8b87836a` (main)
- Totals: 149 / P 148 / F 1 / S 0
- Delta: new-fails 1 | newly-green 1

### 2026-06-13T10:18:37.289192+00:00
- Commit: `6da4df0467c7fd9cca1db0f700e6ebae8b87836a` (main)
- Totals: 132 / P 131 / F 1 / S 0
- Delta: new-fails 1 | newly-green 0

### 2026-06-12T12:00:00Z
- Commit: `ee5979008dace594f92b45315bdf687fb1aa00df` (main)
- Totals: N / P n / F n / S n
- Delta: new-fails 0 | newly-green 0
