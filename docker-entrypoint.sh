#!/usr/bin/env bash
# Copyright 2026 Cloud-Dog, Viewdeck Engineering Limited
# Licensed under the Apache License, Version 2.0.

set -euo pipefail

SYSTEM_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
export REQUESTS_CA_BUNDLE="${REQUESTS_CA_BUNDLE:-${SYSTEM_CA_BUNDLE}}"
export SSL_CERT_FILE="${SSL_CERT_FILE:-${SYSTEM_CA_BUNDLE}}"
export CURL_CA_BUNDLE="${CURL_CA_BUNDLE:-${SYSTEM_CA_BUNDLE}}"
export GIT_SSL_CAINFO="${GIT_SSL_CAINFO:-${SYSTEM_CA_BUNDLE}}"
export NODE_EXTRA_CA_CERTS="${NODE_EXTRA_CA_CERTS:-${SYSTEM_CA_BUNDLE}}"

CA_PATH="${CLOUD_DOG_TLS_CA_BUNDLE:-}"
if [[ -n "${CA_PATH}" ]]; then
  if [[ ! -f "${CA_PATH}" ]]; then
    echo "ERROR: CLOUD_DOG_TLS_CA_BUNDLE does not name a readable file" >&2
    exit 2
  fi
  RUNTIME_CA_BUNDLE="/tmp/cloud-dog-ca-bundle-${UID}.crt"
  cp "${SYSTEM_CA_BUNDLE}" "${RUNTIME_CA_BUNDLE}"
  printf '\n' >> "${RUNTIME_CA_BUNDLE}"
  cat "${CA_PATH}" >> "${RUNTIME_CA_BUNDLE}"
  chmod 600 "${RUNTIME_CA_BUNDLE}"
  export REQUESTS_CA_BUNDLE="${RUNTIME_CA_BUNDLE}"
  export SSL_CERT_FILE="${RUNTIME_CA_BUNDLE}"
  export CURL_CA_BUNDLE="${RUNTIME_CA_BUNDLE}"
  export GIT_SSL_CAINFO="${RUNTIME_CA_BUNDLE}"
  export NODE_EXTRA_CA_CERTS="${RUNTIME_CA_BUNDLE}"
fi

exec "$@"
