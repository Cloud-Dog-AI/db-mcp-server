#!/usr/bin/env bash
set -euo pipefail

VERSION="${1:-latest}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTAINER="db-mcp-server"
FOLDER="cloud-dog"
REGISTRY="registry.cloud-dog.net:443"
PIP_CONF=".pip.conf.build"

PYPI_URL="${PYPI_URL:-https://pypi.cloud-dog.net/simple/}"
PYPI_USERNAME="${PYPI_USERNAME:-}"
PYPI_PASSWORD="${PYPI_PASSWORD:-}"

if [[ -z "${PYPI_USERNAME}" || -z "${PYPI_PASSWORD}" ]]; then
  if [[ -f /opt/iac/Development/cloud-dog-ai/env-vault ]]; then
    set -a; source /opt/iac/Development/cloud-dog-ai/env-vault; set +a
    VAULT_JSON=$(curl -fsS \
      -H "X-Vault-Token: ${VAULT_TOKEN}" \
      "${VAULT_ADDR}/v1/${VAULT_MOUNT_POINT}/data/${VAULT_CONFIG_PATH}" 2>/dev/null || echo "{}")
    readarray -t PYPI_CREDS < <(VAULT_JSON_PAYLOAD="${VAULT_JSON}" python3 - <<'PY'
import json, os
raw = os.environ.get("VAULT_JSON_PAYLOAD", "{}")
payload = json.loads(raw).get("data", {}).get("data", {})
if isinstance(payload.get("json"), dict):
    dev = payload["json"].get("dev", {})
elif isinstance(payload.get("json"), str):
    dev = json.loads(payload["json"]).get("dev", {})
elif isinstance(payload.get("content"), str):
    dev = json.loads(payload["content"]).get("dev", {})
else:
    dev = payload.get("dev", {}) if isinstance(payload, dict) else {}
repo = dev.get("repository", {}) if isinstance(dev, dict) else {}
pypi = repo.get("pypi", {}) if isinstance(repo, dict) else {}
print(pypi.get("username", ""))
print(pypi.get("password", ""))
PY
    ) || true
    PYPI_USERNAME="${PYPI_CREDS[0]:-}"
    PYPI_PASSWORD="${PYPI_CREDS[1]:-}"
  fi
fi

if [[ -n "${PYPI_USERNAME}" && -n "${PYPI_PASSWORD}" ]]; then
  cat > "${PIP_CONF}" << EOF
[global]
extra-index-url = https://${PYPI_USERNAME}:${PYPI_PASSWORD}@${PYPI_URL#https://}
trusted-host = $(python3 -c "from urllib.parse import urlsplit; print(urlsplit('${PYPI_URL}').hostname or 'pypi.cloud-dog.net')")
               files.pythonhosted.org
EOF
else
  cat > "${PIP_CONF}" << EOF
[global]
extra-index-url = ${PYPI_URL}
trusted-host = $(python3 -c "from urllib.parse import urlsplit; print(urlsplit('${PYPI_URL}').hostname or 'pypi.cloud-dog.net')")
               files.pythonhosted.org
EOF
fi
chmod 600 "${PIP_CONF}"

DOCKER_BUILDKIT=1 docker buildx build \
  --progress=plain \
  --network=host \
  --load \
  -f Dockerfile \
  --secret id=pip_conf,src="${PIP_CONF}" \
  -t "${FOLDER}/${CONTAINER}:${VERSION}" \
  "${SCRIPT_DIR}"

docker tag "${FOLDER}/${CONTAINER}:${VERSION}" \
  "${REGISTRY}/${FOLDER}/${CONTAINER}:${VERSION}"

rm -f "${PIP_CONF}"
