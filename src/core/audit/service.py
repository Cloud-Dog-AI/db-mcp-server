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
# Description: Audit event browsing service for MCP audit tools.
# Related requirements: AC-02, NF-01
# Related tests: IT1.3

"""Audit event browsing service."""

from __future__ import annotations

import gzip
import json
import re
from typing import Any

from fastapi import Request

from cloud_dog_api_kit.errors import NotFoundError

from src.common.storage_paths import (
    file_name,
    list_sibling_files,
    read_text_file,
    storage_exists,
    storage_for_path,
)

# The audit log rotates aggressively under high-frequency ``http.read`` request
# auditing, so a domain event (job delete, secret reveal, RBAC change) is often
# evicted from the tip file within seconds of being written. The browsing
# service therefore reads across the current file plus its rotated siblings so
# recently-emitted events remain retrievable.
#
# Scan the tip plus this many rotated generations at most. Under noise
# suppression the loop normally stops far earlier (once ``want`` retained
# events are gathered); this cap only bounds the pathological case where a
# window is almost entirely read-request noise, so a single browse call never
# parses the whole (multi-generation, up to ~10 MB each) rotation set.
_MAX_ROTATIONS_SCANNED = 4
_ROTATION_SUFFIX = re.compile(r"\.(\d+)(?:\.gz)?$")

# ``http.<verb>`` events are the per-request middleware trail. Read-request
# (GET/HEAD/OPTIONS) auditing is extremely high volume and duplicates the API
# access log, so it floods the browse surface and buries security-relevant
# domain events (deletes, secret reveals, RBAC/config changes) within seconds.
# The audit *log file* still retains every event for compliance; the browse
# surface (WebUI Audit page + audit.list_events) simply de-noises by default so
# operators see actionable events. A caller can still request the read-request
# trail explicitly via ``event_type="http.read"``.
_NOISE_EVENT_TYPES: frozenset[str] = frozenset({"http.read"})


class AuditEventService:
    """Read audit events from the configured audit log."""

    def __init__(self, runtime) -> None:
        self._runtime = runtime

    def list_events(self, request: Request, *, limit: int = 50, event_type: str | None = None) -> list[dict[str, Any]]:
        self._runtime.access_control.require_request_permission(
            request,
            permission="audit.read",
            audit_resource_type="audit",
            audit_resource_id="list",
        )
        want = max(1, min(limit, 500))
        # By default suppress the high-volume ``http.read`` request trail so the
        # browse surface shows actionable events. An explicit event_type filter
        # (including "http.read") opts back into that specific stream.
        suppress = _NOISE_EVENT_TYPES if not event_type else frozenset()
        events = self._read_events(want=want, suppress=suppress, event_type=event_type)
        return list(reversed(events[-want:]))

    def get_event(self, request: Request, *, event_id: str) -> dict[str, Any]:
        self._runtime.access_control.require_request_permission(
            request,
            permission="audit.read",
            audit_resource_type="audit",
            audit_resource_id=event_id,
        )
        for item in self._read_events(want=500):
            if str(item.get("correlation_id")) == event_id:
                return item
        raise NotFoundError(message=f"Audit event not found: {event_id}")

    def _read_events(
        self,
        *,
        want: int = 500,
        suppress: frozenset[str] = frozenset(),
        event_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return audit events newest-last across the current + rotated logs.

        The tip file alone is not sufficient: ``http.read`` request auditing
        rotates it every few minutes, so a just-written domain event is quickly
        pushed into a ``.jsonl.N`` sibling. We therefore read the rotated
        generations (newest → oldest), dropping any ``suppress`` event types as
        we go, until we have accumulated at least ``want`` retained events (or
        exhausted the scanned rotation set), then return them in chronological
        (newest-last) order. Suppressing the high-volume request trail keeps the
        scan bounded while still surfacing recent domain events that a burst of
        that trail pushed off the tip.
        """
        base_path = str(self._runtime.config.get("log.audit_log", "logs/audit.log.jsonl"))
        files = self._rotation_files(base_path)[:_MAX_ROTATIONS_SCANNED]  # newest → oldest
        newest_last_batches: list[list[dict[str, Any]]] = []
        retained = 0
        for path in files:
            batch = self._read_events_file(path)
            if not batch:
                continue
            if suppress:
                batch = [ev for ev in batch if str(ev.get("event_type")) not in suppress]
                if not batch:
                    # File was all-noise; keep scanning deeper rotations.
                    continue
            if event_type:
                # Apply an explicit filter *before* deciding whether enough rows
                # have been retained. Multi-process rotation can leave the newest
                # matching domain event in .2 while .1 contains more than ``want``
                # unrelated request/tool events; filtering only after this loop
                # would stop at .1 and incorrectly return an empty result.
                batch = [ev for ev in batch if str(ev.get("event_type")) == event_type]
                if not batch:
                    continue
            newest_last_batches.append(batch)
            retained += len(batch)
            if retained >= want:
                break
        events: list[dict[str, Any]] = []
        # ``files`` is newest → oldest, so append the batches back-to-front to
        # produce a single chronological (oldest → newest) stream.
        for batch in reversed(newest_last_batches):
            events.extend(batch)
        return events

    def _rotation_files(self, base_path: str) -> list[str]:
        """Return the tip + rotated audit files ordered newest → oldest."""
        base_name = file_name(base_path)
        candidates = list_sibling_files(base_path, prefix=base_name)
        if not candidates and storage_exists(base_path):
            candidates = [base_path]

        def rank(path: str) -> tuple[int, int]:
            # Tip file (no numeric suffix) is newest → rank 0; rotated
            # ``.N``/``.N.gz`` are older with increasing N. ``.gz`` (compressed,
            # so rotated after its plain counterpart) sorts just after ``.N``.
            match = _ROTATION_SUFFIX.search(file_name(path))
            if not match:
                return (0, 0)
            return (int(match.group(1)), 1 if path.endswith(".gz") else 0)

        return sorted(candidates, key=rank)

    def _read_events_file(self, path: str) -> list[dict[str, Any]]:
        """Parse one JSONL audit file (plain or gzip) into a newest-last list."""
        if not storage_exists(path):
            return []
        try:
            if path.endswith(".gz"):
                storage, key = storage_for_path(path)
                raw = gzip.decompress(storage.read_bytes(key)).decode("utf-8")
            else:
                raw = read_text_file(path, encoding="utf-8")
        except Exception:  # noqa: BLE001 — a corrupt/unreadable rotation is skipped, not fatal
            return []
        events: list[dict[str, Any]] = []
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return events
