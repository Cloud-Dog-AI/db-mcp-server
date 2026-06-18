---
template-id: T-BLD
template-version: 1.0
applies-to: docs/BUILD.md
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

# db-mcp-server — Build

## Current status
Build scaffolding only. Runtime implementation is not present yet.

## Local development setup
```bash
cd ./db-mcp-server
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -e ".[dev]" --index-url https://your-package-index/simple/
```

## Docker build
```bash
bash docker-build.sh latest
```

## Planned test commands
```bash
pytest tests/quality --env tests/env-QT -q
pytest tests/unit --env tests/env-UT -q
pytest tests/system --env tests/env-ST -q
pytest tests/integration --env tests/env-IT -q
pytest tests/application --env tests/env-AT -q
```
