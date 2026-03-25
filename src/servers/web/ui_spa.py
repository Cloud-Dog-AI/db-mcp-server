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
# Description: Helpers for serving the PS-30 db-mcp SPA from ui/dist.
# Related requirements: W28A-274-J deliverables 2, 4
# Related tests: UT1.11, ST1.8

"""Helpers for serving the db-mcp PS-30 SPA."""

from __future__ import annotations

import json
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from fastapi import HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, Response

_SPA_ENTRY_ROUTES = {
    "/",
    "/login",
    "/admin/profiles",
    "/admin/users",
    "/catalogue",
    "/search",
    "/relationships",
    "/schema",
    "/audit",
    "/settings",
}


def spa_entry_routes() -> set[str]:
    """Return browser history entry routes for the SPA."""
    return set(_SPA_ENTRY_ROUTES)


def is_spa_entry_path(path: str) -> bool:
    """Return whether a path should be served by the SPA entry point."""
    cleaned = "/" + str(path or "").strip().lstrip("/")
    if cleaned in _SPA_ENTRY_ROUTES:
        return True
    if cleaned.startswith("/catalogue/") or cleaned.startswith("/data/"):
        return True
    return "." not in cleaned.rsplit("/", 1)[-1]


def ui_dist_root(project_root: Path) -> Path:
    """Return the checked-in SPA build directory."""
    return (project_root / "ui" / "dist").resolve()


def resolve_dist_file(project_root: Path, relative_path: str) -> Path:
    """Resolve one static asset within ui/dist and enforce path confinement."""
    root = ui_dist_root(project_root)
    candidate = (root / str(relative_path or "").lstrip("/")).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="UI asset not found") from exc
    if not candidate.is_file():
        raise HTTPException(status_code=404, detail="UI asset not found")
    return candidate


def require_ui_dist(project_root: Path) -> None:
    """Fail fast if the SPA build output is missing."""
    index_path = ui_dist_root(project_root) / "index.html"
    if not index_path.is_file():
        raise HTTPException(
            status_code=503,
            detail="UI dist is missing. Build the db-mcp monorepo app and sync it into ui/dist.",
        )


def serve_spa_index(project_root: Path) -> HTMLResponse:
    """Return the built SPA index.html content."""
    require_ui_dist(project_root)
    index_path = resolve_dist_file(project_root, "index.html")
    return HTMLResponse(index_path.read_text(encoding="utf-8"))


def serve_spa_asset(project_root: Path, relative_path: str) -> FileResponse:
    """Return one built SPA static asset from ui/dist."""
    require_ui_dist(project_root)
    asset_path = resolve_dist_file(project_root, relative_path)
    return FileResponse(asset_path)


def serve_runtime_config(runtime, request: Request) -> Response:
    """Return runtime-config.js for the SPA bootstrap contract."""
    api_base = str(request.base_url).rstrip("/")
    payload = {
        "ENV": str(runtime.config.get("environment", "dev")),
        "API_BASE_URL": api_base,
        "AUTH_MODE": "api_key",
        "API_KEY_HEADER": "X-API-Key",
        "APP_VERSION": _application_release(),
    }
    body = "window.__RUNTIME_CONFIG__ = " + json.dumps(payload, separators=(",", ":")) + ";\n"
    return Response(content=body, media_type="application/javascript")


def _application_release() -> str:
    """Resolve package version for runtime-config.js."""
    try:
        return str(version("cloud-dog-db-mcp-server"))
    except PackageNotFoundError:
        return "0.0.0-dev"
