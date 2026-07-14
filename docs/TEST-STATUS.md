---
template-id: T-TSS
template-version: 1.0
project: db-mcp-server
doc-last-updated: 2026-07-14
doc-git-commit: 7da1fe4abe8926735c08c6e61db5df6de1e38a29
doc-git-branch: main
doc-age-policy: 30d
doc-conformance-stamp: 2026-07-14T17:44:23Z
---

# db-mcp-server - TEST-STATUS

> **Template version:** T-TSS v1.0. Only runs with original UTC time, tested commit, literal executable command, exact environment/configuration, runtime, totals, and immutable raw evidence are canonical.

## 1. Latest run

- **Run timestamp:** NOT RUN (no qualifying canonical run in the 2026-07-08..14 review window)
- **Commit:** `7da1fe4abe8926735c08c6e61db5df6de1e38a29` (`origin/main` documentation review baseline; not a tested commit)
- **Runtime:** N/A (no qualifying run imported)
- **Lane:** `W28R-3011` and seven-day candidate audit
- **Environment:** NOT IMPORTED - retained candidates do not bind exact environment/configuration to an attributable tested service source and literal executable invocation
- **Command:** NOT IMPORTED - candidate command fields contain explanatory prose or describe a flow rather than the literal foreground command
- **Evidence:** `docs/TEST-CANDIDATE-DISPOSITION.tsv`; immutable `W28R-3011-EVIDENCE-R6^{}` at `bf6f9a2d60fa33dcfc9e1be88c5a13bfa2c64c60` and `W28R-3011-FINAL-PROOF-R6^{}` at `bb87ffccb699e034bdfc336736220322c77a90ee`
- **Totals:** 0 tests | 0 passed | 0 failed | 0 errors | 0 skipped (canonical imported runs)

### Runtime truth

| Runtime | Canonical result | Disposition |
|---|---|---|
| CPython 3.12 | NOT RUN | No full CPython 3.12 suite was found for W28R-3011. |
| CPython 3.13.14 | NOT IMPORTED | Retained R5 JUnits total 222/222 across QT 5, UT 156, ST 16, IT 27, and AT 18, but their original literal commands and exact environments are absent. R6 only replayed those artifacts; replay totals are not new test runs. |
| N/A (Node/Playwright), local | NOT IMPORTED | R6 reports 18/18 at `2026-07-14T12:30:55Z`; the log's command appends non-executable explanatory text and does not bind exact service environment/source provenance. |
| N/A (Node/Playwright), deployed | NOT IMPORTED | R6 reports 18/18 at `2026-07-14T12:39:24Z`; its run ledger describes a flow and the log's command appends non-executable prose. |
| N/A (Node/Playwright), retained R5 | NOT IMPORTED | Local 140/140 and deployed 140/140 JUnits have totals and timestamps but no retained original command/environment tuple. |

## 2. Per-test status

No per-test rows are canonically imported for the review window.

| Test ID | Tier | Status | Last run | Commit | Known issue |
|---|---|---|---|---|---|
| _No canonical rows_ | - | - | - | - | See runtime truth and immutable evidence dispositions. |

## 3. Noncanonical and adverse evidence

- R6 local browser attempt 1 forced the wrong authentication mode and failed; attempt 2 encountered a leftover managed port.
- R6 deployed browser attempt 1 received deterministic unauthorized responses.
- The initial login capture helper failed module resolution, and seven local/deployed screenshot hashes collided before recapture.
- The first retained-proof parser used an incorrect expected audit-regression count before the corrected replay.
- Final R6 local and deployed 18/18, retained R5 Python 222/222, and retained R5 browser 140/140 local plus 140/140 deployed remain **NOT IMPORTED** for missing command/environment provenance.

The complete candidate review is [TEST-CANDIDATE-DISPOSITION.tsv](TEST-CANDIDATE-DISPOSITION.tsv).
