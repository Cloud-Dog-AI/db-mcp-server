#!/usr/bin/env bash
# Copyright 2026 Cloud-Dog, Viewdeck Engineering Limited
# Licensed under the Apache License, Version 2.0
#
# db-mcp-server — Docker Build Script (PS-91 / PS-97 v1.1 §1.1.3)
# Uses a BuildKit secret mount for optional PyPI auth — credentials never enter
# image layers.
#
# Variant selector (PS-97 v1.1 §1.1.3):
#   --variant public  (default) builds Dockerfile.public for publication.
#                      Single public index (PIP_INDEX_URL defaults to pypi.org),
#                      no --extra-index-url, no internal-host default
#                      (W28A-861-R3 §4).
#   --variant dev      builds the internal Dockerfile (internal staging package
#                      index default) for developer checkouts.
#
# Usage:
#   docker-build.sh [VERSION] [--variant dev|public]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Argument parsing ────────────────────────────────────────────
VARIANT="${PUBLICATION_BUILD_VARIANT:-public}"
POSITIONAL=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --variant)
      VARIANT="${2:-dev}"
      shift 2
      ;;
    --variant=*)
      VARIANT="${1#*=}"
      shift
      ;;
    *)
      POSITIONAL+=("$1")
      shift
      ;;
  esac
done
set -- "${POSITIONAL[@]}"

case "${VARIANT}" in
  dev)
    DOCKERFILE="Dockerfile"
    ;;
  public)
    DOCKERFILE="Dockerfile.public"
    ;;
  *)
    echo "ERROR: --variant must be 'dev' or 'public' (got: ${VARIANT})" >&2
    exit 2
    ;;
esac
if [[ ! -f "${SCRIPT_DIR}/${DOCKERFILE}" ]]; then
  echo "ERROR: ${DOCKERFILE} not found (variant=${VARIANT})" >&2
  exit 2
fi

VERSION="${1:-latest}"
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

echo "=========================================="
echo "Docker Build: ${FOLDER}/${CONTAINER}:${EFFECTIVE_TAG} (variant=${VARIANT}, dockerfile=${DOCKERFILE})"
echo "=========================================="

# ── PyPI Configuration ───────────────────────────────────────────
# Default index depends on variant:
#   public → public PyPI (single index, no extra-index-url; PS-97 §3.3 / §4).
#   dev    → caller-supplied internal staging mirror (set PIP_INDEX_URL or DEV_PIP_INDEX_URL;
#            no internal host is hard-coded in this published script — §5).
if [[ -n "${PIP_INDEX_URL:-}" ]]; then
  : # honour caller override
elif [[ "${VARIANT}" == "public" ]]; then
  PIP_INDEX_URL="https://pypi.org/simple"
elif [[ -n "${DEV_PIP_INDEX_URL:-}" ]]; then
  PIP_INDEX_URL="${DEV_PIP_INDEX_URL}"
else
  echo "ERROR: --variant dev requires PIP_INDEX_URL or DEV_PIP_INDEX_URL (internal index)." >&2
  echo "       The public-build path is: ./docker-build.sh latest --variant public" >&2
  exit 2
fi
PYPI_USERNAME="${PYPI_USERNAME:-}"
PYPI_PASSWORD="${PYPI_PASSWORD:-}"

PYPI_HOST="$(python3 -c "from urllib.parse import urlsplit; print(urlsplit('${PIP_INDEX_URL}').hostname or 'pypi.org')")"

if [[ "${VARIANT}" == "public" ]]; then
  # Single strict index — no extra-index-url (PS-97 §3.3 / §4).
  if [[ -n "${PYPI_USERNAME}" ]] && [[ -n "${PYPI_PASSWORD}" ]]; then
    cat > "${SCRIPT_DIR}/${PIP_CONF}" << EOF
