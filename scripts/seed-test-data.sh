#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${1:-all}"

resolve_python() {
  if [[ -x "${ROOT_DIR}/venv/bin/python" ]]; then
    printf '%s\n' "${ROOT_DIR}/venv/bin/python"
    return
  fi
  if command -v python3 >/dev/null 2>&1; then
    command -v python3
    return
  fi
  command -v python
}

python_bin="$(resolve_python)"

resolve_pip() {
  if [[ -x "${ROOT_DIR}/venv/bin/pip" ]]; then
    printf '%s\n' "${ROOT_DIR}/venv/bin/pip"
    return
  fi
  "${python_bin}" -m pip --version >/dev/null 2>&1 || return 1
  printf '%s -m pip\n' "${python_bin}"
}

pip_cmd="$(resolve_pip || true)"

ensure_python_module() {
  local module_name="$1"
  local package_name="$2"
  if "${python_bin}" -c "import ${module_name}" >/dev/null 2>&1; then
    return 0
  fi
  if [[ -z "${pip_cmd}" ]]; then
    echo "Missing Python module ${module_name} and no pip command available to install ${package_name}" >&2
    return 1
  fi
  # shellcheck disable=SC2086
  ${pip_cmd} install "${package_name}" >/dev/null
}

wait_for_health() {
  local container="$1"
  local timeout="${2:-180}"
  local deadline=$((SECONDS + timeout))
  while (( SECONDS < deadline )); do
    local status
    status="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "${container}" 2>/dev/null || true)"
    if [[ "${status}" == "healthy" || "${status}" == "running" ]]; then
      return 0
    fi
    sleep 2
  done
  echo "Timed out waiting for ${container} to become healthy" >&2
  return 1
}

start_stack() {
  local compose_file="$1"
  shift
  docker compose -f "${compose_file}" down -v >/dev/null 2>&1 || true
  docker compose -f "${compose_file}" up -d "$@"
}

cleanup_conflicts() {
  case "${TARGET}" in
    mongodb|all)
      docker rm -f db-mcp-server-test-mongo6 >/dev/null 2>&1 || true
      ;;
  esac
}

source_env_defaults() {
  local env_file="$1"
  local raw_line line key value

  while IFS= read -r raw_line || [[ -n "${raw_line}" ]]; do
    line="${raw_line#"${raw_line%%[![:space:]]*}"}"
    line="${line%"${line##*[![:space:]]}"}"
    [[ -z "${line}" || "${line}" == \#* ]] && continue
    line="${line#export }"
    [[ "${line}" == *=* ]] || continue
    key="${line%%=*}"
    value="${line#*=}"
    [[ -n "${key}" ]] || continue
    if [[ -z "${!key+x}" ]]; then
      export "${key}=${value}"
    fi
  done < "${env_file}"
}

seed_target() {
  case "${TARGET}" in
    mongodb)
      source_env_defaults "${ROOT_DIR}/tests/env-mongodb"
      start_stack "${ROOT_DIR}/docker/docker-compose.mongodb.yml" mongodb
      wait_for_health db-mcp-mongodb 120
      "${python_bin}" -m tests.fixtures.mongodb_seed
      ;;
    couchdb)
      source_env_defaults "${ROOT_DIR}/tests/env-couchdb"
      start_stack "${ROOT_DIR}/docker/docker-compose.couchdb.yml" couchdb
      wait_for_health db-mcp-couchdb 120
      "${python_bin}" -m tests.fixtures.couchdb_seed
      ;;
    opensearch)
      source_env_defaults "${ROOT_DIR}/tests/env-opensearch"
      start_stack "${ROOT_DIR}/docker/docker-compose.opensearch.yml" opensearch
      wait_for_health db-mcp-opensearch 240
      "${python_bin}" -m tests.fixtures.opensearch_seed
      ;;
    elasticsearch)
      source_env_defaults "${ROOT_DIR}/tests/env-elasticsearch"
      start_stack "${ROOT_DIR}/docker/docker-compose.elasticsearch.yml" elasticsearch
      wait_for_health db-mcp-elasticsearch 240
      "${python_bin}" -m tests.fixtures.elasticsearch_seed
      ;;
    cassandra)
      source_env_defaults "${ROOT_DIR}/tests/env-cassandra"
      start_stack "${ROOT_DIR}/docker/docker-compose.cassandra.yml" cassandra
      wait_for_health db-mcp-cassandra 360
      "${python_bin}" -m tests.fixtures.cassandra_seed
      ;;
    all)
      source_env_defaults "${ROOT_DIR}/tests/env-all"
      start_stack "${ROOT_DIR}/docker/docker-compose.all.yml" mongodb couchdb opensearch elasticsearch cassandra
      wait_for_health db-mcp-mongodb 120
      wait_for_health db-mcp-couchdb 120
      wait_for_health db-mcp-opensearch 240
      wait_for_health db-mcp-elasticsearch 240
      wait_for_health db-mcp-cassandra 360
      "${python_bin}" -m tests.fixtures.mongodb_seed
      "${python_bin}" -m tests.fixtures.couchdb_seed
      "${python_bin}" -m tests.fixtures.opensearch_seed
      "${python_bin}" -m tests.fixtures.elasticsearch_seed
      "${python_bin}" -m tests.fixtures.cassandra_seed
      ;;
    *)
      echo "Unsupported target: ${TARGET}" >&2
      exit 2
      ;;
  esac
}

cd "${ROOT_DIR}"
cleanup_conflicts
ensure_python_module pymongo pymongo
ensure_python_module requests requests
if [[ "${TARGET}" == "cassandra" || "${TARGET}" == "all" ]]; then
  ensure_python_module cassandra.cluster cassandra-driver
fi
seed_target

echo "Seed completed for target: ${TARGET}"
