# requirements.lock — exception (W28A-861-R3)

A fully-resolved public-boundary `requirements.lock` cannot be produced for
`db-mcp-server` at this time. The blocker is recorded here per §6 of
`W28A-861-R3-PUBLICATION-PREP-EXTERNAL-BUILD-LEAKAGE-HARDENING-2026-06-07.md`
(record the exact command + error; do not silently omit it).

## Why

The service depends on seven Cloud-Dog platform packages
(`cloud_dog_config`, `cloud_dog_logging`, `cloud_dog_api_kit`,
`cloud_dog_idam`, `cloud_dog_jobs`, `cloud_dog_db`, `cloud-dog-storage`).
These are **not yet published to the public index (pypi.org)**. The §4 package
strategy for the public boundary is single-index `https://pypi.org/simple` with
**no** `--extra-index-url` (PS-97 §3.3). A lock that pins exact transitive
versions therefore cannot be resolved on the public boundary until the platform
packages are published there (handoff to the publication-loop lanes
W28A-862-R3 / W28A-865).

Producing a lock against the internal staging index instead would bake an
internal-host reference into a publishable artefact, which §5 forbids. So a lock
is deliberately NOT committed rather than committing an internal-host lock.

## NoSQL / SQL drivers stay as optional extras (not direct deps)

`db-mcp-server` does not list `pymongo`, `couchdb`, `couchbase`,
`cassandra-driver`, `elasticsearch`, `opensearch-py`, `psycopg`, `PyMySQL`, or
`SQLAlchemy` as direct dependencies. They are obtained transitively through
`cloud_dog_db[nosql,sql]>=0.3.0` (the `[nosql]` and `[sql]` extras of
`cloud_dog_db` 0.3.0, confirmed in its package metadata). The lockfile, once
producible, must preserve that: the drivers appear only as transitive
dependencies of the `cloud_dog_db` extras, never as top-level pins.

## Exact command attempted (Python 3.12 builder, single public index)

```
docker run --rm --network host python:3.12-slim \
  pip download --no-deps --dest /tmp/dl --index-url https://pypi.org/simple \
    "cloud_dog_db[nosql,sql]>=0.3.0" cloud_dog_config cloud_dog_logging \
    "cloud_dog_api_kit==0.12.4" cloud_dog_idam cloud_dog_jobs cloud-dog-storage
```

(pip 25.0.1, single public index `https://pypi.org/simple`, no extra-index-url.)

## Exact error

```
ERROR: Could not find a version that satisfies the requirement
  cloud_dog_db>=0.3.0 (from versions: none)
ERROR: No matching distribution found for cloud_dog_db>=0.3.0
```

The same failure applies to the other six `cloud_dog_*` / `cloud-dog-*`
packages — none are present on pypi.org.

## Reproducibility in the interim

Until the platform packages reach pypi.org, reproducibility is anchored by:

- `pyproject.toml` `[project].dependencies` — lower-bound pins on every
  third-party dependency, and the platform packages pinned by name
  (`cloud_dog_api_kit==0.12.4` exactly; the rest `>=`). The DB drivers are
  carried only via `cloud_dog_db[nosql,sql]>=0.3.0`.
- `Dockerfile.public` installs the seven platform packages by name from the
  configured single public index, then `pip install .` resolves the remaining
  third-party deps from the same index.
- `cloud-dog-api-kit==0.12.4` is the one version-sensitive platform package and
  is pinned exactly in both `pyproject.toml` and `Dockerfile.public`.

## Removal condition

Replace this file with a real `requirements.lock` once the seven
`cloud_dog_*` / `cloud-dog-*` packages are published to
`https://pypi.org/simple` (Cloud-Dog-External namespace). Re-run the exact
command above; it will then resolve, and a pinned `requirements.lock` becomes
the committed artefact.
