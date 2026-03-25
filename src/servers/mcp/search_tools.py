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
# Description: Discovery search and indexing MCP tools.
# Related requirements: W28A-274-I deliverables 3, 4
# Related tests: ST1.7, IT1.6

"""Search and indexing MCP tool registry."""

from __future__ import annotations

from typing import Any, Callable

from cloud_dog_api_kit import ToolContract
from cloud_dog_logging import Actor


def build_search_tool_registry(runtime) -> dict[str, ToolContract]:
    """Build discovery search and index management tools."""
    search = runtime.search
    access_control = runtime.access_control
    audit_logger = runtime.audit_logger

    async def _run(
        request,
        *,
        permission: str,
        audit_action: str,
        audit_target_id: str,
        callback: Callable[[Any], dict[str, Any]],
        profile_id: str | None = None,
    ) -> dict[str, Any]:
        principal = access_control.require_request_permission(
            request,
            permission=permission,
            profile_id=profile_id,
            audit_resource_type="profile" if profile_id else "service",
            audit_resource_id=audit_target_id,
        )
        try:
            result = callback(principal)
        except Exception as exc:
            audit_logger.log_tool_call(
                actor=Actor(type="user", id=principal.user_id, roles=principal.roles),
                tool=audit_action,
                params={"profile_id": profile_id, "target": audit_target_id},
                outcome="failure",
                duration_ms=0,
                error=str(exc),
            )
            raise
        audit_logger.log_tool_call(
            actor=Actor(type="user", id=principal.user_id, roles=principal.roles),
            tool=audit_action,
            params={"profile_id": profile_id, "target": audit_target_id},
            outcome="success",
            duration_ms=0,
        )
        return result

    async def search_metadata(payload: dict[str, Any], request) -> dict[str, Any]:
        profile_id = str(payload.get("profile_id", ""))
        query = str(payload.get("query", ""))
        limit = int(payload.get("limit") or runtime.config.get("search.metadata_limit", 20))
        return _ensure_awaitable(
            await _run(
                request,
                permission="content.search",
                audit_action="search.metadata",
                audit_target_id=profile_id,
                profile_id=profile_id,
                callback=lambda _principal: {"items": search.search_metadata(profile_id=profile_id, query=query, limit=limit)},
            )
        )

    async def search_content(payload: dict[str, Any], request) -> dict[str, Any]:
        profile_id = str(payload.get("profile_id", ""))
        query = str(payload.get("query", ""))
        limit = int(payload.get("limit") or runtime.config.get("search.content_limit", 20))
        return _ensure_awaitable(
            await _run(
                request,
                permission="content.search",
                audit_action="search.content",
                audit_target_id=profile_id,
                profile_id=profile_id,
                callback=lambda _principal: {"items": search.search_content(profile_id=profile_id, query=query, limit=limit)},
            )
        )

    async def search_related(payload: dict[str, Any], request) -> dict[str, Any]:
        profile_id = str(payload.get("profile_id", ""))
        namespace = str(payload.get("namespace", ""))
        entity = str(payload.get("entity", ""))
        limit = int(payload.get("limit") or 10)
        return _ensure_awaitable(
            await _run(
                request,
                permission="content.search",
                audit_action="search.related",
                audit_target_id=f"{profile_id}:{namespace}.{entity}",
                profile_id=profile_id,
                callback=lambda _principal: {
                    "items": search.search_related(profile_id=profile_id, namespace=namespace, entity=entity, limit=limit)
                },
            )
        )

    async def explain_match(payload: dict[str, Any], request) -> dict[str, Any]:
        profile_id = str(payload.get("profile_id", ""))
        query = str(payload.get("query", ""))
        document_id = str(payload.get("document_id", ""))
        return _ensure_awaitable(
            await _run(
                request,
                permission="content.search",
                audit_action="search.explain_match",
                audit_target_id=document_id,
                profile_id=profile_id,
                callback=lambda _principal: search.explain_match(profile_id=profile_id, query=query, document_id=document_id),
            )
        )

    async def index_status(payload: dict[str, Any], request) -> dict[str, Any]:
        profile_id = str(payload.get("profile_id", "")).strip()
        return _ensure_awaitable(
            await _run(
                request,
                permission="index.manage",
                audit_action="index.status",
                audit_target_id=profile_id or "all-profiles",
                profile_id=profile_id or None,
                callback=lambda principal: search.index_status(
                    profile_ids=[profile_id] if profile_id else search._resolve_accessible_profiles(principal)
                ),
            )
        )

    async def sync_profile(payload: dict[str, Any], request) -> dict[str, Any]:
        profile_id = str(payload.get("profile_id", ""))
        return _ensure_awaitable(
            await _run(
                request,
                permission="index.manage",
                audit_action="index.sync_profile",
                audit_target_id=profile_id,
                profile_id=profile_id,
                callback=lambda principal: search.sync_profile(profile_id=profile_id, principal=principal),
            )
        )

    async def sync_entity(payload: dict[str, Any], request) -> dict[str, Any]:
        profile_id = str(payload.get("profile_id", ""))
        namespace = str(payload.get("namespace", ""))
        entity = str(payload.get("entity", ""))
        return _ensure_awaitable(
            await _run(
                request,
                permission="index.manage",
                audit_action="index.sync_entity",
                audit_target_id=f"{profile_id}:{namespace}.{entity}",
                profile_id=profile_id,
                callback=lambda principal: search.sync_entity(
                    profile_id=profile_id,
                    namespace=namespace,
                    entity=entity,
                    principal=principal,
                ),
            )
        )

    async def rebuild(payload: dict[str, Any], request) -> dict[str, Any]:
        requested = [str(item) for item in payload.get("profile_ids", [])]
        return _ensure_awaitable(
            await _run(
                request,
                permission="index.manage",
                audit_action="index.rebuild",
                audit_target_id=",".join(requested) or "all-profiles",
                callback=lambda principal: search.rebuild(principal=principal, profile_ids=requested or None),
            )
        )

    return {
        "search.metadata": ToolContract(name="search.metadata", handler=search_metadata, description="Search entity, field, namespace, and relationship metadata"),
        "search.content": ToolContract(name="search.content", handler=search_content, description="Search indexed content excerpts"),
        "search.related": ToolContract(name="search.related", handler=search_related, description="Find related entities for a given entity"),
        "search.explain_match": ToolContract(name="search.explain_match", handler=explain_match, description="Explain why a discovery search result matched"),
        "index.status": ToolContract(name="index.status", handler=index_status, description="Show discovery index freshness and coverage"),
        "index.sync_profile": ToolContract(name="index.sync_profile", handler=sync_profile, description="Queue and execute a profile discovery index refresh"),
        "index.sync_entity": ToolContract(name="index.sync_entity", handler=sync_entity, description="Queue and execute an entity discovery index refresh"),
        "index.rebuild": ToolContract(name="index.rebuild", handler=rebuild, description="Queue and execute a full discovery index rebuild"),
    }


def _ensure_awaitable(result: dict[str, Any]) -> dict[str, Any]:
    """Keep tool handlers explicit about returning plain payloads."""
    return result
