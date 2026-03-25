#!/usr/bin/env bash
set -euo pipefail
VERSION="${1:-latest}"
WORKSPACE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOCKER_BUILDKIT=1 docker build \
  --network host \
  -f "${WORKSPACE_ROOT}/db-mcp-server/Dockerfile" \
  -t "cloud-dog/db-mcp-server:${VERSION}" \
  "${WORKSPACE_ROOT}"
