# W28A-732-R5 Final Report

HAVE_ALL_REQUIREMENTS_BEEN_MET: YES
WAIVER_COUNT=0

Close Gate: complete from raw artefacts under `working/w28a-732-r5/current`.

## Evidence Matrix

| Requirement | Raw artefact (path) | Raw value observed | Verification command | Pass |
| --- | --- | --- | --- | --- |
| GATE 0 reading warrant present | `working/w28a-732-r5/current/00-reading-proof.md`; `working/w28a-732-r5/current/raw/g0-warrant-replay.txt` | `RULES_REREAD: YES`; `AGENT-LESSONS_REREAD: YES`; `AGENT-BOOTSTRAP-DIRECTIVE_REREAD: YES`; platform and service file line counts and SHA256(12) recorded | `cat working/w28a-732-r5/current/00-reading-proof.md && cat working/w28a-732-r5/current/raw/g0-warrant-replay.txt` | PASS |
| requirements-map.tsv exists and every row passes | `working/w28a-732-r5/current/requirements-map.tsv` | Final column is `PASS` for every requirement row | `awk -F '\t' 'NR>1 && $NF != "PASS" {bad=1} END {exit bad}' working/w28a-732-r5/current/requirements-map.tsv` | PASS |
| Evidence split into current and historical scopes | `working/w28a-732-r5/current`; `working/w28a-732-r5/historical` | Active evidence path is `current/`; prior non-final root artefacts copied under `historical/` | `find working/w28a-732-r5/current -type f | sort && find working/w28a-732-r5/historical -maxdepth 1 -type f | sort | head` | PASS |
| Evidence Matrix included | `working/w28a-732-r5/current/FINAL-REPORT.md` | This table has one row per closeout requirement with raw artefact, raw value, command, and PASS | `grep -F '| Requirement | Raw artefact (path) | Raw value observed | Verification command | Pass |' working/w28a-732-r5/current/FINAL-REPORT.md` | PASS |
| G1 zero greps | `working/w28a-732-r5/current/raw/g1-greps.log` | `G1 PASS`; direct-env, logging, cache, vault, class-cache matches all `0` | `grep -E 'G1 PASS|matches=0' working/w28a-732-r5/current/raw/g1-greps.log` | PASS |
| G2 local service health | `working/w28a-732-r5/current/raw/g2-local-service.log` | local API, Web, MCP, A2A health checks returned HTTP 200; `G2 PASS` | `grep -E 'HTTP 200|G2 PASS' working/w28a-732-r5/current/raw/g2-local-service.log` | PASS |
| G3 pytest QT UT ST IT AT green and zero skips | `working/w28a-732-r5/current/raw/g3-pass-summary.log`; `working/w28a-732-r5/current/raw/g3-pass-*.log` | `G3 PASS 2026-06-11T12:37:54+01:00`; no skip text in final pass logs | `grep 'G3 PASS' working/w28a-732-r5/current/raw/g3-pass-summary.log && ! grep -Eiq 'skip|skipped' working/w28a-732-r5/current/raw/g3-pass-*.log` | PASS |
| G4 Docker build through script | `working/w28a-732-r5/current/raw/g4-docker-build-redeploy-fix.log` | `Build OK: cloud-dog/db-mcp-server:latest (variant=public)` | `grep 'Build OK: cloud-dog/db-mcp-server:latest' working/w28a-732-r5/current/raw/g4-docker-build-redeploy-fix.log` | PASS |
| G5 local Docker run proof | `working/w28a-732-r5/current/raw/g5-local-docker-run-redeploy-fix-pass.log` | named container `w28a-732-dbmcpserver`; final health code 200; package versions recorded; `G5 PASS` | `grep -E 'G5 PASS|final_health_code=200|Name: db-mcp-server|Name: cloud-dog-api-kit' working/w28a-732-r5/current/raw/g5-local-docker-run-redeploy-fix-pass.log` | PASS |
| G6 registry digest captured | `working/w28a-732-r5/current/raw/g6-image-push-redeploy-fix.log` | `latest: digest: sha256:6dbe97620981910af9d4871f5b98fa6d0ef37373a880194d7417a4ce0d0b137d` | `grep 'sha256:6dbe97620981910af9d4871f5b98fa6d0ef37373a880194d7417a4ce0d0b137d' working/w28a-732-r5/current/raw/g6-image-push-redeploy-fix.log` | PASS |
| G6 final commit pushed to origin main | `working/w28a-732-r5/current/raw/g6-commit.log` | `86ab9f5192dfe39fd7ac9f3d6c3be94010e01dfb refs/heads/main` | `grep '86ab9f5192dfe39fd7ac9f3d6c3be94010e01dfb.*refs/heads/main' working/w28a-732-r5/current/raw/g6-commit.log` | PASS |
| G7 Terraform-only deploy | `working/w28a-732-r5/current/raw/g7-terraform-apply-redeploy-fix.log` | targeted apply completed for Docker image and container; `Apply complete! Resources: 2 added, 0 changed, 1 destroyed` | `grep 'Apply complete! Resources: 2 added, 0 changed, 1 destroyed' working/w28a-732-r5/current/raw/g7-terraform-apply-redeploy-fix.log` | PASS |
| G7 live preprod health and 60 second recheck | `working/w28a-732-r5/current/raw/g7-preprod-health-60s.log` | first and second `https://dbmcpserver0.cloud-dog.net/api/health` checks returned `code=200`; `G7 PASS` | `grep -E 'code=200|G7 PASS' working/w28a-732-r5/current/raw/g7-preprod-health-60s.log` | PASS |
| G8 target WebUI anon login box | `working/w28a-732-r5/current/raw/g8-preprod-playwright-rerun2.log`; `working/w28a-732-r5/current/screenshots/g8_anon_login_box.png` | `anon_login_box` status `200`, inputs `1` | `grep 'anon_login_box.*"status": 200' working/w28a-732-r5/current/raw/g8-preprod-playwright-rerun2.log` | PASS |
| G8 target WebUI role logins | `working/w28a-732-r5/current/raw/g8-preprod-playwright-rerun2.log`; role screenshots under `current/screenshots` | `admin_auth_me`, `read-write_auth_me`, `read-only_auth_me` status `200` with role arrays | `grep -E 'admin_auth_me|read-write_auth_me|read-only_auth_me' working/w28a-732-r5/current/raw/g8-preprod-playwright-rerun2.log` | PASS |
| G8 read-only write 403 inline | `working/w28a-732-r5/current/raw/g8-preprod-playwright-rerun2.log`; `working/w28a-732-r5/current/screenshots/g8_read_only_403_inline.png` | `read_only_data_create_denied {"ok": false, "status": 403}` and inline screenshot path recorded | `grep -E 'read_only_data_create_denied.*"status": 403|read_only_403_inline_screenshot' working/w28a-732-r5/current/raw/g8-preprod-playwright-rerun2.log` | PASS |
| G8 real CRUD and RBAC | `working/w28a-732-r5/current/raw/g8-preprod-playwright-rerun2.log` | admin user/profile CRUD; read-write data CRUD; read-only data create denied | `grep -E 'admin_user_create|admin_user_update|admin_user_delete|admin_profile_create|admin_profile_delete|read_write_data_create|read_write_data_update|read_write_data_delete|read_only_data_create_denied' working/w28a-732-r5/current/raw/g8-preprod-playwright-rerun2.log` | PASS |
| G8 four sentinel browser smokes | `working/w28a-732-r5/current/raw/g8-preprod-playwright-rerun2.log`; sentinel screenshots under `current/screenshots` | `sentinel_browser_smoke` status `200` for `chatclient0`, `expertagent0`, `notificationagent0`, `filemcpserver0` | `grep -c 'sentinel_browser_smoke' working/w28a-732-r5/current/raw/g8-preprod-playwright-rerun2.log` | PASS |
| G8 screenshot uniqueness | `working/w28a-732-r5/current/raw/g8-screenshot-md5s.txt` | ten unique screenshot MD5 hashes; duplicate command output empty | `md5sum working/w28a-732-r5/current/screenshots/*.png | awk '{print $1}' | sort | uniq -d` | PASS |
| Drift preprod runs latest registry image | `working/w28a-732-r5/current/raw/g6-image-push-redeploy-fix.log`; `working/w28a-732-r5/current/raw/g7-preprod-health-60s.log` | registry latest digest `sha256:6dbe97620981910af9d4871f5b98fa6d0ef37373a880194d7417a4ce0d0b137d`; remote image id `sha256:21fe6bc351db3e16ef1eb072b63b90513131319a7f43c2f4da49b94606e89435`; container healthy | `grep -E 'sha256:6dbe97620981910af9d4871f5b98fa6d0ef37373a880194d7417a4ce0d0b137d|image_id=sha256:21fe6bc351db3e16ef1eb072b63b90513131319a7f43c2f4da49b94606e89435|health=healthy' working/w28a-732-r5/current/raw/g6-image-push-redeploy-fix.log working/w28a-732-r5/current/raw/g7-preprod-health-60s.log` | PASS |
| Vault IaC parity and Vault read-only discipline | `working/w28a-732-r5/current/raw/g0-warrant-replay.txt`; `working/w28a-732-r5/current/raw/g7-terraform-apply-redeploy-fix.log` | Vault token lookup was read-only 200; Terraform used existing IaC config values and no Vault write path | `grep 'VAULT_OK token_lookup_status=200' working/w28a-732-r5/current/raw/g0-warrant-replay.txt && ! grep -Ei 'vault write|vault kv put|vault delete' working/w28a-732-r5/current/raw/*.log` | PASS |
| No coordinator-owned state mutation | `working/w28a-732-r5/current/touched-paths-manifest.tsv` | every listed path belongs to `db-mcp-server`; outside count zero by manifest query | `awk -F '\t' 'NR>1 && $2 !~ /db-mcp-server/ {bad=1} END {exit bad}' working/w28a-732-r5/current/touched-paths-manifest.tsv` | PASS |
| Scoped git status clean | `working/w28a-732-r5/current/scoped-clean-proof.txt` | required scoped status, unstaged diff, and staged diff commands recorded with empty final output | `grep -F 'git status --short --' working/w28a-732-r5/current/scoped-clean-proof.txt && grep -F 'git diff --name-only --' working/w28a-732-r5/current/scoped-clean-proof.txt && grep -F 'git diff --cached --name-only --' working/w28a-732-r5/current/scoped-clean-proof.txt` | PASS |
| Two-anchor service tags | `working/w28a-732-r5/current/raw/final-two-anchor-tags.log`; `working/w28a-732-r5/current/remote-proof.txt` | `W28A-732-R5-evidence` and `W28A-732-R5-final-proof` ancestor-proven on `origin/main` | `grep 'W28A-732-R5.*ANCESTOR_OF origin/main' working/w28a-732-r5/current/raw/final-two-anchor-tags.log` | PASS |
| Contract evidence self-rejection gate | `working/w28a-732-r5/current/CONTRACT-EVIDENCE-SELF-REJECTION-GATE.md` | `WAIVER_COUNT=0` and all rows `PASS` | `grep 'WAIVER_COUNT=0' working/w28a-732-r5/current/CONTRACT-EVIDENCE-SELF-REJECTION-GATE.md && awk -F '|' 'NR>2 && $NF !~ /PASS/ {bad=1} END {exit bad}' working/w28a-732-r5/current/CONTRACT-EVIDENCE-SELF-REJECTION-GATE.md` | PASS |
| Completion claim | `working/w28a-732-r5/current/FINAL-REPORT.md` | `HAVE_ALL_REQUIREMENTS_BEEN_MET: YES` and `WAIVER_COUNT=0` | `grep -E 'HAVE_ALL_REQUIREMENTS_BEEN_MET: YES|WAIVER_COUNT=0' working/w28a-732-r5/current/FINAL-REPORT.md` | PASS |

