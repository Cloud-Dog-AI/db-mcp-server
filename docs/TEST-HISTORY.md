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
doc-last-updated: 2026-07-14
doc-git-commit: 7da1fe4abe8926735c08c6e61db5df6de1e38a29
doc-git-branch: main
doc-source-shas: []
doc-age-policy: indefinite
doc-conformance-stamp: 2026-07-14T17:44:23Z
---

# db-mcp-server — TEST-HISTORY

> **Template version:** T-TSH v1.0 — appended to by `scripts/update-test-state.py`. Roll-archive to `archive/test-history/<YYYY-MM>.md` when >500 lines.

## Runs (most recent first)

### 2026-07-14T21:20:17.869Z — W28E-1882
- Commit: `39cbed348c00813df55639c41aaf70ee687965a3` (main)
- Runtime: N/A (Node/Playwright)
- Environment: `deployed preprod; approved runtime/Vault credentials; service E2E_BASE_URL`
- Command: `bash /opt/iac/Development/cloud-dog-ai/tmp/W28E-1882/run-dbmcp.sh FINAL`
- Evidence: `W28E-1882-FINAL-PROOF-R2:working/evidence/W28E-1882/current/raw/db-mcp/db-mcp.FINAL.junit.xml`
- Totals: 140 / P 140 / F 0 / E 0 / S 0
- Delta: new-fails 0 | newly-green 0

### 2026-07-14T17:44:23Z - W28R-3011 traceability correction
- Timestamp source: `date -u +%Y-%m-%dT%H:%M:%SZ` captured `2026-07-14T17:44:23Z` (epoch `1784051063`).
- Commit: `7da1fe4abe8926735c08c6e61db5df6de1e38a29` (`origin/main` documentation review baseline)
- Runtime: N/A (documentation-only evidence audit; no test run)
- Lane: `W28R-3011` seven-day traceability correction
- Environment: NOT IMPORTED
- Command: N/A (documentation audit only)
- Evidence: `docs/TEST-CANDIDATE-DISPOSITION.tsv`; immutable `W28R-3011-EVIDENCE-R6^{}` and `W28R-3011-FINAL-PROOF-R6^{}`
- Totals: 0 / P 0 / F 0 / E 0 / S 0 canonical imported runs
- Delta: removed both synthetic 18/18 browser imports; retained their totals and all adverse attempts as NOT IMPORTED
- Runtime separation: CPython 3.12 NOT RUN; CPython 3.13.14 222/222 NOT IMPORTED; Node/Playwright local and deployed 18/18 NOT IMPORTED; retained local/deployed 140/140 browser totals NOT IMPORTED.

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
