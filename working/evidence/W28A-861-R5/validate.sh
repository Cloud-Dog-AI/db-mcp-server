#!/usr/bin/env bash
set -uo pipefail; cd "$(git rev-parse --show-toplevel)" 2>/dev/null || cd "$(dirname "$0")/../../.."
E=working/evidence/W28A-861-R5; fail=0; ok(){ echo "PASS $1"; }; bad(){ echo "FAIL $1"; fail=$((fail+1)); }
for f in pyproject.toml requirements.lock Dockerfile.public; do grep -qE "cloud[-_]dog[-_]storage(\"|')?==0\.1\.4" "$f" && ! grep -qE "cloud[-_]dog[-_]storage[\"']?[ ]*>=" "$f" && ok "storage==0.1.4 $f" || bad "storage $f"; done
grep -qE "RUN mkdir -p config" Dockerfile.public && ! grep -qE "^COPY config/" Dockerfile.public && ok "N04 config mkdir (no COPY config/)" || bad "N04 config"
! grep -qE "(^|[^_])PYPI_URL" docker-build.sh && grep -qE "PIP_INDEX_URL" docker-build.sh && ok "OBS1 PIP_INDEX_URL" || bad "OBS1"
bash -n docker-build.sh && ok "bash -n docker-build.sh" || bad "bash -n"
grep -q 'db-mcp.example.com' ui/dist/runtime-config.example.js && ! grep -q 'dbmcp.cloud-dog.net' ui/dist/runtime-config.example.js && ok "leak scrubbed (ui/dist runtime-config.example.js)" || bad "leak scrub"
for f in 02-db-build-start-smoke.txt 03-publish-gate-leak-scrub.txt requirements-map.tsv final-report.md; do [ -s "$E/$f" ] && ok "evidence $f" || bad "evidence $f"; done
grep -q "CONFIG LOADED OK" "$E/02-db-build-start-smoke.txt" 2>/dev/null || grep -q "Health=healthy" "$E/02-db-build-start-smoke.txt" 2>/dev/null && ok "N04 start proof present" || bad "N04 start proof"
echo "----"; [ "$fail" -eq 0 ] && echo "FINAL_EVIDENCE_VALIDATOR: PASS failures=0" || echo "FINAL_EVIDENCE_VALIDATOR: FAIL failures=$fail"
