---
template-id: T-EXT
template-version: 1.0
applies-to: EXTERNAL-BUILD.md
registry: service
required: must-have
when-applicable: ""
template-last-updated: 2026-06-12
template-owner: platform-standards

project: db-mcp-server
doc-last-updated: 2026-06-18T00:00:00Z
doc-git-commit: 58fb399bb2ba144e262f97293103a7a0a19ba05d
doc-git-branch: main
doc-source-shas: []
doc-age-policy: 90d
doc-conformance-stamp: 2026-06-18T00:00:00Z
---

# External Build Guide — db-mcp-server

This document lets an external builder build, run, and smoke-test
`db-mcp-server` from this published source tree alone, using only public
package sources. It assumes **no** access to any internal Cloud-Dog host,
registry, package index, or secret store.

## Package source strategy

- All third-party Python dependencies resolve from **public PyPI**
  (`https://pypi.org/simple`).
- Cloud-Dog platform packages (`cloud-dog-config`, `cloud-dog-logging`,
  `cloud-dog-api-kit`, `cloud-dog-idam`, `cloud-dog-db`, `cloud-dog-jobs`,
  `cloud-dog-storage`) must be available on the index you point the build at.
  On the public boundary they are published to public PyPI (Cloud-Dog-External
  namespace) or installed from the GitHub-mirrored source. If a platform
  package is not yet on your index, **stop and report the gap** — do not add a
  second index (`--extra-index-url`) as a workaround (PS-97 §3.3 / §4).
- A single index is used throughout. The default is `https://pypi.org/simple`.

### NoSQL / SQL drivers come via extras, not directly

`db-mcp-server` does **not** depend on `pymongo`, `couchdb`, `couchbase`,
`cassandra-driver`, `elasticsearch`, `opensearch-py`, `psycopg`, `PyMySQL`, or
`SQLAlchemy` directly. All database access goes through the `cloud_dog_db`
platform package, and the drivers are pulled transitively through its
**optional extras**:

- `cloud-dog-db[sql]` — PostgreSQL + MariaDB/MySQL
- `cloud-dog-db[nosql]` — MongoDB, CouchDB, Couchbase, Cassandra,
  Elasticsearch, OpenSearch, pgvector

`Dockerfile.public` installs `cloud-dog-db[nosql,sql]==0.3.3`, which is the only
supported way to obtain the drivers. Do not add the raw drivers to a build.

## Prerequisites

| Component | Minimum | Notes |
|-----------|---------|-------|
| Docker    | 24+     | BuildKit enabled (default in 24+). Required for the container path. |
| Python    | 3.12    | Required only for the pure-source path and the lockfile check. |
| Node.js   | 20+     | Only if you rebuild the UI bundle. The published tree ships a prebuilt `ui/dist/`. |
| OS        | Linux, macOS, or Windows | Docker path is identical on all three. Shell snippets below are bash; on Windows use WSL2 or Git Bash. |

## Path A — Docker (recommended)

```bash
# 1. Build the public image. The default index is public PyPI.
./docker-build.sh latest --variant public

# Or with an explicit single index:
PYPI_URL=https://pypi.org/simple ./docker-build.sh latest --variant public
```

The build produces `cloud-dog/db-mcp-server:latest`. To build a throwaway,
registry-skipping publication-test image instead:

```bash
PUBLICATION_TAG_SUFFIX=github-test ./docker-build.sh latest --variant public
# image tag: cloud-dog/db-mcp-server:latest-github-test
```

### Smoke test

Run the shell block in [PUBLICATION-SMOKE.md](PUBLICATION-SMOKE.md). It starts
the image with the checked-in [docker-env.public.example](docker-env.public.example)
mounted at `/app/env` and probes the API, Web, MCP, and A2A surfaces:

```bash
TAG=latest bash -c "$(sed -n '/^```bash$/,/^```$/p' PUBLICATION-SMOKE.md | sed '1d;$d')"
```

Expected: `RESULT: PASS`. Auth-gated `401/403` and redirect `3xx` responses
count as PASS because they prove the surface is up and routing. The smoke runs
with SQLite metadata/audit stores and no live database backends, so connector
endpoints need not be reachable.

## Path B — Pure source (no Docker)

```bash
# Linux / macOS
python3.13 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip

# Windows (PowerShell)
#   py -3.13 -m venv .venv
#   .venv\Scripts\Activate.ps1
#   python -m pip install --upgrade pip

# Single public index, no extra-index-url. The [nosql,sql] extras on
# cloud_dog_db (declared in pyproject.toml) pull the DB drivers transitively.
pip install --index-url https://pypi.org/simple -e .

# Provide a local env file (see docker-env.public.example for all keys):
cp docker-env.public.example .env.local
# edit .env.local: at minimum set CLOUD_DOG__AUTH__API_KEY; the SQLite stores
# and ports already default to working values.
mkdir -p ./data ./logs

# Run all four surfaces:
./server_control.sh --env ./.env.local start all
./server_control.sh --env ./.env.local status all

# Probe:
curl -sS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8086/health

# Stop:
./server_control.sh --env ./.env.local stop all
```

## Ports

| Port | Surface | Env key | Base path |
|------|---------|---------|-----------|
| 8086 | API     | `CLOUD_DOG__API_SERVER__PORT` | `/v1` |
| 8087 | Web UI  | `CLOUD_DOG__WEB_SERVER__PORT` | `/` |
| 8088 | MCP     | `CLOUD_DOG__MCP_SERVER__PORT` | `/mcp` |
| 8089 | A2A     | `CLOUD_DOG__A2A_SERVER__PORT` | `/a2a` |

(Source: `defaults.yaml` `api_server.port` / `web_server.port` /
`mcp_server.port` / `a2a_server.port`.)

## Environment

Env keys map onto `defaults.yaml` using the `CLOUD_DOG__` prefix with `__` as
the section delimiter (e.g. `api_server.port` → `CLOUD_DOG__API_SERVER__PORT`).
See [docker-env.public.example](docker-env.public.example) for the full set with
public placeholders. No internal host, registry, Vault path, or local absolute
filesystem path is required to build or run.

## Returning evidence

Place all build/smoke evidence under `evidence/external-build/` in your working
copy:

- `build.log` — full output of `docker-build.sh` (or the `pip install`).
- `image-digest.txt` — `docker inspect --format '{{.Id}}' cloud-dog/db-mcp-server:latest`.
- `smoke.log` — full output of the PUBLICATION-SMOKE run (must end `RESULT: PASS`).
- `pip-index-check.txt` — proof the build used a single index and no
  `--extra-index-url` (e.g. `grep -n 'index-url' build.log`).

Then produce a tarball and checksum and return both:

```bash
tar czf db-mcp-external-build-evidence.tgz evidence/external-build/
sha256sum db-mcp-external-build-evidence.tgz > db-mcp-external-build-evidence.tgz.sha256
```

Report any dependency-resolution gap (missing platform package on your index)
verbatim, with the failing `pip` line. Do not work around it with a second index.
