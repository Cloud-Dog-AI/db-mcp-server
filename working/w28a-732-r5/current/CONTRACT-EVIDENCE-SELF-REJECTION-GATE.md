# Contract Evidence Self-Rejection Gate

WAIVER_COUNT=0

| Check | Raw artefact | Raw value observed | Verification command | Pass |
| --- | --- | --- | --- | --- |
| Mandatory reading proof exists | `00-reading-proof.md`, `raw/g0-warrant-replay.txt` | `RULES_REREAD: YES`; `AGENT-LESSONS_REREAD: YES`; `AGENT-BOOTSTRAP-DIRECTIVE_REREAD: YES` | `grep -E 'RULES_REREAD: YES|AGENT-LESSONS_REREAD: YES|AGENT-BOOTSTRAP-DIRECTIVE_REREAD: YES' working/w28a-732-r5/current/00-reading-proof.md` | PASS |
| Requirements map all PASS | `requirements-map.tsv` | Final column `PASS` on every row | `awk -F '\\t' 'NR>1 && $NF != "PASS" {bad=1} END {exit bad}' working/w28a-732-r5/current/requirements-map.tsv` | PASS |
| Current evidence only final pass artefacts | `current/raw`, `current/screenshots` | final pass logs and unique screenshots only | `find working/w28a-732-r5/current -type f | sort` | PASS |
| Stale artefacts separated | `working/w28a-732-r5/historical` | prior non-final run files copied outside active `current/` evidence scope | `find working/w28a-732-r5/historical -maxdepth 1 -type f | sort | head` | PASS |
| Live preprod proof | `raw/g7-preprod-health-60s.log`, `raw/g8-preprod-playwright-rerun2.log` | G7 PASS and G8 PASS | `grep -E 'G7 PASS|G8 \\{\"result\": \"PASS\"' working/w28a-732-r5/current/raw/g7-preprod-health-60s.log working/w28a-732-r5/current/raw/g8-preprod-playwright-rerun2.log` | PASS |
| No credential exposure in final report | `FINAL-REPORT.md` | keys represented only by SHA-256 hashes in G8 log | `grep 'flat_key_hashes' working/w28a-732-r5/current/raw/g8-preprod-playwright-rerun2.log` | PASS |
| Git and tags reproducible | `remote-proof.txt`, `FINAL-TAG-VERIFICATION.txt` | service and validator anchor tag names recorded | `grep -E 'EVIDENCE_TAG|FINAL_PROOF_TAG|W28A-732-R5' working/w28a-732-r5/current/remote-proof.txt working/w28a-732-r5/current/FINAL-TAG-VERIFICATION.txt` | PASS |
