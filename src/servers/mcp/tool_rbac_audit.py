"""Per-tool RBAC permission map and audit logging for db-mcp MCP tools.

Centralises RBAC enforcement (PS-70 UM3) and audit logging (PS-40 L3)
for all ~45 registered MCP tools. Uses cloud_dog_idam.RBACEngine for
permission checks and cloud_dog_logging for structured audit events.

Related: W28A-746, PS-70 UM3, PS-40 L3, PS-50
"""

from __future__ import annotations

import dataclasses
import time
from typing import Any, Callable, Dict

from cloud_dog_api_kit.mcp.tool_router import ToolContract
from cloud_dog_idam import RBACEngine
from cloud_dog_logging import get_logger  # type: ignore[import-untyped]
from cloud_dog_logging.audit_logger import Actor, Target

logger = get_logger("db_mcp_server.mcp.tools")

# ── PS-70 UM3: Per-tool RBAC permission map ──────────────────────────────
# Destructive operations (drop, raw execute, restore) require admin.

TOOL_RBAC_MAP: Dict[str, str] = {
    # Catalog (read)
    "catalog.list_namespaces": "db:catalog:read",
    "catalog.list_entities": "db:catalog:read",
    "catalog.get_entity": "db:catalog:read",
    "catalog.search": "db:catalog:read",
    # Schema (read + admin for mutations)
    "schema.describe_entity": "db:schema:read",
    "schema.describe_fields": "db:schema:read",
    "schema.list_indexes": "db:schema:read",
    "schema.sample_shapes": "db:schema:read",
    "schema.change.plan": "db:schema:read",
    "schema.change.apply": "db:schema:migrate",  # admin/owner only
    "schema.change.history": "db:schema:read",
    # Content CRUD
    "data.read": "db:data:read",
    "data.count": "db:data:read",
    "data.exists": "db:data:read",
    "data.create": "db:data:write",
    "data.update": "db:data:write",
    "data.delete": "db:data:delete",  # elevated
    # Search / discovery
    "search.metadata": "db:search:read",
    "search.content": "db:search:read",
    "search.related": "db:search:read",
    "search.explain_match": "db:search:read",
    # Index management
    "index.status": "db:index:read",
    "index.sync_profile": "db:index:write",
    "index.sync_entity": "db:index:write",
    "index.rebuild": "db:index:write",
    # Relationships
    "relationship.list": "db:relationship:read",
    "relationship.get": "db:relationship:read",
    "relationship.create": "db:relationship:write",
    "relationship.update": "db:relationship:write",
    "relationship.delete": "db:relationship:delete",
    "relationship.infer": "db:relationship:write",
    # Profiles (admin)
    "profiles.list": "db:profile:read",
    "profiles.get": "db:profile:read",
    "profiles.create": "db:admin:*",
    "profiles.update": "db:admin:*",
    "profiles.delete": "db:admin:*",
    # Access control / IDAM (admin)
    "users.list": "db:admin:*",
    "users.create": "db:admin:*",
    "groups.list": "db:admin:*",
    "groups.create": "db:admin:*",
    "api_keys.list": "db:admin:*",
    "api_keys.create": "db:admin:*",
    "api_keys.revoke": "db:admin:*",
    # Audit (admin read)
    "audit.list_events": "db:audit:read",
    "audit.get_event": "db:audit:read",
    # Change-watch (W28E-1870-E, PS-102 §7): read verbs need data:read, mutating
    # lifecycle verbs need data:write. Enforced per call in watch_tools against
    # the requesting principal, scoped to the watched profile.
    "db_watch_list": "db:data:read",
    "db_watch_status": "db:data:read",
    "db_watch_get_batch": "db:data:read",
    "db_watch_ack": "db:data:read",
    "db_watch_recover": "db:data:read",
    "db_watch_capabilities": "db:data:read",
    "db_watch_create": "db:data:write",
    "db_watch_pause": "db:data:write",
    "db_watch_resume": "db:data:write",
    "db_watch_delete": "db:data:write",
    "db_watch_test_event": "db:data:write",
}


def check_tool_permission(tool_name: str, user_role: str = "user") -> bool:
    """Check per-tool RBAC via cloud_dog_idam.RBACEngine.has_permission."""
    required = TOOL_RBAC_MAP.get(tool_name, "db:tool:execute")
    if user_role == "admin":
        return True
    engine = RBACEngine()
    engine.assign_role_to_user(user_role, user_role)
    return engine.has_permission(user_role, required)


# ── PS-40 L3: Tool audit logging with redaction ──────────────────────────

_REDACT_KEYS = {
    "password", "secret", "token", "api_key", "connection_string",
    "connection_uri", "uri", "bind_params", "bind_parameters",
    "row_data", "values", "records", "documents",
}


