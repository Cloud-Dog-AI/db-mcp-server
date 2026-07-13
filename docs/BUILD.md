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
doc-last-updated: 2026-07-13T00:00:00Z
doc-git-commit: 58fb399bb2ba144e262f97293103a7a0a19ba05d
doc-git-branch: main
doc-source-shas: []
doc-age-policy: 90d
doc-conformance-stamp: 2026-06-18T00:00:00Z
---

# db-mcp-server — Build

## Current status
The API, WebUI, MCP, and A2A runtime is implemented. Python 3.13 is mandatory
for container builds and project-local development/tests.

## Local development setup
```bash
cd ./db-mcp-server
python3.13 -m venv .venv
.venv/bin/python --version  # must report Python 3.13.x
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -e ".[dev]" --index-url https://your-package-index/simple/
```

The project-local quality and runtime contract is exposed through stable targets:

```bash
make runtime-preflight
make lint
```

## Docker build
```bash
bash docker-build.sh latest --variant dev
```

## Planned test commands
```bash
.venv/bin/python -m pytest tests/quality --env tests/env-QT -q
.venv/bin/python -m pytest tests/unit --env tests/env-UT -q
.venv/bin/python -m pytest tests/system --env tests/env-ST -q
.venv/bin/python -m pytest tests/integration --env tests/env-IT -q
.venv/bin/python -m pytest tests/application --env tests/env-AT -q
```
