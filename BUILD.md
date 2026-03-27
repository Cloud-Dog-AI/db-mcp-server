# Build Instructions

## Project
`db-mcp-server`

## Prerequisites
- Python `3.10+`
- Node.js `20+` and npm `10+` for the PS-30 UI app
- Docker
- Access to `https://pypi.cloud-dog.net/simple/`
- Vault bootstrap file: `/opt/iac/Development/cloud-dog-ai/env-vault`

## Local Development Setup
```bash
cd /opt/iac/Development/cloud-dog-ai/db-mcp-server
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -e ".[dev]" --index-url https://pypi.cloud-dog.net/simple/
set -a; source /opt/iac/Development/cloud-dog-ai/env-vault; set +a
```

## Run Locally
```bash
./server_control.sh --env tests/env-IT start all
./server_control.sh --env tests/env-IT status all
./server_control.sh --env tests/env-IT stop all
```

## Run Tests
```bash
.venv/bin/python -m pytest tests/quality --env tests/env-QT -q
.venv/bin/python -m pytest tests/unit --env tests/env-UT -q
.venv/bin/python -m pytest tests/system --env tests/env-ST -q
.venv/bin/python -m pytest tests/integration --env tests/env-IT -q
.venv/bin/python -m pytest tests/system/ST1.8_WebUiServing --env tests/env-ST-WEBUI -q
```

There are no application-tier pytest suites in this repo yet.

Connector-specific overlays are available in `tests/env-mongodb`, `tests/env-couchdb`, `tests/env-opensearch`, `tests/env-elasticsearch`, `tests/env-cassandra`, and `tests/env-all`.

## Build and Stage the Web UI Bundle
```bash
cd /opt/iac/Development/cloud-dog-ai/cloud-dog-ai-ui-monorepo
npm run build --workspace=apps/db-mcp

cd /opt/iac/Development/cloud-dog-ai/db-mcp-server
mkdir -p ui
rm -rf ui/dist
cp -r /opt/iac/Development/cloud-dog-ai/cloud-dog-ai-ui-monorepo/apps/db-mcp/dist ui/dist
```

## Docker Build
```bash
bash docker-build.sh latest
```

## Docker Push
```bash
docker push registry.cloud-dog.net:443/cloud-dog/db-mcp-server:latest
```

## Deploy to Preprod
No preprod Terraform workspace is assigned to `db-mcp-server` yet. Build and push the image first, then add the deployment workspace before documenting `terraform apply` here.

## Environment Files
- `tests/env-QT`, `tests/env-UT`, `tests/env-ST`, `tests/env-ST-WEBUI`, `tests/env-IT`
- connector overlays: `tests/env-mongodb`, `tests/env-couchdb`, `tests/env-opensearch`, `tests/env-elasticsearch`, `tests/env-cassandra`, `tests/env-all`
- defaults: `defaults.yaml`

## Dependencies
- FastAPI / Uvicorn / SQLAlchemy / PyJWT runtime
- connector clients: `pymongo`, `couchdb`, `opensearch-py`, `elasticsearch`, `cassandra-driver`
- See `pyproject.toml` for the full dependency set.