def _redact_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Redact bind params, row data, connection strings from audit logs."""
    redacted: Dict[str, Any] = {}
    for key, value in (params or {}).items():
        lower = key.lower()
        if any(s in lower for s in _REDACT_KEYS):
            if isinstance(value, str):
                redacted[key] = f"[REDACTED {len(value)} chars]"
            elif isinstance(value, (list, dict)):
                redacted[key] = f"[REDACTED {len(value)} items]"
            else:
                redacted[key] = "[REDACTED]"
        else:
            redacted[key] = value
    return redacted


def audit_tool_call(
    tool_name: str,
    params: Dict[str, Any],
    *,
    success: bool = True,
    duration_ms: float = 0.0,
    error: str = "",
    actor_id: str = "",
    correlation_id: str = "",
) -> None:
    """Emit structured audit event for a db-mcp MCP tool call (PS-40 L3)."""
    logger.info(
        f"mcp_tool_audit tool={tool_name} outcome={'success' if success else 'failure'}"
        f" duration_ms={duration_ms:.0f} actor={actor_id}"
    )


# ── TD-001 (W28E-1808B): full NIST AU-3 MCP audit emission ───────────────────
# Every MCP tool call emits a fully-populated audit event through the platform
# AuditLogger (PS-AUDIT-LOG §3): actor (id/roles/ip), target, outcome,
# correlation_id, session_id, duration. Mirrors the API AuditMiddleware path so
# the MCP surface is no longer un-audited (TD-001 / DM-AL-09 / DM-X-19).

# payload keys that identify the target resource of a tool call, best-first.
_TARGET_ID_KEYS = (
    "entity", "entity_name", "namespace", "profile_id", "profile",
    "name", "relationship_id", "query_id", "user_id", "group_id",
    "api_key_id", "event_id", "id",
)


def _derive_target(tool_name: str, params: Dict[str, Any]) -> Target:
    """Derive a PS-AUDIT-LOG Target from the tool name + payload (best-effort)."""
    target_type = tool_name.split(".", 1)[0] or "tool"
    target_id = "-"
    for key in _TARGET_ID_KEYS:
        value = (params or {}).get(key)
        if value not in (None, ""):
            target_id = str(value)
            break
    return Target(type=target_type, id=target_id, name=tool_name)


def _actor_from_request(request: Any) -> Actor:
    """Build a PS-AUDIT-LOG Actor (id/roles/ip) from request.state (auth middleware)."""
    state = getattr(request, "state", None)
    user_id = getattr(state, "user", None) if state is not None else None
    roles = getattr(state, "roles", None) if state is not None else None
    client = getattr(request, "client", None)
    ip = getattr(client, "host", None) if client is not None else None
    if not user_id:
        # W28E-1879: platform Actor type must be user/service/system — use the
        # AuditMiddleware "system/anonymous" convention so denied/anonymous
        # requests are still auditable (PS-AUDIT-LOG §4), not swallowed.
        return Actor(type="system", id="anonymous", roles=None, ip=ip)
    return Actor(type="user", id=str(user_id), roles=list(roles) if roles else None, ip=ip)


def actor_from_principal(principal: Any, *, ip: str | None = None) -> Actor:
    """Build a PS-AUDIT-LOG Actor from a resolved access-control principal object.

    Used where the authenticated subject is a principal object rather than
    request.state (e.g. the A2A task boundary). Carries id/roles/ip so the emitted
    AU-3 event names the real subject and client IP (W28E-1879 / DM-X-19).
    """
    user_id = getattr(principal, "user_id", None) or getattr(principal, "username", None)
    roles = getattr(principal, "roles", None)
    if not user_id:
        return Actor(type="system", id="anonymous", roles=None, ip=ip)
    return Actor(type="user", id=str(user_id), roles=list(roles) if roles else None, ip=ip)


def au3_request_fields(request: Any) -> Dict[str, Any]:
    """Return the NIST AU-3 request-context fields for a platform AuditLogger call.

    This is the single, shared source of AU-3 request context consumed by the MCP,
    REST, and A2A audit emit paths (W28E-1879: DM-AL-09 / DM-D-12 / DM-X-19). It is
    a thin adapter over the platform ``cloud_dog_logging`` schema — it does not
    reimplement any audit logic.

    Returned keys (all spread into the ``log_*`` call, so they land in the event):
      - ``client_ip``      — the NIST AU-3 client IP. Also read by the caller for
        ``Actor(ip=...)``. Carried in ``details.client_ip`` (unredacted on every
        ``cloud_dog_logging`` version) plus ``actor.ip`` — this is the canonical,
        version-independent client-IP/source-address carriage.
      - ``source_address`` — kept for compatibility: on package versions whose
        ``AuditEvent`` exposes a top-level ``source_address`` field it is emitted
        there; on versions without it the value is redacted in ``details`` (the
        redaction engine masks any ``*address`` key). Rely on ``client_ip``/
        ``actor.ip`` for the AU-3 value, not this key.
      - ``session_id``     — lands in ``details.session_id``.
      - ``correlation_id`` — when present, mirrored into ``details``; the top-level
        ``correlation_id`` is taken from the request correlation contextvar.
    """
    state = getattr(request, "state", None)
    client = getattr(request, "client", None)
    client_ip = getattr(client, "host", None) if client is not None else None
    correlation_id = getattr(state, "correlation_id", None) if state is not None else None
    session_id = (
        getattr(state, "session_id", None) or getattr(state, "api_key_id", None)
        if state is not None else None
    )
    fields: Dict[str, Any] = {
        "client_ip": client_ip,
        "source_address": client_ip,
        "session_id": session_id,
    }
    if correlation_id:
        fields["correlation_id"] = correlation_id
    return fields


def emit_tool_audit(
    audit_logger: Any,
    *,
    tool_name: str,
    request: Any,
    params: Dict[str, Any],
    success: bool,
    duration_ms: float,
    error: str = "",
) -> None:
    """Emit a full NIST AU-3 audit event for an MCP tool call via the platform AuditLogger."""
    fields = au3_request_fields(request)
    actor = _actor_from_request(request)
    target = _derive_target(tool_name, params)
    details: Dict[str, Any] = {
        "target_type": target.type,
        "target_id": target.id,
        "target_name": target.name,
        **fields,  # client_ip, source_address, session_id, [correlation_id]
    }
    if not success and error:
        details["error_code"] = "tool_error"
        details["error_message"] = error
    try:
        audit_logger.log_tool_call(
            actor,
            tool_name,
            _redact_params(params if isinstance(params, dict) else {}),
            "success" if success else "failure",
            int(duration_ms),
            **details,
        )
    except Exception:  # noqa: BLE001 — audit must never break the tool call
        logger.exception(f"mcp_tool_audit emit failed tool={tool_name}")


def emit_a2a_audit(
    audit_logger: Any,
    *,
    request: Any,
    principal: Any,
    skill_id: str,
    input_text: str,
    success: bool,
    duration_ms: float,
    error: str = "",
) -> None:
    """Emit a full NIST AU-3 audit event for an A2A task via the platform AuditLogger.

    Closes DM-X-19: the A2A surface was previously un-audited (its skills call the
    MCP tool handlers via a synthetic request that bypasses ``wrap_tool_contract``).
    This emits one AU-3-complete event per task at the dispatch boundary, using the
    REAL inbound request (client IP / correlation / session) plus the resolved
    principal (actor id/roles).
    """
    if audit_logger is None:
        return
    fields = au3_request_fields(request)
    client_ip = fields.get("client_ip")
    actor = actor_from_principal(principal, ip=client_ip)
    details: Dict[str, Any] = {
        "target_type": "a2a_task",
        "target_id": skill_id,
        "target_name": f"a2a.{skill_id}",
        "surface": "a2a",
        **fields,  # client_ip, source_address, session_id, [correlation_id]
    }
    if not success and error:
        details["error_code"] = "a2a_error"
        details["error_message"] = error[:200]
    try:
        audit_logger.log_tool_call(
            actor,
            f"a2a.{skill_id}",
            {"input_chars": len(input_text or "")},
            "success" if success else "failure",
            int(duration_ms),
            **details,
        )
    except Exception:  # noqa: BLE001 — audit must never break the task
        logger.exception(f"a2a_audit emit failed skill={skill_id}")


def wrap_tool_contract(runtime: Any, contract: ToolContract) -> ToolContract:
    """Return a copy of the ToolContract whose handler emits a full AU-3 audit event.

    The wrapped handler keeps the platform (payload, request) signature so it is
    transparent to register_tool_router / register_mcp_routes.
    """
    inner = contract.handler
    tool_name = contract.name
    audit_logger = getattr(runtime, "audit_logger", None)
    if audit_logger is None:
        return contract

    async def _audited(payload: Dict[str, Any], request: Any) -> Any:
        start = time.monotonic()
        success = True
        error_msg = ""
        try:
            result = inner(payload, request)
            if hasattr(result, "__await__"):
                result = await result
            return result
        except Exception as exc:  # noqa: BLE001
            success = False
            error_msg = str(exc)[:200]
            raise
        finally:
            emit_tool_audit(
                audit_logger,
                tool_name=tool_name,
                request=request,
                params=payload if isinstance(payload, dict) else {},
                success=success,
                duration_ms=(time.monotonic() - start) * 1000,
                error=error_msg,
            )

    return dataclasses.replace(contract, handler=_audited)


def wrap_tool_with_audit(tool_name: str, handler: Callable) -> Callable:
    """Wrap a tool handler with audit logging and RBAC check."""

    async def _audited_handler(*args: Any, **kwargs: Any) -> Any:
        start = time.monotonic()
        success = True
        error_msg = ""
        try:
            result = handler(*args, **kwargs)
            if hasattr(result, "__await__"):
                result = await result
            return result
        except Exception as exc:
            success = False
            error_msg = str(exc)[:200]
            raise
        finally:
            duration_ms = (time.monotonic() - start) * 1000
            params = args[0] if args and isinstance(args[0], dict) else kwargs
            audit_tool_call(
                tool_name,
                _redact_params(params if isinstance(params, dict) else {}),
                success=success,
                duration_ms=duration_ms,
                error=error_msg,
            )

    _audited_handler.__name__ = f"audited_{tool_name}"
    _audited_handler.__qualname__ = f"audited_{tool_name}"
    return _audited_handler
