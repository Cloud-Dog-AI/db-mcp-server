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

"""Helpers for serving the db-mcp PS-30 SPA via cloud_dog_storage (PS-85)."""

from __future__ import annotations

import mimetypes
import os
from importlib.metadata import PackageNotFoundError, version

from cloud_dog_storage.backends.local import LocalStorage
from cloud_dog_storage.errors import StorageFileNotFoundError, StoragePermissionError
from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse, Response

_SPA_PREFIX = "/ui/dist"


def _project_storage() -> LocalStorage:
    """Local storage rooted at the current working directory (service process root)."""
    return LocalStorage(root_path=os.getcwd())


def _logical_dist_path(relative: str) -> str:
    rel = str(relative or "").lstrip("/").replace("\\", "/")
    return f"{_SPA_PREFIX}/{rel}" if rel else f"{_SPA_PREFIX}/"


def spa_entry_routes() -> set[str]:
    """Return browser history entry routes for the SPA."""
    return set(_SPA_ENTRY_ROUTES)


_SPA_ENTRY_ROUTES = {
    "/",
    "/login",
    "/admin/profiles",
    "/admin/users",
    "/admin/roles",
    "/catalogue",
    "/search",
    "/relationships",
    "/schema",
    "/audit",
    "/mcp-console",
    "/a2a-console",
    "/settings",
}


def is_spa_entry_path(path: str) -> bool:
    """Return whether a path should be served by the SPA entry point."""
    cleaned = "/" + str(path or "").strip().lstrip("/")
    if cleaned in _SPA_ENTRY_ROUTES:
        return True
    if cleaned.startswith("/catalogue/") or cleaned.startswith("/data/"):
        return True
    return "." not in cleaned.rsplit("/", 1)[-1]


def require_ui_dist(storage: LocalStorage) -> None:
    """Fail fast if the SPA build output is missing."""
    if not storage.exists(f"{_SPA_PREFIX}/index.html"):
        raise HTTPException(
            status_code=503,
            detail="UI dist is missing. Build the db-mcp monorepo app and sync it into ui/dist.",
        )


def serve_spa_index() -> HTMLResponse:
    """Return the built SPA index.html content."""
    storage = _project_storage()
    require_ui_dist(storage)
    logical = f"{_SPA_PREFIX}/index.html"
    try:
        raw = storage.read_bytes(logical)
    except StorageFileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="UI asset not found") from exc
    except StoragePermissionError as exc:
        raise HTTPException(status_code=404, detail="UI asset not found") from exc
    return HTMLResponse(raw.decode("utf-8"))


def serve_spa_asset(relative_path: str) -> Response:
    """Return one built SPA static asset from ui/dist."""
    storage = _project_storage()
    require_ui_dist(storage)
    logical = _logical_dist_path(relative_path)
    try:
        data = storage.read_bytes(logical)
    except StorageFileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="UI asset not found") from exc
    except StoragePermissionError as exc:
        raise HTTPException(status_code=404, detail="UI asset not found") from exc
    media_type, _ = mimetypes.guess_type(relative_path)
    return Response(content=data, media_type=media_type or "application/octet-stream")


def serve_runtime_config(runtime, request: Request) -> Response:
    """Return runtime-config.js for the SPA bootstrap contract."""
    environment = str(runtime.config.get("environment", "dev"))
    app_version = _application_release()
    body = (
        "const __origin = window.location.origin;\n"
        "window.__RUNTIME_CONFIG__ = {\n"
        f'  "ENV": "{environment}",\n'
        '  "API_BASE_URL": __origin,\n'
        '  "MCP_BASE_URL": __origin,\n'
        '  "A2A_BASE_URL": __origin,\n'
        '  "AUTH_MODE": "cookie",\n'
        '  "API_KEY_HEADER": "X-API-Key",\n'
        f'  "APP_VERSION": "{app_version}"\n'
        "};\n"
    )
    return Response(content=body, media_type="application/javascript")


def _application_release() -> str:
    """Resolve package version for runtime-config.js."""
    try:
        return str(version("cloud-dog-db-mcp-server"))
    except PackageNotFoundError:
        return "0.0.0-dev"
