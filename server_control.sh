#!/usr/bin/env bash
# db-mcp-server control script skeleton
# Phase 1 planning scaffold only — runtime servers not implemented yet.

set -euo pipefail

ENV_FILE=""
POSITIONAL_ARGS=()
while [ $# -gt 0 ]; do
  case "$1" in
    --env)
      ENV_FILE="${2:-}"
      shift 2
      ;;
    *)
      POSITIONAL_ARGS+=("$1")
      shift
      ;;
  esac
done
set -- "${POSITIONAL_ARGS[@]}"

if [ -z "$ENV_FILE" ]; then
  echo "[ERROR] --env <path> is required by platform rules" >&2
  exit 2
fi

if [ ! -f "$ENV_FILE" ]; then
  echo "[ERROR] env file not found: $ENV_FILE" >&2
  exit 2
fi

ACTION="${1:-status}"
TARGET="${2:-all}"

case "$ACTION" in
  status)
    echo "db-mcp-server skeleton only. No runtime processes exist yet."
    echo "Requested target: $TARGET"
    ;;
  start|stop|restart)
    echo "db-mcp-server runtime is not implemented yet."
    echo "Requested action: $ACTION $TARGET"
    exit 1
    ;;
  *)
    echo "Usage: $0 --env <path> [start|stop|restart|status] [api|web|mcp|a2a|all]" >&2
    exit 2
    ;;
esac
