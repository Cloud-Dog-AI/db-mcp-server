#!/usr/bin/env bash
set -euo pipefail
VERSION="${1:-latest}"
echo "db-mcp-server planning skeleton build"
docker build -t "cloud-dog/db-mcp-server:${VERSION}" .
