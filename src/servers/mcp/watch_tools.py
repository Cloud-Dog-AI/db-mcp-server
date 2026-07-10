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
# Description: Database change-watch MCP tools (PS-102 §5.3 / CSTREAM-DB-001/002).
# Related requirements: CSTREAM-DB-001, CSTREAM-DB-002

"""Database change-watch MCP tool registry (``db_watch_*``).

Exposes the common change-stream lifecycle + retrieval surface as MCP tools that
drive the shared :class:`~src.core.change_stream.WatchService` adapter. RBAC is
enforced per call against the requesting principal (read verbs need ``data.read``,
mutating verbs need ``data.write``), scoped to the watched database profile. The
journal, cursor, queue, and error model are all consumed from the foundation
(RULES §1.4).
"""

from __future__ import annotations

import json
from typing import Any

from cloud_dog_api_kit import ToolContract
from cloud_dog_api_kit.change_stream.errors import ChangeStreamError
from cloud_dog_api_kit.errors import ValidationError


def _tenant_of(payload: dict[str, Any]) -> str:
    return str(payload.get("tenant_id") or payload.get("profile") or payload.get("profile_id") or "default")


def _as_error(exc: ChangeStreamError) -> ValidationError:
    """Surface the stable change-stream machine code through the MCP error path."""
    return ValidationError(message=json.dumps(exc.to_dict()))


