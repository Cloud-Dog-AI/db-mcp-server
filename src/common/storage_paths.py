"""String-based filesystem helpers backed by cloud_dog_storage."""

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

from __future__ import annotations

from cloud_dog_storage.backends.local import LocalStorage


def normalise_fs_path(path: str) -> str:
    """Normalise a filesystem path string without object wrappers."""
    raw = str(path or "").replace("\\", "/")
    if not raw:
        return "."

    absolute = raw.startswith("/")
    parts: list[str] = []
    for part in raw.split("/"):
        if part in {"", "."}:
            continue
        if part == "..":
            if parts and parts[-1] != "..":
                parts.pop()
            elif not absolute:
                parts.append(part)
            continue
        parts.append(part)

    joined = "/".join(parts)
    if absolute:
        return f"/{joined}" if joined else "/"
    return joined or "."


def join_fs_path(base: str, *segments: str) -> str:
    """Join path segments into one normalised filesystem path string."""
    current = normalise_fs_path(base)
    for segment in segments:
        piece = str(segment or "").replace("\\", "/")
        if not piece:
            continue
        if current == "/":
            current = f"/{piece.lstrip('/')}"
        elif current in {"", "."}:
            current = piece
        else:
            current = f"{current.rstrip('/')}/{piece.lstrip('/')}"
        current = normalise_fs_path(current)
    return current


def parent_fs_path(path: str) -> str:
    """Return the parent directory string for a filesystem path."""
    normalised = normalise_fs_path(path)
    if normalised == "/":
        return "/"
    trimmed = normalised.rstrip("/")
    if "/" not in trimmed:
        return "."
    parent = trimmed[: trimmed.rfind("/")]
    return parent or "/"


def file_name(path: str) -> str:
    """Return the final path segment."""
    normalised = normalise_fs_path(path)
    if normalised == "/":
        return ""
    trimmed = normalised.rstrip("/")
    if "/" not in trimmed:
        return trimmed
    return trimmed[trimmed.rfind("/") + 1 :]


def storage_for_path(path: str) -> tuple[LocalStorage, str]:
    """Return a LocalStorage rooted at the path parent plus a key for the basename."""
    normalised = normalise_fs_path(path)
    return LocalStorage(root_path=parent_fs_path(normalised)), f"/{file_name(normalised)}"


def storage_exists(path: str) -> bool:
    """Return whether a file or directory exists."""
    storage, key = storage_for_path(path)
    return storage.exists(key)


def ensure_directory(path: str) -> None:
    """Create a directory path if required."""
    normalised = normalise_fs_path(path)
    if normalised in {"", "."}:
        return
    if normalised == "/":
        LocalStorage(root_path="/").create_dir("/")
        return
    storage, key = storage_for_path(normalised)
    storage.create_dir(key)


def read_text_file(path: str, *, encoding: str = "utf-8") -> str:
    """Read a UTF-8 text file via LocalStorage."""
    storage, key = storage_for_path(path)
    return storage.read_bytes(key).decode(encoding)


def write_text_file(path: str, content: str, *, encoding: str = "utf-8", mode: int | None = None) -> None:
    """Write a UTF-8 text file via LocalStorage."""
    storage, key = storage_for_path(path)
    storage.write_bytes(key, content.encode(encoding))
    if mode is not None:
        storage.chmod_path(key, mode)


def find_project_root(start_file: str, marker: str = "pyproject.toml") -> str:
    """Walk upward from a module file until the project marker is found."""
    candidate = parent_fs_path(start_file)
    visited: set[str] = set()
    while candidate not in visited:
        visited.add(candidate)
        if LocalStorage(root_path=candidate).exists(f"/{marker}"):
            return candidate
        parent = parent_fs_path(candidate)
        if parent == candidate:
            break
        candidate = parent
    return parent_fs_path(start_file)
