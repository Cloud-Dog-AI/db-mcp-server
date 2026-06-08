# W28A-861-R3 — db-mcp public-build prep — final report

Service: **db-mcp** (`db-mcp-server`)
Worktree: `/opt/iac/Development/cloud-dog-ai/.w28a861r3-db-mcp`
Branch: `fix/W28A-861-R3-db-mcp` (off `origin/main` @ 5c2086e)

## Mandatory reading (versions cited)
- RULES.md v2.7 — §3.2.0 Gitea exclusivity, §3.2.3/§5.6 shared-test-backend reuse.
- AGENT-LESSONS.md v3.17 (2026-06-07).
- AGENT-BOOTSTRAP-DIRECTIVE.md v5.3 (2026-06-01).
- PLATFORM-TLS-PROXY-GUIDANCE.md (no version header; public variant ships no private CA).
- PS-97 (97-gitea-github-isolation.md) v1.1 (2026-04-23) — §1.1.3 Dockerfile split,
  §1.1.4 env split, §3.3 single-index/no-extra-index-url, §3.4 no vendored wheels.
- W28A-861-R3-PUBLICATION-PREP-EXTERNAL-BUILD-LEAKAGE-HARDENING-2026-06-07.md — §4 (public=pypi.org),
  §5 (leakage), §6 (lockfile/exception).

## §4 package-index decision (implemented)
- public boundary: single index `https://pypi.org/simple` + GitHub-mirrored platform packages.
- dev boundary: caller-supplied internal staging index (PYPI_URL/DEV_PYPI_URL); no internal host
  hard-coded in the published `docker-build.sh`.
- index via build ARG (`PUBLIC_PYPI_INDEX_URL`); never `--extra-index-url`; never an internal host
  in any published file.

## Ports + prefix (DERIVED, source = defaults.yaml)
API 8086 (/v1), Web 8087 (/), MCP 8088 (/mcp), A2A 8089 (/a2a). Env prefix `CLOUD_DOG__`
with `__` delimiter, no service segment (e.g. api_server.port -> CLOUD_DOG__API_SERVER__PORT).

## NoSQL §1.4 handling
db-mcp src imports the drivers directly (pre-existing §1.4 condition — NOT changed here).
Dependency strategy switched to the W28E-606 canonical extras form: drivers come transitively
via `cloud_dog_db[nosql,sql]>=0.3.0`; zero direct nosql/sql driver deps in pyproject. Confirmed
against cloud_dog_db 0.3.0 metadata (nosql/sql/mongodb/couchdb/cassandra/elasticsearch/opensearch
extras present). Verified: 0 direct driver deps (08-py-compile.txt).

## Deliverables
- Dockerfile.public — multi-stage public build; single index via ARG; installs
  cloud_dog_db[nosql,sql] extras; no private CA; no vendor COPY (PS-97 §3.4).
- docker-env.public.example — *.example.com placeholders, no internal hosts/Vault.
- EXTERNAL-BUILD.md — Docker + pure-source paths; Linux/macOS/Windows; evidence return.
- docker-build.sh — `--variant public|dev`; public default pypi.org single-index;
  dev requires caller-supplied index (no hard-coded internal host).
- requirements.lock.EXCEPTION.md — honest pip command + error (platform pkgs absent on pypi.org).
- pyproject.toml — extras-not-direct-deps; RULES.md dropped from sdist; public files added.
- .publish-exclude / .dockerignore — exclude AGENT-LESSONS.md, RULES.md, vendor/,
  scripts/validate-vault.sh, dev Dockerfile from the public mirror.
- Leakage scrubs in README, BUILD, docs/PARAMETERS, docs/ENV-REFERENCE, docs/REQUIREMENTS,
  docs/BACKLOG, ui/dist/runtime-config.example.js, and 7 test fixtures/helpers.

## Leakage: BEFORE 37 -> AFTER 0 (publishable tree)
07-leakage-before.txt / 07-leakage-after.txt. The dev `Dockerfile` (internal staging index)
is reclassified as an explicitly non-published internal file via `.publish-exclude`
(PS-97 §1.1.3 / W28A-861-R3 §5 carve-out).

## Build attempt (honest, server2)
`PYPI_URL=https://pypi.org/simple PUBLICATION_TAG_SUFFIX=github-test ./docker-build.sh latest --variant public`
Reached the platform-package install layer using a single pypi.org index (0 extra-index-url in
the build log) and failed exactly at `No matching distribution found for cloud-dog-config`
(`from versions: none`) — the documented EXCEPTION blocker. Base image, apt, COPY, pip-upgrade
all succeeded; the `cloud_dog_db[nosql,sql]>=0.3.0` requirement parsed correctly. See
08-build-attempt.txt / 08-docker-build-full.log.

## R2 regression preservation
PUBLICATION-SMOKE.md does not reference cdci/scripts/publication-smoke.sh; server_control.sh +
start_*.py present at the paths server_control uses; env-file name consistent (.env.example /
docker-env.public.example).
