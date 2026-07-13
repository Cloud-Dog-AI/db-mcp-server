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
CUSTOM_CA_CERT_SOURCE="${CUSTOM_CA_CERT:-/usr/local/share/ca-certificates/cloud-dog.net.ca.crt}"
CUSTOM_CA_CONTEXT="${SCRIPT_DIR}/custom-ca.crt"

cleanup_build_secrets() {
  rm -f "${SCRIPT_DIR}/${PIP_CONF}" "${CUSTOM_CA_CONTEXT}"
}
trap cleanup_build_secrets EXIT

if [[ ! -f "${CUSTOM_CA_CERT_SOURCE}" ]]; then
  echo "ERROR: corporate CA certificate not found: ${CUSTOM_CA_CERT_SOURCE}" >&2
  exit 2
fi
cp "${CUSTOM_CA_CERT_SOURCE}" "${CUSTOM_CA_CONTEXT}"
chmod 644 "${CUSTOM_CA_CONTEXT}"

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

VCS_REF="${VCS_REF:-$(git -C "${SCRIPT_DIR}" rev-parse HEAD 2>/dev/null || printf 'unknown')}"
BUILD_DATE="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
# W28E-1863 fix-wave-d (WSC-014): propagate build identity to the image so the
# Dockerfile can stamp OCI ref.name + runtime ENV for _build_identity() / /version.
SOURCE_COMMIT="${SOURCE_COMMIT:-${VCS_REF}}"
SOURCE_BRANCH="${SOURCE_BRANCH:-$(git -C "${SCRIPT_DIR}" rev-parse --abbrev-ref HEAD 2>/dev/null || printf 'unknown')}"

LOCAL_IMAGE_REF="${FOLDER}/${CONTAINER}:${EFFECTIVE_TAG}"
BUILD_IMAGE_REF="${LOCAL_IMAGE_REF}"
if [[ "${VARIANT}" == "dev" && -n "${REGISTRY}" && -z "${PUBLICATION_TAG_SUFFIX}" ]]; then
  # Build directly under the sanctioned internal registry name.  Besides
  # avoiding a redundant retag, this prevents tooling from rendering an
  # unqualified local name as a misleading docker.io boundary in build proof.
  BUILD_IMAGE_REF="${REGISTRY}/${LOCAL_IMAGE_REF}"
fi

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
# Vault stores the repository root.  pip requires the PEP 503 simple API; make
# both root and already-normalized caller values resolve to the same endpoint.
PIP_INDEX_URL="${PIP_INDEX_URL%/}"
if [[ ! "${PIP_INDEX_URL}" =~ /simple$ ]]; then
  PIP_INDEX_URL="${PIP_INDEX_URL}/simple"
fi
PYPI_USERNAME="${PYPI_USERNAME:-}"
PYPI_PASSWORD="${PYPI_PASSWORD:-}"

# Credentials are URL userinfo, so characters such as @, :, /, %, and # must
# be percent-encoded before constructing an authenticated index URL.  Keep the
# encoded values in memory only; the generated config is removed by the EXIT
# trap and is consumed through BuildKit's secret mount.
if [[ -n "${PYPI_USERNAME}" ]] && [[ -n "${PYPI_PASSWORD}" ]]; then
  PYPI_USERNAME_URLENCODED="$(PYPI_VALUE="${PYPI_USERNAME}" python3 -c \
    'import os, urllib.parse; print(urllib.parse.quote(os.environ["PYPI_VALUE"], safe=""))')"
  PYPI_PASSWORD_URLENCODED="$(PYPI_VALUE="${PYPI_PASSWORD}" python3 -c \
    'import os, urllib.parse; print(urllib.parse.quote(os.environ["PYPI_VALUE"], safe=""))')"
else
  PYPI_USERNAME_URLENCODED=""
  PYPI_PASSWORD_URLENCODED=""
fi

PYPI_HOST="$(python3 -c "from urllib.parse import urlsplit; print(urlsplit('${PIP_INDEX_URL}').hostname or 'pypi.org')")"

if [[ "${VARIANT}" == "public" ]]; then
  # Single strict index — no extra-index-url (PS-97 §3.3 / §4).
  if [[ -n "${PYPI_USERNAME}" ]] && [[ -n "${PYPI_PASSWORD}" ]]; then
    cat > "${SCRIPT_DIR}/${PIP_CONF}" << EOF
