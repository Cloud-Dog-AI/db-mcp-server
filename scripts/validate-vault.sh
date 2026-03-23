#!/usr/bin/env bash
set -euo pipefail
if [ -z "${VAULT_ADDR:-}" ] || [ -z "${VAULT_TOKEN:-}" ] || [ -z "${VAULT_MOUNT_POINT:-}" ] || [ -z "${VAULT_CONFIG_PATH:-}" ]; then
  echo "Vault environment not loaded. Source /opt/iac/Development/cloud-dog-ai/env-vault first." >&2
  exit 1
fi
echo "Vault environment variables are present for db-mcp-server planning tasks."