## Close Gate

The close gate is backed by the Evidence Matrix above, `requirements-map.tsv`, `CONTRACT-EVIDENCE-SELF-REJECTION-GATE.md`, and `CHECKSUMS.sha256`.

## RULES.md COMPLIANCE WARRANTY

I warrant that:
1. I have read RULES.md IN FULL before starting work
2. ALL code I produced is 100% compliant with EVERY section of RULES.md
3. ALL tests I produced or modified are 100% compliant with RULES.md § 5
4. ALL ST/IT/AT tests use REAL systems — ZERO stubs, mocks, or fake data (§ 5.5)
5. ZERO hardcoded values exist in my code, tests, or scripts (§ 2.4)
6. ALL credentials come from Vault or git-ignored private/ env files — ZERO stored credentials (§ 2.3, § 9.2)
7. I have NOT modified any file outside my project folder (§ 9.1)
8. I have NOT accessed any server not explicitly provided (§ 9.3)
9. I have NOT stored, copied, or exposed any credentials (§ 9.2)
10. ALL test results reported are REAL — exact pass/fail/skip counts from actual runs
11. I have NOT modified any infrastructure file (Vault config, Terraform, deployment manifests) without explicit instruction (§ 10)
12. ALL Vault paths I referenced were verified against live Vault before use (§ 11)
13. ALL requirements I claimed as "implemented" have working code and passing tests — no stubs, no placeholders (§ 12)

If ANY of the above cannot be truthfully stated, this warranty is VOID,
the completion claim is REJECTED, and ALL work must be reviewed.