[global]
index-url = https://${PYPI_USERNAME}:${PYPI_PASSWORD}@${PIP_INDEX_URL#https://}
trusted-host = ${PYPI_HOST}
EOF
    echo "pip.conf: public variant, authenticated single-index access (${PYPI_HOST})."
  else
    cat > "${SCRIPT_DIR}/${PIP_CONF}" << EOF
[global]
index-url = ${PIP_INDEX_URL}
trusted-host = ${PYPI_HOST}
EOF
    echo "pip.conf: public variant, anonymous single-index access (${PYPI_HOST})."
  fi
else
  # Dev variant — internal Dockerfile uses public PyPI as primary index plus the
  # internal mirror as extra-index-url for platform packages.
  if [[ -n "${PYPI_USERNAME}" ]] && [[ -n "${PYPI_PASSWORD}" ]]; then
    cat > "${SCRIPT_DIR}/${PIP_CONF}" << EOF
[global]
extra-index-url = https://${PYPI_USERNAME}:${PYPI_PASSWORD}@${PIP_INDEX_URL#https://}
trusted-host = ${PYPI_HOST}
               files.pythonhosted.org
EOF
    echo "pip.conf: dev variant, authenticated mirror access (${PYPI_HOST})."
  else
    cat > "${SCRIPT_DIR}/${PIP_CONF}" << EOF
[global]
extra-index-url = ${PIP_INDEX_URL}
trusted-host = ${PYPI_HOST}
               files.pythonhosted.org
EOF
    echo "pip.conf: dev variant, anonymous mirror access (${PYPI_HOST})."
  fi
fi
chmod 600 "${SCRIPT_DIR}/${PIP_CONF}"

# ── Build ────────────────────────────────────────────────────────
DOCKER_BUILDKIT=1 docker buildx build \
  --progress=plain \
  --network=host \
  --load \
  -f "${SCRIPT_DIR}/${DOCKERFILE}" \
  --secret id=pip_conf,src="${SCRIPT_DIR}/${PIP_CONF}" \
  --build-arg PUBLIC_PYPI_INDEX_URL="${PIP_INDEX_URL}" \
  --build-arg PIP_INDEX_URL="${PIP_INDEX_URL}" \
  --build-arg HTTP_PROXY="${HTTP_PROXY:-}" \
  --build-arg HTTPS_PROXY="${HTTPS_PROXY:-}" \
  --build-arg NO_PROXY="${NO_PROXY:-}" \
  --build-arg http_proxy="${http_proxy:-}" \
  --build-arg https_proxy="${https_proxy:-}" \
  --build-arg no_proxy="${no_proxy:-}" \
  -t "${FOLDER}/${CONTAINER}:${EFFECTIVE_TAG}" \
  "${SCRIPT_DIR}" 2>&1 | tee "${SCRIPT_DIR}/docker-build.log"

BUILD_STATUS=${PIPESTATUS[0]}

if [[ ${BUILD_STATUS} -eq 0 ]]; then
  echo "Build OK: ${FOLDER}/${CONTAINER}:${EFFECTIVE_TAG} (variant=${VARIANT})"
  if [[ "${VARIANT}" == "dev" && -n "${REGISTRY}" && -z "${PUBLICATION_TAG_SUFFIX}" ]]; then
    docker tag "${FOLDER}/${CONTAINER}:${EFFECTIVE_TAG}" \
      "${REGISTRY}/${FOLDER}/${CONTAINER}:${EFFECTIVE_TAG}"
    echo "Tagged: ${REGISTRY}/${FOLDER}/${CONTAINER}:${EFFECTIVE_TAG}"
  elif [[ -n "${PUBLICATION_TAG_SUFFIX}" ]]; then
    echo "Registry tag skipped for publication suffix '${PUBLICATION_TAG_SUFFIX}'."
  else
    echo "Registry tag skipped (public variant or no REGISTRY set; PS-97 §1.1.3 closed-loop)."
  fi
else
  echo "Build FAILED — see docker-build.log"
fi

rm -f "${SCRIPT_DIR}/${PIP_CONF}"
exit ${BUILD_STATUS}
