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
# Description: Database change-watch REST API routes (PS-102 §5.5 / CSTREAM-DB-001).
# Related requirements: CSTREAM-DB-001, CSTREAM-DB-002

"""Database change-watch REST routes (``/v1/watches*``, PS-102 §5.5).

Thin REST projection over the shared :class:`~src.core.change_stream.WatchService`
adapter. Lifecycle + pull-batch retrieval + a Server-Sent-Events feed (``/events``,
resumable via ``Last-Event-ID``). RBAC is enforced per request against the
authenticated principal; the journal/cursor/queue/SSE-frame primitives are all
consumed from the common foundation (RULES §1.4).
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from cloud_dog_api_kit import success_envelope
from cloud_dog_api_kit.change_stream import to_sse_frame
from cloud_dog_api_kit.change_stream.envelope import ChangeEvent
from cloud_dog_api_kit.change_stream.errors import (
    ChangeStreamError,
    CursorExpired,
    RateLimited,
    Unauthorised as _CSUnauthorised,
    WatchNotFound,
)


def _tenant_from(payload_or_query: dict[str, Any]) -> str:
    return str(
        payload_or_query.get("tenant_id")
        or payload_or_query.get("profile")
        or payload_or_query.get("profile_id")
        or "default"
    )


def _watch_error(exc: ChangeStreamError) -> HTTPException:
    """Map a change-stream error to a truthful HTTP response with its code."""
    detail = exc.to_dict()
    if isinstance(exc, WatchNotFound):
        return HTTPException(status_code=404, detail=detail)
    if isinstance(exc, _CSUnauthorised):
        return HTTPException(status_code=403, detail=detail)
    if isinstance(exc, RateLimited):
        return HTTPException(status_code=429, detail=detail)
    if isinstance(exc, CursorExpired):
        return HTTPException(status_code=409, detail=detail)
    return HTTPException(status_code=400, detail=detail)


def create_watches_router(runtime, base_path: str) -> APIRouter:
    """Create the database change-watch REST routes (PS-102 §5.5)."""
    access = runtime.access_control
    router = APIRouter(prefix=base_path, tags=["change-watches"])

    def _require(request: Request, permission: str, profile_id: str):
        return access.require_request_permission(
            request,
            permission=permission,
            profile_id=profile_id,
            audit_resource_type="change_watch",
            audit_resource_id=profile_id,
        )

    async def _body(request: Request) -> dict[str, Any]:
        try:
            raw = await request.body()
        except Exception:
            return {}
        if not raw or not raw.strip():
            return {}
        import json

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=422, detail="request body must be a JSON object") from exc
        if not isinstance(data, dict):
            raise HTTPException(status_code=422, detail="request body must be a JSON object")
        return data

    @router.post("/watches")
    async def create_watch(request: Request) -> dict:
        payload = await _body(request)
        profile_id = str(payload.get("profile") or payload.get("profile_id") or "default")
        principal = _require(request, "data.create", profile_id)
        try:
            return success_envelope(
                runtime.watch_service.create_watch(
                    profile_id=profile_id,
                    tenant_id=_tenant_from(payload),
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
            )
        except ChangeStreamError as exc:
            raise _watch_error(exc) from exc

    @router.get("/watches")
    async def list_watches(request: Request, profile: str = "default", tenant_id: str | None = None) -> dict:
        _require(request, "data.read", profile)
        tenant = str(tenant_id or profile or "default")
        return success_envelope({"watches": runtime.watch_service.list_watches(tenant_id=tenant)})

    @router.get("/watches/capabilities")
    async def watch_capabilities(request: Request, profile: str = "default") -> dict:
        _require(request, "data.read", profile)
        # Honest per-source-type change-capture disposition (PS-102 §6).
        return success_envelope(
            {
                "capture_mechanism": "server_mediated",
                "native_cdc_support": runtime.watch_service.native_cdc_support(),
            }
        )

    @router.get("/watches/{watch_id}")
    async def get_watch(watch_id: str, request: Request, profile: str = "default", tenant_id: str | None = None) -> dict:
        _require(request, "data.read", profile)
        tenant = str(tenant_id or profile or "default")
        try:
            return success_envelope(runtime.watch_service.get_watch(watch_id, tenant_id=tenant))
        except ChangeStreamError as exc:
            raise _watch_error(exc) from exc

    @router.get("/watches/{watch_id}/status")
    async def get_status(watch_id: str, request: Request, profile: str = "default", tenant_id: str | None = None) -> dict:
        _require(request, "data.read", profile)
        tenant = str(tenant_id or profile or "default")
        try:
            return success_envelope(runtime.watch_service.get_status(watch_id, tenant_id=tenant))
        except ChangeStreamError as exc:
            raise _watch_error(exc) from exc

    @router.get("/watches/{watch_id}/events")
    async def get_events(
        watch_id: str,
        request: Request,
        profile: str = "default",
        tenant_id: str | None = None,
        since_cursor: str | None = None,
        max_batch: int | None = None,
    ) -> dict:
        """Pull-batch / bounded batch retrieval (PS-102 §5.2 base mode).

        Nonblocking: an empty batch + current cursor is returned immediately when
        no events are pending (CSTREAM-002). The SSE feed (``/stream``) is
        additive for the streaming retrieval mode.
        """
        _require(request, "data.read", profile)
        tenant = str(tenant_id or profile or "default")
        try:
            return success_envelope(
                runtime.watch_service.get_batch(
                    watch_id,
                    tenant_id=tenant,
                    since_cursor=since_cursor or None,
                    max_batch=int(max_batch) if max_batch else None,
                )
            )
        except ChangeStreamError as exc:
            raise _watch_error(exc) from exc

    @router.get("/watches/{watch_id}/stream")
    async def stream_events(
        watch_id: str,
        request: Request,
        profile: str = "default",
        tenant_id: str | None = None,
        since_cursor: str | None = None,
    ) -> StreamingResponse:
        """Server-Sent-Events feed for the streaming retrieval mode (PS-102 §5.2).

        Renders the currently-journalled batch as SSE frames whose ``id`` is the
        opaque cursor, so a reconnecting consumer resumes via ``Last-Event-ID``.
        This is a nonblocking snapshot stream (no long-lived worker hold); the
        consumer reconnects with the last id to continue.
        """
        _require(request, "data.read", profile)
        tenant = str(tenant_id or profile or "default")
        resume = since_cursor or request.headers.get("last-event-id") or None
        try:
            batch = runtime.watch_service.get_batch(watch_id, tenant_id=tenant, since_cursor=resume)
        except ChangeStreamError as exc:
            raise _watch_error(exc) from exc

        def _frames():
            for event_dict in batch.get("events", []):
                yield to_sse_frame(ChangeEvent.from_dict(event_dict), redact=True)

        return StreamingResponse(_frames(), media_type="text/event-stream")

    @router.post("/watches/{watch_id}/ack")
    async def ack(watch_id: str, request: Request) -> dict:
        payload = await _body(request)
        profile_id = str(payload.get("profile") or payload.get("profile_id") or "default")
        _require(request, "data.read", profile_id)
        if not payload.get("ack_cursor"):
            raise HTTPException(status_code=422, detail="ack_cursor is required")
        try:
            return success_envelope(
                runtime.watch_service.ack(watch_id, tenant_id=_tenant_from(payload), ack_cursor=str(payload["ack_cursor"]))
            )
        except ChangeStreamError as exc:
            raise _watch_error(exc) from exc

    @router.post("/watches/{watch_id}/recover")
    async def recover(watch_id: str, request: Request) -> dict:
        payload = await _body(request)
        profile_id = str(payload.get("profile") or payload.get("profile_id") or "default")
        _require(request, "data.read", profile_id)
        try:
            return success_envelope(
                runtime.watch_service.recover(
                    watch_id, tenant_id=_tenant_from(payload), since_cursor=payload.get("since_cursor") or None
                )
            )
        except ChangeStreamError as exc:
            raise _watch_error(exc) from exc

    @router.post("/watches/{watch_id}/pause")
    async def pause(watch_id: str, request: Request) -> dict:
        payload = await _body(request)
        profile_id = str(payload.get("profile") or payload.get("profile_id") or "default")
        _require(request, "data.create", profile_id)
        try:
            return success_envelope(runtime.watch_service.pause(watch_id, tenant_id=_tenant_from(payload)))
        except ChangeStreamError as exc:
            raise _watch_error(exc) from exc

    @router.post("/watches/{watch_id}/resume")
    async def resume(watch_id: str, request: Request) -> dict:
        payload = await _body(request)
        profile_id = str(payload.get("profile") or payload.get("profile_id") or "default")
        _require(request, "data.create", profile_id)
        try:
            return success_envelope(runtime.watch_service.resume(watch_id, tenant_id=_tenant_from(payload)))
        except ChangeStreamError as exc:
            raise _watch_error(exc) from exc

    @router.post("/watches/{watch_id}/test-event")
    async def test_event(watch_id: str, request: Request) -> dict:
        payload = await _body(request)
        profile_id = str(payload.get("profile") or payload.get("profile_id") or "default")
        _require(request, "data.create", profile_id)
        extra = {
            k: v
            for k, v in payload.items()
            if k not in {"watch_id", "tenant_id", "profile", "profile_id", "action", "object_ref"}
        }
        try:
            return success_envelope(
                runtime.watch_service.test_event(
                    watch_id,
                    tenant_id=_tenant_from(payload),
                    action=str(payload.get("action", "created")),
                    object_ref=str(payload.get("object_ref", "test")),
                    **extra,
                )
            )
        except ChangeStreamError as exc:
            raise _watch_error(exc) from exc

    @router.delete("/watches/{watch_id}")
    async def delete_watch(watch_id: str, request: Request, profile: str = "default", tenant_id: str | None = None) -> dict:
        _require(request, "data.create", profile)
        tenant = str(tenant_id or profile or "default")
        try:
            return success_envelope(runtime.watch_service.delete(watch_id, tenant_id=tenant))
        except ChangeStreamError as exc:
            raise _watch_error(exc) from exc

    return router
