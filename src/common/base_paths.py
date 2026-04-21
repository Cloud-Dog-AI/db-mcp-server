"""Shared helpers for configurable server route prefixes."""

from __future__ import annotations

from typing import Any

SURFACE_BASE_PATH_DEFAULTS: dict[str, str] = {
    "api": "/api/v1",
    "web": "",
    "mcp": "/mcp",
    "a2a": "/a2a",
}

HEALTH_ROUTE_SUFFIXES: tuple[str, ...] = (
    "/health",
    "/ready",
    "/live",
    "/status",
)

DOC_ROUTE_SUFFIXES: tuple[str, ...] = (
    "/docs",
    "/redoc",
    "/openapi.json",
)


def normalise_base_path(value: object, *, default: str = "") -> str:
    """Return a normalised URL prefix with a leading slash and no trailing slash."""
    resolved = str(value or "").strip() or str(default or "").strip()
    if resolved in {"", "/"}:
        return ""
    return "/" + resolved.strip("/")


def configured_base_path(config: Any, surface: str) -> str:
    """Return the configured base path for one server surface."""
    default = SURFACE_BASE_PATH_DEFAULTS.get(surface, "")
    return normalise_base_path(config.get(f"{surface}_server.base_path", default), default=default)


def join_route(base_path: str, suffix: str = "") -> str:
    """Join a base path and route fragment into one absolute URL path."""
    prefix = normalise_base_path(base_path)
    tail = str(suffix or "").strip()
    if tail in {"", "/"}:
        return prefix or "/"
    if not tail.startswith("/"):
        tail = f"/{tail}"
    return f"{prefix}{tail}" if prefix else tail


def prefixed_paths(base_path: str, suffixes: tuple[str, ...] | list[str] | set[str]) -> set[str]:
    """Return a set of suffixes mapped underneath the configured base path."""
    return {join_route(base_path, suffix) for suffix in suffixes}


def exempt_paths_for_surface(base_path: str, *, include_unprefixed_health: bool = True) -> set[str]:
    """Return auth-exempt routes for one HTTP surface."""
    paths = set(DOC_ROUTE_SUFFIXES)
    paths.update(prefixed_paths(base_path, HEALTH_ROUTE_SUFFIXES))
    if include_unprefixed_health:
        paths.update(HEALTH_ROUTE_SUFFIXES)
    return paths


def first_path_segment(path: str) -> str:
    """Return the first segment of a URL path, preserving the leading slash."""
    normalised = normalise_base_path(path)
    if not normalised:
        return ""
    parts = [part for part in normalised.split("/") if part]
    return f"/{parts[0]}" if parts else ""
