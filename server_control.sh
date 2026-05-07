#!/usr/bin/env bash
# Copyright 2026 Cloud-Dog, Viewdeck Engineering Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Description: Process manager for db-mcp-server API, Web, MCP, and A2A servers.
# Related requirements: W28A-274-A deliverable 3
# Related tests: ST1.1

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

ENV_FILE=""
POSITIONAL=()
while [ $# -gt 0 ]; do
  case "$1" in
    --env)
      ENV_FILE="${2:-}"
      shift 2
      ;;
    *)
      POSITIONAL+=("$1")
      shift
      ;;
  esac
done
set -- "${POSITIONAL[@]}"

if [ -z "$ENV_FILE" ]; then
  echo "[ERROR] --env <path> is required" >&2
  exit 2
fi
if [ ! -f "$ENV_FILE" ]; then
  echo "[ERROR] env file not found: $ENV_FILE" >&2
  exit 2
fi

ACTION="${1:-status}"
TARGET="${2:-all}"

mkdir -p .pids logs data

if [ -x "venv/bin/python" ]; then
  PYTHON_BIN="venv/bin/python"
elif [ -x ".venv/bin/python" ]; then
  PYTHON_BIN=".venv/bin/python"
else
  PYTHON_BIN="python3"
fi

export CLOUD_DOG_ENV_FILES="$ENV_FILE"

config_get() {
  local key="$1"
  "$PYTHON_BIN" - <<PY
from src.common.config_loader import load_runtime_config
cfg = load_runtime_config()
print(cfg.get("$key"))
PY
}

port_for() {
  case "$1" in
    api) config_get "api_server.port" ;;
    web) config_get "web_server.port" ;;
    mcp) config_get "mcp_server.port" ;;
    a2a) config_get "a2a_server.port" ;;
    *) echo "" ;;
  esac
}

script_for() {
  case "$1" in
    api) echo "start_api_server.py" ;;
    web) echo "start_web_server.py" ;;
    mcp) echo "start_mcp_server.py" ;;
    a2a) echo "start_a2a_server.py" ;;
    *) echo "" ;;
  esac
}

pid_file_for() {
  echo ".pids/$1.pid"
}

log_file_for() {
  echo "logs/$1.log"
}

is_running() {
  local pid="$1"
  [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null
}

wait_for_port() {
  local port="$1"
  local attempts=30
  while [ $attempts -gt 0 ]; do
    if "$PYTHON_BIN" - <<PY >/dev/null 2>&1
import socket
s = socket.socket()
s.settimeout(0.5)
try:
    s.connect(("127.0.0.1", int($port)))
    ok = True
except Exception:
    ok = False
finally:
    s.close()
raise SystemExit(0 if ok else 1)
PY
    then
      return 0
    fi
    attempts=$((attempts-1))
    sleep 1
  done
  return 1
}

wait_for_health() {
  local port="$1"
  local pid="$2"
  local attempts="${SERVER_START_ATTEMPTS:-90}"
  while [ "$attempts" -gt 0 ]; do
    if ! is_running "$pid"; then
      return 2
    fi
    if "$PYTHON_BIN" - <<PY >/dev/null 2>&1
import sys
import urllib.request

try:
    with urllib.request.urlopen("http://127.0.0.1:${port}/health", timeout=2.0) as response:
        raise SystemExit(0 if response.status == 200 else 1)
except Exception:
    raise SystemExit(1)
PY
    then
      return 0
    fi
    attempts=$((attempts-1))
    sleep 1
  done
  return 1
}

start_one() {
  local name="$1"
  local script
  script="$(script_for "$name")"
  local port
  port="$(port_for "$name")"
  local pid_file
  pid_file="$(pid_file_for "$name")"
  local log_file
  log_file="$(log_file_for "$name")"

  if [ -f "$pid_file" ] && is_running "$(cat "$pid_file")"; then
    echo "$name already running"
    return 0
  fi

  local pid
  pid="$("$PYTHON_BIN" - <<PY
import os
import subprocess

with open("${log_file}", "ab", buffering=0) as log_handle:
    process = subprocess.Popen(
        ["${PYTHON_BIN}", "${script}"],
        stdin=subprocess.DEVNULL,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        start_new_session=True,
        env={**os.environ, "PYTHONUNBUFFERED": "1"},
        cwd="${SCRIPT_DIR}",
    )
    print(process.pid)
PY
)"
  echo "$pid" > "$pid_file"

  if wait_for_health "$port" "$pid"; then
    echo "$name started (pid $pid, port $port)"
    return 0
  fi

  echo "$name failed to start" >&2
  tail -n 50 "$log_file" >&2 || true
  return 1
}

stop_one() {
  local name="$1"
  local pid_file
  pid_file="$(pid_file_for "$name")"
  local port
  port="$(port_for "$name")"
  if [ -f "$pid_file" ]; then
    local pid
    pid="$(cat "$pid_file")"
    if is_running "$pid"; then
      kill "$pid" 2>/dev/null || true
      for _ in $(seq 1 15); do
        if ! is_running "$pid"; then
          break
        fi
        sleep 1
      done
      if is_running "$pid"; then
        kill -9 "$pid" 2>/dev/null || true
      fi
    fi
    rm -f "$pid_file"
  fi
  if command -v fuser >/dev/null 2>&1 && [ -n "$port" ] && fuser -n tcp "$port" >/dev/null 2>&1; then
    fuser -k -TERM -n tcp "$port" >/dev/null 2>&1 || true
    for _ in $(seq 1 15); do
      if ! fuser -n tcp "$port" >/dev/null 2>&1; then
        break
      fi
      sleep 1
    done
    if fuser -n tcp "$port" >/dev/null 2>&1; then
      fuser -k -KILL -n tcp "$port" >/dev/null 2>&1 || true
    fi
  fi
  echo "$name stopped"
}

status_one() {
  local name="$1"
  local pid_file
  pid_file="$(pid_file_for "$name")"
  local port
  port="$(port_for "$name")"
  if [ -f "$pid_file" ] && is_running "$(cat "$pid_file")"; then
    echo "$name running (pid $(cat "$pid_file"), port $port)"
  else
    echo "$name not running"
  fi
}

for_each_target() {
  if [ "$TARGET" = "all" ]; then
    for item in api web mcp a2a; do
      "$@" "$item"
    done
  else
    "$@" "$TARGET"
  fi
}

case "$ACTION" in
  start)
    if [ "$TARGET" = "all" ]; then
      for item in api web mcp a2a; do
        bash "$SCRIPT_DIR/server_control.sh" --env "$ENV_FILE" start "$item"
      done
    else
      start_one "$TARGET"
    fi
    ;;
  stop)
    for_each_target stop_one
    ;;
  restart)
    for_each_target stop_one
    if [ "$TARGET" = "all" ]; then
      for item in api web mcp a2a; do
        bash "$SCRIPT_DIR/server_control.sh" --env "$ENV_FILE" start "$item"
      done
    else
      start_one "$TARGET"
    fi
    ;;
  status)
    for_each_target status_one
    ;;
  help)
    echo "Usage: ./server_control.sh --env <path> [start|stop|restart|status] [api|web|mcp|a2a|all]"
    ;;
  *)
    echo "Usage: ./server_control.sh --env <path> [start|stop|restart|status] [api|web|mcp|a2a|all]" >&2
    exit 2
    ;;
esac
