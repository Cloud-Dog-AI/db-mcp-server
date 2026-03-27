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