def build_watch_tool_registry(runtime) -> dict[str, ToolContract]:
    """Build the ``db_watch_*`` MCP tool family over the shared watch adapter."""
    access = runtime.access_control

    def _require(request, permission: str, profile_id: str) -> None:
        access.require_request_permission(
            request,
            permission=permission,
            profile_id=profile_id,
            audit_resource_type="change_watch",
            audit_resource_id=profile_id,
        )

    async def watch_create(payload: dict[str, Any], request) -> dict[str, Any]:
        profile_id = str(payload.get("profile") or payload.get("profile_id") or "default")
        _require(request, "data.write", profile_id)
        principal = access.principal_from_request(request)
        try:
            return runtime.watch_service.create_watch(
                profile_id=profile_id,
                tenant_id=_tenant_of(payload),
                actor=principal.user_id,
                criteria=payload.get("criteria") if isinstance(payload.get("criteria"), dict) else None,
                max_batch=int(payload.get("max_batch", 100)),
                max_inflight=int(payload.get("max_inflight", 4)),
                journal_max=int(payload.get("journal_max", 1000)),
                journal_ttl_seconds=(
                    float(payload["journal_ttl_seconds"])
                    if payload.get("journal_ttl_seconds") not in (None, "")
                    else None
                ),
            )
        except ChangeStreamError as exc:
            raise _as_error(exc) from exc

    async def watch_list(payload: dict[str, Any], request) -> dict[str, Any]:
        profile_id = str(payload.get("profile") or payload.get("profile_id") or "default")
        _require(request, "data.read", profile_id)
        return {"watches": runtime.watch_service.list_watches(tenant_id=_tenant_of(payload))}

    async def watch_status(payload: dict[str, Any], request) -> dict[str, Any]:
        profile_id = str(payload.get("profile") or payload.get("profile_id") or "default")
        _require(request, "data.read", profile_id)
        try:
            return runtime.watch_service.get_status(str(payload["watch_id"]), tenant_id=_tenant_of(payload))
        except ChangeStreamError as exc:
            raise _as_error(exc) from exc

    async def watch_get_batch(payload: dict[str, Any], request) -> dict[str, Any]:
        profile_id = str(payload.get("profile") or payload.get("profile_id") or "default")
        _require(request, "data.read", profile_id)
        try:
            return runtime.watch_service.get_batch(
                str(payload["watch_id"]),
                tenant_id=_tenant_of(payload),
                since_cursor=payload.get("since_cursor") or None,
                max_batch=int(payload["max_batch"]) if payload.get("max_batch") else None,
            )
        except ChangeStreamError as exc:
            raise _as_error(exc) from exc

    async def watch_ack(payload: dict[str, Any], request) -> dict[str, Any]:
        profile_id = str(payload.get("profile") or payload.get("profile_id") or "default")
        _require(request, "data.read", profile_id)
        try:
            return runtime.watch_service.ack(
                str(payload["watch_id"]), tenant_id=_tenant_of(payload), ack_cursor=str(payload["ack_cursor"])
            )
        except ChangeStreamError as exc:
            raise _as_error(exc) from exc

    async def watch_recover(payload: dict[str, Any], request) -> dict[str, Any]:
        profile_id = str(payload.get("profile") or payload.get("profile_id") or "default")
        _require(request, "data.read", profile_id)
        try:
            return runtime.watch_service.recover(
                str(payload["watch_id"]), tenant_id=_tenant_of(payload), since_cursor=payload.get("since_cursor") or None
            )
        except ChangeStreamError as exc:
            raise _as_error(exc) from exc

    async def watch_pause(payload: dict[str, Any], request) -> dict[str, Any]:
        profile_id = str(payload.get("profile") or payload.get("profile_id") or "default")
        _require(request, "data.write", profile_id)
        try:
            return runtime.watch_service.pause(str(payload["watch_id"]), tenant_id=_tenant_of(payload))
        except ChangeStreamError as exc:
            raise _as_error(exc) from exc

    async def watch_resume(payload: dict[str, Any], request) -> dict[str, Any]:
        profile_id = str(payload.get("profile") or payload.get("profile_id") or "default")
        _require(request, "data.write", profile_id)
        try:
            return runtime.watch_service.resume(str(payload["watch_id"]), tenant_id=_tenant_of(payload))
        except ChangeStreamError as exc:
            raise _as_error(exc) from exc

    async def watch_delete(payload: dict[str, Any], request) -> dict[str, Any]:
        profile_id = str(payload.get("profile") or payload.get("profile_id") or "default")
        _require(request, "data.write", profile_id)
        try:
            return runtime.watch_service.delete(str(payload["watch_id"]), tenant_id=_tenant_of(payload))
        except ChangeStreamError as exc:
            raise _as_error(exc) from exc

    async def watch_test_event(payload: dict[str, Any], request) -> dict[str, Any]:
        profile_id = str(payload.get("profile") or payload.get("profile_id") or "default")
        _require(request, "data.write", profile_id)
        extra = {
            k: v
            for k, v in payload.items()
            if k not in {"watch_id", "tenant_id", "profile", "profile_id", "action", "object_ref"}
            and not str(k).startswith("_")
        }
        try:
            return runtime.watch_service.test_event(
                str(payload["watch_id"]),
                tenant_id=_tenant_of(payload),
                action=str(payload.get("action", "created")),
                object_ref=str(payload.get("object_ref", "test")),
                **extra,
            )
        except ChangeStreamError as exc:
            raise _as_error(exc) from exc

    async def watch_capabilities(payload: dict[str, Any], request) -> dict[str, Any]:
        profile_id = str(payload.get("profile") or payload.get("profile_id") or "default")
        _require(request, "data.read", profile_id)
        # Honest per-source-type change-capture disposition (PS-102 §6).
        return {"capture_mechanism": "server_mediated", "native_cdc_support": runtime.watch_service.native_cdc_support()}

    return {
        "db_watch_create": ToolContract(name="db_watch_create", handler=watch_create, description="Create a database change-watch with criteria (namespace/entity/entity_pattern/action/value/value_keys) — PS-102 CSTREAM-DB-001/002"),
        "db_watch_list": ToolContract(name="db_watch_list", handler=watch_list, description="List the caller's database change-watches for the current tenant/profile"),
        "db_watch_status": ToolContract(name="db_watch_status", handler=watch_status, description="Return a change-watch status (state, journal depth, cursors, in-flight, throttle)"),
        "db_watch_get_batch": ToolContract(name="db_watch_get_batch", handler=watch_get_batch, description="Retrieve a bounded batch of DB change events since a cursor with the next cursor (backpressure-aware)"),
        "db_watch_ack": ToolContract(name="db_watch_ack", handler=watch_ack, description="Acknowledge change-watch progress up to a cursor, releasing an in-flight batch slot"),
        "db_watch_recover": ToolContract(name="db_watch_recover", handler=watch_recover, description="Re-enquire a safe resume cursor for a change-watch without a replay storm"),
        "db_watch_pause": ToolContract(name="db_watch_pause", handler=watch_pause, description="Pause a change-watch (retains cursor + journal within retention)"),
        "db_watch_resume": ToolContract(name="db_watch_resume", handler=watch_resume, description="Resume a paused change-watch"),
        "db_watch_delete": ToolContract(name="db_watch_delete", handler=watch_delete, description="Delete a change-watch and its journal"),
        "db_watch_test_event": ToolContract(name="db_watch_test_event", handler=watch_test_event, description="Inject a deterministic synthetic change event into a watch's journal (test-mode, no external mutation)"),
        "db_watch_capabilities": ToolContract(name="db_watch_capabilities", handler=watch_capabilities, description="Report the change-capture mechanism and per-database-type native CDC disposition (PS-102 §6)"),
    }
