#!/usr/bin/env bash
set -euo pipefail
VERSION="${1:-latest}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_BUILDKIT=1 docker build \
  --network host \
  -t "cloud-dog/db-mcp-server:${VERSION}" \
  "${SCRIPT_DIR}"
