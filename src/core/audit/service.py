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

import json
from typing import Any

from fastapi import Request

from cloud_dog_api_kit.errors import NotFoundError

from src.common.storage_paths import read_text_file, storage_exists


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
        events = self._read_events()
        if event_type:
            events = [item for item in events if str(item.get("event_type")) == event_type]
        return list(reversed(events[-max(1, min(limit, 500)):]))

    def get_event(self, request: Request, *, event_id: str) -> dict[str, Any]:
        self._runtime.access_control.require_request_permission(
            request,
            permission="audit.read",
            audit_resource_type="audit",
            audit_resource_id=event_id,
        )
        for item in self._read_events():
            if str(item.get("correlation_id")) == event_id:
                return item
        raise NotFoundError(message=f"Audit event not found: {event_id}")

    def _read_events(self) -> list[dict[str, Any]]:
        path = str(self._runtime.config.get("log.audit_log", "logs/audit.log.jsonl"))
        if not storage_exists(path):
            return []
        events: list[dict[str, Any]] = []
        for line in read_text_file(path, encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return events
