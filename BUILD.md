# Build Instructions

## Project
`db-mcp-server` - database access and catalog service with API, Web, MCP, and A2A servers.

## Prerequisites
- Python 3.12+
- Node.js 20+ and npm 10+ for the UI bundle
- Docker

## Development Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"
```

If platform dependencies are served from a package index rather than editable local source:
```bash
PYPI_URL=https://gitea.cloud-dog.net/api/packages/Cloud-Dog-External/pypi/simple
pip install -e ".[dev]" --extra-index-url "$PYPI_URL"
```

## Local Configuration
```bash
cat > .env.local <<'ENV'
API_SERVER_PORT=8086
WEB_SERVER_PORT=8087
MCP_SERVER_PORT=8088
A2A_SERVER_PORT=8089
METADATA_STORE_URI=sqlite:///./data/dbmcp_metadata.db
AUDIT_STORE_URI=sqlite:///./data/dbmcp_audit.db
ENV
```

## Run Locally
```bash
./server_control.sh --env ./.env.local start all
./server_control.sh --env ./.env.local status all
./server_control.sh --env ./.env.local stop all
```

## Run Tests
```bash
.venv/bin/python -m pytest tests/quality -v
.venv/bin/python -m pytest tests/unit -v
.venv/bin/python -m pytest tests/system -v
.venv/bin/python -m pytest tests/integration -v
```

## Build
### Python Package
```bash
python -m pip install build
python -m build
```

### UI Bundle
The exported tree includes the UI files used by the Docker build. Rebuild the UI only if you maintain a separate UI source tree.

### Docker Container
The provided script builds from the parent workspace as the Docker context:
```bash
PUBLICATION_TAG_SUFFIX=gitea-test ./docker-build.sh latest
```

Equivalent direct Docker invocation:
```bash
DOCKER_BUILDKIT=1 docker build --network host -f ./Dockerfile -t registry.example.com/team/db-mcp-server:latest ..
```

## Docker Push
```bash
docker tag cloud-dog/db-mcp-server:latest registry.example.com/team/db-mcp-server:latest
docker push registry.example.com/team/db-mcp-server:latest
```

## Configuration
Runtime configuration comes from the env file passed to `server_control.sh`, then any higher-priority shell variables, then `defaults.yaml`.

## Local Secrets
Put local-only values in the env file passed to `server_control.sh` or mounted into Docker. Do not commit real credentials.