[global]
index-url = https://${PYPI_USERNAME_URLENCODED}:${PYPI_PASSWORD_URLENCODED}@${PIP_INDEX_URL#https://}
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
  # Dev/deployment variant — one Cloud-Dog-controlled index only.  The internal
  # repository proxies approved public dependencies, so no direct public PyPI
  # fallback is necessary or permitted for the supply-chain closure path.
  if [[ -n "${PYPI_USERNAME}" ]] && [[ -n "${PYPI_PASSWORD}" ]]; then
    cat > "${SCRIPT_DIR}/${PIP_CONF}" << EOF
[global]
index-url = https://${PYPI_USERNAME_URLENCODED}:${PYPI_PASSWORD_URLENCODED}@${PIP_INDEX_URL#https://}
trusted-host = ${PYPI_HOST}
EOF
    echo "pip.conf: dev variant, authenticated single-index access (${PYPI_HOST})."
  else
    cat > "${SCRIPT_DIR}/${PIP_CONF}" << EOF
[global]
index-url = ${PIP_INDEX_URL}
trusted-host = ${PYPI_HOST}
EOF
    echo "pip.conf: dev variant, anonymous single-index access (${PYPI_HOST})."
  fi
fi
chmod 600 "${SCRIPT_DIR}/${PIP_CONF}"

# ── Build ────────────────────────────────────────────────────────
# ── W28C-1719 publish-before-pin guard + build-provenance revision label (fail-closed) ──
_PBP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
"${_PBP_DIR}/scripts/publish-before-pin-guard.sh" "${_PBP_DIR}" || exit $?
_PBP_REV="$(git -C "${_PBP_DIR}" rev-parse HEAD 2>/dev/null || echo unknown)"

DOCKER_BUILDKIT=1 docker buildx build \
  --label "org.opencontainers.image.revision=${_PBP_REV}" \
  --progress=plain \
  --network=host \
  --load \
  -f "${SCRIPT_DIR}/${DOCKERFILE}" \
  --secret id=pip_conf,src="${SCRIPT_DIR}/${PIP_CONF}" \
  --build-arg PUBLIC_PYPI_INDEX_URL="${PIP_INDEX_URL}" \
  --build-arg PIP_INDEX_URL="${PIP_INDEX_URL}" \
  --build-arg CUSTOM_CA_CERT=custom-ca.crt \
  --build-arg HTTP_PROXY="${HTTP_PROXY:-}" \
  --build-arg HTTPS_PROXY="${HTTPS_PROXY:-}" \
  --build-arg NO_PROXY="${NO_PROXY:-}" \
  --build-arg http_proxy="${http_proxy:-}" \
  --build-arg https_proxy="${https_proxy:-}" \
  --build-arg no_proxy="${no_proxy:-}" \
  --build-arg VCS_REF="${VCS_REF}" \
  --build-arg BUILD_DATE="${BUILD_DATE}" \
  --build-arg SOURCE_COMMIT="${SOURCE_COMMIT}" \
  --build-arg SOURCE_BRANCH="${SOURCE_BRANCH}" \
  -t "${BUILD_IMAGE_REF}" \
  "${SCRIPT_DIR}" 2>&1 | tee "${SCRIPT_DIR}/docker-build.log"

BUILD_STATUS=${PIPESTATUS[0]}

if [[ ${BUILD_STATUS} -eq 0 ]]; then
  echo "Build OK: ${BUILD_IMAGE_REF} (variant=${VARIANT})"
  if [[ "${VARIANT}" == "dev" && -n "${REGISTRY}" && -z "${PUBLICATION_TAG_SUFFIX}" ]]; then
    echo "Tagged: ${BUILD_IMAGE_REF}"
  elif [[ -n "${PUBLICATION_TAG_SUFFIX}" ]]; then
    echo "Registry tag skipped for publication suffix '${PUBLICATION_TAG_SUFFIX}'."
  else
    echo "Registry tag skipped (public variant or no REGISTRY set; PS-97 §1.1.3 closed-loop)."
  fi
else
  echo "Build FAILED — see docker-build.log"
fi

exit ${BUILD_STATUS}
