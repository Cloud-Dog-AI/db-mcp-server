---
template-id: T-BLR
template-version: 1.0
applies-to: BUILD.md
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

# Build Instructions

## Project
`db-mcp-server` - database access and catalog service with API, Web, MCP, and A2A servers.

## Prerequisites
- Python 3.13 (the project-local and container runtime floor)
- Node.js 20+ and npm 10+ for the UI bundle
- Docker

## Development Setup
```bash
python3.13 -m venv .venv
source .venv/bin/activate
python --version  # must report Python 3.13.x
pip install --upgrade pip
pip install -e ".[dev]"
```

If platform dependencies are served from a package index rather than editable local source,
use a single index (no `--extra-index-url`; PS-97 §3.3 / W28A-861-R3 §4):
```bash
PYPI_URL=https://pypi.org/simple
pip install -e ".[dev]" --index-url "$PYPI_URL"
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
.venv/bin/python -m pytest tests/quality --env tests/env-QT -v
.venv/bin/python -m pytest tests/unit --env tests/env-UT -v
.venv/bin/python -m pytest tests/system --env tests/env-ST -v
.venv/bin/python -m pytest tests/integration --env tests/env-IT -v
.venv/bin/python -m pytest tests/application --env tests/env-AT -v
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
The provided script builds with this repository as the Docker context. Use the
public variant for publication (single public index, no internal hosts):
```bash
./docker-build.sh latest --variant public
# or a throwaway publication-test image:
PUBLICATION_TAG_SUFFIX=github-test ./docker-build.sh latest --variant public
```

The sanctioned path copies the corporate CA into the build context, mounts the
single-index pip configuration as a BuildKit secret, and removes both afterwards.
Do not bypass it with a direct `docker build` for internal delivery.

Equivalent public-boundary invocation requires the same temporary CA preparation:
```bash
cp /usr/local/share/ca-certificates/cloud-dog.net.ca.crt ./custom-ca.crt
DOCKER_BUILDKIT=1 docker build --network host -f ./Dockerfile.public \
  --build-arg CUSTOM_CA_CERT=custom-ca.crt \
  --build-arg PUBLIC_PYPI_INDEX_URL=https://pypi.org/simple \
  -t registry.example.com/team/db-mcp-server:latest .
rm -f ./custom-ca.crt
```

See [EXTERNAL-BUILD.md](EXTERNAL-BUILD.md) for the full external-builder guide.

## Docker Push
```bash
docker tag cloud-dog/db-mcp-server:latest registry.example.com/team/db-mcp-server:latest
docker push registry.example.com/team/db-mcp-server:latest
```

## Configuration
Runtime configuration comes from the env file passed to `server_control.sh`, then any higher-priority shell variables, then `defaults.yaml`.

## Local Secrets
Put local-only values in the env file passed to `server_control.sh` or mounted into Docker. Do not commit real credentials.
