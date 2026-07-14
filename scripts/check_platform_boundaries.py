#!/usr/bin/env python3
"""Fail when service source bypasses mandatory Cloud-Dog platform packages."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVICE_SRC = ROOT / "src"
FORBIDDEN_DB_IMPORTS = {
    "cassandra",
    "couchdb",
    "elasticsearch",
    "opensearchpy",
    "psycopg",
    "pymongo",
    "pymysql",
    "requests",
    "sqlalchemy",
    "sqlite3",
}
FORBIDDEN_PLATFORM_REPLACEMENTS = {"hvac", "logging"}


def _import_root(node: ast.AST) -> set[str]:
    if isinstance(node, ast.Import):
        return {alias.name.split(".", 1)[0] for alias in node.names}
    if isinstance(node, ast.ImportFrom) and node.module:
        return {node.module.split(".", 1)[0]}
    return set()


def scan_service_source() -> list[str]:
    """Return deterministic platform-boundary violations in service source."""

    failures: list[str] = []
    for path in sorted(SERVICE_SRC.rglob("*.py")):
        relative = path.relative_to(ROOT)
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(relative))
        for node in ast.walk(tree):
            roots = _import_root(node)
            for root in sorted(roots & FORBIDDEN_DB_IMPORTS):
                failures.append(f"{relative}:{node.lineno}: direct database/client import: {root}")
            for root in sorted(roots & FORBIDDEN_PLATFORM_REPLACEMENTS):
                failures.append(f"{relative}:{node.lineno}: bespoke platform replacement import: {root}")
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if isinstance(node.func.value, ast.Name) and node.func.value.id == "os" and node.func.attr == "getenv":
                    failures.append(f"{relative}:{node.lineno}: direct environment access: os.getenv")
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                if node.value.id == "os" and node.attr == "environ":
                    failures.append(f"{relative}:{node.lineno}: direct environment access: os.environ")
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {"lru_cache", "cache"}:
                failures.append(f"{relative}:{node.lineno}: bespoke cache decorator: {node.func.id}")
    return failures


def main() -> int:
    failures = scan_service_source()
    if failures:
        print("PLATFORM_BOUNDARY_SCAN: FAIL")
        print("\n".join(failures))
        return 1
    print("PLATFORM_BOUNDARY_SCAN: PASS direct_env=0 direct_db_clients=0 bespoke_replacements=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
