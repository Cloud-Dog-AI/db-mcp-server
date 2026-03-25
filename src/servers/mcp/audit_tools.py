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
# Description: Audit MCP tools for browsing audit events.
# Related requirements: AC-02, NF-01
# Related tests: IT1.3

"""Audit MCP tool registry."""

from __future__ import annotations

from typing import Any

from cloud_dog_api_kit import ToolContract


def build_audit_tool_registry(runtime) -> dict[str, ToolContract]:
    """Build audit MCP tools."""
    audit_events = runtime.audit_events

    async def list_events(payload: dict[str, Any], request) -> dict[str, Any]:
        return {
            "items": audit_events.list_events(
                request,
                limit=int(payload.get("limit", 50) or 50),
                event_type=payload.get("event_type"),
            )
        }

    async def get_event(payload: dict[str, Any], request) -> dict[str, Any]:
        return audit_events.get_event(request, event_id=str(payload.get("event_id", "")))

    return {
        "audit.list_events": ToolContract(name="audit.list_events", handler=list_events, description="List audit events"),
        "audit.get_event": ToolContract(name="audit.get_event", handler=get_event, description="Get audit event detail"),
    }
