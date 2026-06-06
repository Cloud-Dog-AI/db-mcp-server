#!/usr/bin/env bash
set -euo pipefail

VERSION="${1:-latest}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTAINER="db-mcp-server"
FOLDER="cloud-dog"
REGISTRY="${REGISTRY:-}"
PIP_CONF=".pip.conf.build"

PUBLICATION_TAG_SUFFIX="${PUBLICATION_TAG_SUFFIX:-}"
if [[ -n "${PUBLICATION_TAG_SUFFIX}" ]]; then
  if [[ ! "${PUBLICATION_TAG_SUFFIX}" =~ ^[a-z0-9]([a-z0-9-]*[a-z0-9])?$ ]]; then
    echo "ERROR: PUBLICATION_TAG_SUFFIX must match ^[a-z0-9]([a-z0-9-]*[a-z0-9])?\$ (got: '${PUBLICATION_TAG_SUFFIX}')" >&2
    exit 2
  fi
  case "${PUBLICATION_TAG_SUFFIX}" in
    latest|dev|prod|release|stable)
      echo "ERROR: PUBLICATION_TAG_SUFFIX '${PUBLICATION_TAG_SUFFIX}' is reserved" >&2
      exit 2
      ;;
  esac
  EFFECTIVE_TAG="${VERSION}-${PUBLICATION_TAG_SUFFIX}"
  echo "Publication test build: tag suffix '-${PUBLICATION_TAG_SUFFIX}' (registry tag will be skipped)."
else
  EFFECTIVE_TAG="${VERSION}"
fi

PYPI_URL="${PYPI_URL:-https://gitea.cloud-dog.net/api/packages/Cloud-Dog-External/pypi/simple}"
PYPI_USERNAME="${PYPI_USERNAME:-}"
PYPI_PASSWORD="${PYPI_PASSWORD:-}"

if [[ -n "${PYPI_USERNAME}" && -n "${PYPI_PASSWORD}" ]]; then
  cat > "${PIP_CONF}" << EOF
[global]
extra-index-url = https://${PYPI_USERNAME}:${PYPI_PASSWORD}@${PYPI_URL#https://}
trusted-host = $(python3 -c "from urllib.parse import urlsplit; print(urlsplit('${PYPI_URL}').hostname or 'gitea.cloud-dog.net')")
               files.pythonhosted.org
EOF
else
  cat > "${PIP_CONF}" << EOF
[global]
extra-index-url = ${PYPI_URL}
trusted-host = $(python3 -c "from urllib.parse import urlsplit; print(urlsplit('${PYPI_URL}').hostname or 'gitea.cloud-dog.net')")
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
  -t "${FOLDER}/${CONTAINER}:${EFFECTIVE_TAG}" \
  "${SCRIPT_DIR}"

if [[ -n "${REGISTRY}" && -z "${PUBLICATION_TAG_SUFFIX}" ]]; then
  docker tag "${FOLDER}/${CONTAINER}:${EFFECTIVE_TAG}" \
    "${REGISTRY}/${FOLDER}/${CONTAINER}:${EFFECTIVE_TAG}"
elif [[ -n "${PUBLICATION_TAG_SUFFIX}" ]]; then
  echo "Registry tag skipped for publication suffix '${PUBLICATION_TAG_SUFFIX}'."
else
  echo "Registry tag skipped; set REGISTRY to tag a registry image."
fi

rm -f "${PIP_CONF}"
