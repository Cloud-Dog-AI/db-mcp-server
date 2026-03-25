#!/usr/bin/env bash
# Copyright 2026 Cloud-Dog, Viewdeck Engineering Limited
set -euo pipefail

if [ $# -ne 1 ]; then
  echo "Usage: $0 <source-dist-dir>" >&2
  exit 2
fi

SOURCE_DIR="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TARGET_DIR="${PROJECT_ROOT}/ui/dist"

if [ ! -d "$SOURCE_DIR" ]; then
  echo "UI dist source not found: $SOURCE_DIR" >&2
  exit 2
fi

rm -rf "$TARGET_DIR"
mkdir -p "$TARGET_DIR"
cp -R "$SOURCE_DIR"/. "$TARGET_DIR"/

echo "Synced UI dist to $TARGET_DIR"
