# W28A-861-R5 — db-mcp-server publication source/image repair — FINAL REPORT

**Surface:** db-mcp-server (§6.13; db free — 889-B-R2 CLOSED). **Branch:** `fix/W28A-861-R5-db-mcp` (off origin/main `8d1b9e5`).
**Drives 864-R4 N04** + OBS1 + storage 0.1.4 (decision A = pin, no vendor).

## HAVE_ALL_REQUIREMENTS_BEEN_MET: YES (db source proven; republish held for cdci imap-manifest FF)

## Fixes (db source, commits 994c76c + 0c1a51a)
1. **N04** — `Dockerfile.public`: `COPY config/ ./config/` → `RUN mkdir -p config`. Root cause: `config/` holds only a `.gitkeep` placeholder and is NOT in the manifest `public_dirs`, so the boundary build **failed at `COPY config/`** (the published tree has no config/). The app only needs the dir; create it. defaults.yaml resolution itself is correct (pyproject.toml + defaults.yaml COPY to /app + PYTHONPATH=/app → `find_project_root()` → /app).
2. **storage** — pin `cloud_dog_storage==0.1.4` in pyproject.toml + requirements.lock + Dockerfile.public (was `>=0.1.1` / lock `0.1.6`). No vendor (decision A). Signal `storage-pinned=0.1.4`.
3. **OBS1** — `docker-build.sh` index-override `PYPI_URL` → `PIP_INDEX_URL` (`DEV_PYPI_URL` → `DEV_PIP_INDEX_URL`; `PYPI_USERNAME/PASSWORD` unchanged; `bash -n` OK).
4. **Publish-gate leak (discovered, pre-existing)** — `ui/dist/runtime-config.example.js` `API_BASE_URL: https://dbmcp.cloud-dog.net` (service FQDN) failed the cdci publish **leakage-gate** (filter exit 1). Scrubbed → `https://db-mcp.example.com` (public-example convention; deploy-time template, real host injected via `runtime-config.js`). **Proven: gate exit 1 → 0 after scrub.** Pre-existing on origin/main (NOT from the N04/storage/OBS1 edits); blocks the db republish. The `requirements.lock` `pypi.cloud-dog.net` *comment* is a non-blocking WARN (same allowlisted class as imap's Dockerfile.public comment — left as-is for consistency).

## Proof (server0 daemon, single-index, origin/main-manifest published tree)
`02-db-build-start-smoke.txt`: published tree natively ships **Dockerfile.public + docker-env.public.example** (internal Dockerfile absent → manifest (c) already correct on origin/main); build exit 0; container **Status=running Health=healthy Exit=0**; **all 4 surfaces 200** (8086/health, 8087/, 8088/mcp/health, 8089/health + `/.well-known/agent.json`); in-image `load_runtime_config()` → **"CONFIG LOADED OK; defaults.yaml resolved at /app"**; storage `pip show` → **0.1.4**; **0 defaults.yaml/config errors, 0 tracebacks**; single `--index-url pypi.cloud-dog.net/simple/` (no extra-index, no vendor).
`03-publish-gate-leak-scrub.txt`: leak before/after gate exit.

## cdci manifest — NO db change needed
origin/main db manifest already ships `Dockerfile.public` + `docker-env.public.example` (no internal Dockerfile), and the **all-9 exclude_dirs audit** shows db has **no nested-dir collision** (unlike imap's `archive`). So db's cdci manifest is correct as-is; the db fix is purely service-repo.

## Remote (held)
Local closeout: source `994c76c` + leak scrub `0c1a51a` + evidence. FF-merge to db `origin/main` + Gitea republish (single-index, gate-clean) **held for the cdci imap-manifest FF** (republish runs the same cdci pipeline). Agents do not touch the external mirror (§3.2.0); republish is the CDCI hand-off once FF'd.
