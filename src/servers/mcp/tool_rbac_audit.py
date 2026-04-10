"""Per-tool RBAC permission map and audit logging for db-mcp MCP tools.

Centralises RBAC enforcement (PS-70 UM3) and audit logging (PS-40 L3)
for all ~45 registered MCP tools. Uses cloud_dog_idam.RBACEngine for
permission checks and cloud_dog_logging for structured audit events.

Related: W28A-746, PS-70 UM3, PS-40 L3, PS-50
"""

from __future__ import annotations

import time
from typing import Any, Callable, Dict

from cloud_dog_idam import RBACEngine
from cloud_dog_logging import get_logger  # type: ignore[import-untyped]

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
