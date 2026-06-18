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
# Description: Access-control orchestration service for db-mcp-server.
# Related requirements: AC-01, AC-02, AC-03, CFG-01
# Related tests: UT1.3, ST1.2, IT1.1

"""Access-control orchestration service for db-mcp-server."""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import re
import time
from dataclasses import asdict, dataclass
from datetime import timedelta
from typing import Any

from fastapi import Request
from sqlalchemy import Engine
from sqlalchemy.orm import sessionmaker

from cloud_dog_api_kit.errors import (
    ConflictError,
    NotFoundError,
    UnauthorisedError,
    ValidationError,
)
from cloud_dog_idam.api_keys.hashing import hash_api_key, key_matches
from cloud_dog_idam import RBACEngine
from cloud_dog_idam.domain.models import Role
from cloud_dog_idam.storage.sqlalchemy.models import (
    PermissionORM,
    RoleORM,
    RolePermissionORM,
)
from cloud_dog_idam.storage.sqlalchemy.role_store import (
    BaselineRoleProtected,
    SqlAlchemyRoleStore,
)
from cloud_dog_logging import Actor, Target
from cloud_dog_logging.audit_logger import AuditLogger

from src.core.access_control.models import (
    AccessApiKey,
    AccessGroup,
    AccessUser,
    DEFAULT_ROLE_PERMISSIONS,
    PERMISSION_DOMAINS,
    Profile,
    ROLE_NAMES,
    SAVED_QUERY_PAGE_PERMISSIONS,
    SOURCE_CONNECTION_STATUSES,
    SOURCE_CONNECTION_TYPES,
    SavedQuery,
    SourceConnection,
    ensure_known_permissions,
    utcnow,
)
from src.core.access_control.repository import AccessControlRepository
from src.common.storage_paths import ensure_directory, join_fs_path, write_text_file


FLAT_DEMO_ROLES: tuple[tuple[str, str, str, str], ...] = (
    ("flat-admin", "flat-admin", "Flat Admin", "admin"),
    ("flat-read-write", "flat-read-write", "Flat Read Write", "read-write"),
    ("flat-read-only", "flat-read-only", "Flat Read Only", "read-only"),
)


def _mask_connection_secret(value: Any) -> Any:
    """Mask the password embedded in a DB connection string.

    W28A-889-B-R2 / W28A-890: profile reads (/v1/profiles) must never return the
    DB credential. Masks both URI userinfo (``scheme://user:password@host`` ->
    ``scheme://user:****@host``) and DSN/keyword forms (``password=...``).
    """
    if not isinstance(value, str) or not value:
        return value
    masked = re.sub(r"(://[^:/@\s]+:)[^@/\s]+(@)", r"\1****\2", value)
    masked = re.sub(r"(?i)(\b(?:password|passwd|pwd)\s*=\s*)[^;\s]+", r"\1****", masked)
    return masked


@dataclass(slots=True)
class PrincipalContext:
    """Resolved authenticated principal context for request enforcement."""

    user_id: str
    username: str
    roles: list[str]
    permissions: list[str]
    api_key_id: str | None
    profile_ids: list[str]
    scopes: list[str]
    tenant_id: str | None = None


class AccessControlService:
    """Manage users, groups, profiles, keys, and permission evaluation."""

    _SOURCE_CONNECTION_NAME_RE = re.compile(r"^[a-z0-9_-]{1,100}$")

    def __init__(self, *, config: Any, engine: Engine, audit_logger: AuditLogger) -> None:
        self._config = config
        self._engine = engine
        self._repository = AccessControlRepository(engine)
        self._audit_logger = audit_logger
        # W28A-876 Gate 4b: ensure the canonical cloud_dog_idam role tables exist
        # so the PS-71 §IW3A Roles page (/api/v1/admin/roles) is backed by the
        # shared SqlAlchemyRoleStore. Only the role-related tables are created
        # here; the rest of the idam schema is not part of this service.
        RoleORM.metadata.create_all(
            bind=engine,
            checkfirst=True,
            tables=[
                RoleORM.__table__,
                PermissionORM.__table__,
                RolePermissionORM.__table__,
            ],
        )
        self._role_session_factory = sessionmaker(bind=engine, expire_on_commit=False)
        # W28A-871-R2: connector manager wired post-construction by the runtime;
        # used by test_profile_scope to probe namespaces/entities for a profile.
        self._connector_manager: Any | None = None
        configured_permissions = config.get("access_control.roles", {}) or {}
        role_permissions = {role: set(values) for role, values in DEFAULT_ROLE_PERMISSIONS.items()}
        role_permissions.update({
            role: set(values)
            for role, values in configured_permissions.items()
        })
        self._role_permissions = role_permissions
        self._rbac = RBACEngine(role_overlay=self._role_permissions)
        self._bootstrap_user_id = str(config.get("access_control.bootstrap_admin.user_id", "bootstrap-admin"))
        self._bootstrap_username = str(
            config.get("access_control.bootstrap_admin.username", "bootstrap-admin")
        )
        self._bootstrap_display_name = str(
            config.get("access_control.bootstrap_admin.display_name", "Bootstrap Admin")
        )
        self._bootstrap_api_key_name = str(
            config.get("access_control.bootstrap_admin.api_key_name", "bootstrap-admin-key")
        )
        self._bootstrap_api_key = str(config.get("auth.api_key", "") or "")
        self._bootstrap_role = str(config.get("auth.default_role", "admin") or "admin")
        self._seed_bootstrap_admin()
        self._seed_flat_demo_keys()
        self.ensure_roles_seed()
        self._seed_default_group()

    def _seed_default_group(self) -> None:
        """Idempotently seed one baseline group so the IDAM Groups page renders a
        real row rather than an empty 0-record table (W28A-889-B-R2). The
        bootstrap admin is its member and it carries the data_steward role."""
        if self._repository.list_groups():
            return
        group = AccessGroup(
            group_id="data-stewards",
            name="data-stewards",
            description="Baseline data-steward group (catalog and schema read access).",
            roles=["data_steward"],
            member_user_ids=[self._bootstrap_user_id],
        )
        self._repository.upsert_group(group)
        self._rebuild_rbac()

    def bind_connector_manager(self, connector_manager: Any) -> None:
        """Attach the connector manager after runtime construction."""
        self._connector_manager = connector_manager

    def _seed_bootstrap_admin(self) -> None:
        existing_user = self._repository.get_user(self._bootstrap_user_id)
        if existing_user is None:
            existing_user = AccessUser(
                user_id=self._bootstrap_user_id,
                username=self._bootstrap_username,
                display_name=self._bootstrap_display_name,
                email="",
                roles=[self._bootstrap_role],
                status="active",
            )
            self._repository.upsert_user(existing_user)
        elif self._bootstrap_role not in existing_user.roles:
            existing_user.roles = sorted(set(existing_user.roles + [self._bootstrap_role]))
            existing_user.updated_at = utcnow()
            self._repository.upsert_user(existing_user)

        if not self._bootstrap_api_key:
            return

        existing_keys = self._repository.list_api_keys(self._bootstrap_user_id)
        wanted_hash = hash_api_key(self._bootstrap_api_key)
        for item in existing_keys:
            if item.name == self._bootstrap_api_key_name and item.key_hash == wanted_hash and item.status == "active":
                return

        bootstrap_key = AccessApiKey(
            owner_user_id=self._bootstrap_user_id,
            name=self._bootstrap_api_key_name,
            key_prefix=self._bootstrap_api_key[:3] if len(self._bootstrap_api_key) >= 3 else "cd_",
            key_hash=wanted_hash,
            status="active",
            scopes=["*"],
            profile_ids=["*"],
        )
        self._repository.upsert_api_key(bootstrap_key, is_bootstrap=True)

    def _derive_flat_demo_keys(self) -> dict[str, str]:
        """Derive stable raw demo keys from the configured service API key."""
        seed = (self._bootstrap_api_key.strip() or "db-mcp-flat-demo-seed").encode("utf-8")
        keys: dict[str, str] = {}
        for _user_id, _username, _display_name, role in FLAT_DEMO_ROLES:
            digest = hmac.new(seed, role.encode("utf-8"), hashlib.sha256).hexdigest()
            keys[role] = f"flatk-db-mcp-{role}-{digest[:32]}"
        return keys

    def _seed_flat_demo_keys(self) -> None:
        """Seed the three flat-login demo users and API keys idempotently."""
        keys = self._derive_flat_demo_keys()
        for user_id, username, display_name, role in FLAT_DEMO_ROLES:
            user = self._repository.get_user(user_id)
            if user is None:
                user = AccessUser(
                    user_id=user_id,
                    username=username,
                    display_name=display_name,
                    email="",
                    roles=[role],
                    status="active",
                )
            else:
                user.username = username
                user.display_name = display_name
                user.roles = [role]
                user.status = "active"
                user.updated_at = utcnow()
            self._repository.upsert_user(user)

            raw_key = keys[role]
            demo_key = AccessApiKey(
                api_key_id=f"flat-demo-{role}",
                owner_user_id=user_id,
                name=f"flat-demo-{role}",
                key_prefix=raw_key[:12],
                key_hash=hash_api_key(raw_key),
                status="active",
                scopes=["*"],
                profile_ids=["*"],
            )
            self._repository.upsert_api_key(demo_key, is_bootstrap=True)

        self._write_flat_demo_key_files(keys)

    def _write_flat_demo_key_files(self, keys: dict[str, str]) -> None:
        """Write raw demo keys to an ignored runtime path for operators/tests."""
        keys_dir = str(self._config.get("flat_login.demo_keys_dir", "data/flat_role_keys") or "data/flat_role_keys")
        ensure_directory(keys_dir)
        for role, raw_key in keys.items():
            write_text_file(join_fs_path(keys_dir, f"{role}.key"), f"{raw_key}\n", mode=0o600)

    def _rebuild_rbac(self) -> None:
        self._rbac = RBACEngine(role_overlay=self._role_permissions)
        for user in self._repository.list_users():
            for role in user.roles:
                self._rbac.assign_role_to_user(user.user_id, role)
        for group in self._repository.list_groups():
            for member_id in group.member_user_ids:
                self._rbac.add_user_to_group(member_id, group.group_id)
            for role in group.roles:
                self._rbac.assign_role_to_group(group.group_id, role)

    # PS-50 per-tool RBAC permission mapping.
    _TOOL_PERMISSION_MAP = {
        "query": "db:query:execute",
        "schema_list": "db:schema:read",
        "schema_describe": "db:schema:read",
        "admin_stats": "db:admin:read",
        "connection_test": "db:admin:read",
    }

    def require_tool_permission(self, user_id: str, tool_name: str) -> bool:
        """PS-50 per-tool RBAC check."""
        perm = self._TOOL_PERMISSION_MAP.get(tool_name, "db:query:execute")
        return self._rbac.has_permission(user_id, perm)  # has_permission for tool dispatch

    def _build_actor(self, actor_user_id: str | None, roles: list[str] | None = None) -> Actor:
        return Actor(type="user", id=actor_user_id or "unknown", roles=roles or None)

    def _audit_crud(
        self,
        *,
        actor_user_id: str | None,
        actor_roles: list[str] | None,
        action: str,
        resource_type: str,
        resource_id: str,
        outcome: str,
        **details: Any,
    ) -> None:
        self._audit_logger.log_crud(
            actor=self._build_actor(actor_user_id, actor_roles),
            action=action,
            target=Target(type=resource_type, id=resource_id),
            outcome=outcome,
            **details,
        )

    def _audit_denial(
        self,
        *,
        actor_user_id: str | None,
        actor_roles: list[str] | None,
        permission: str,
        resource_type: str,
        resource_id: str,
        reason: str,
    ) -> None:
        self._audit_logger.log_security(
            actor=self._build_actor(actor_user_id, actor_roles),
            action="authorise",
            target=Target(type=resource_type, id=resource_id),
            outcome="denied",
            permission=permission,
            reason=reason,
        )

    def _validate_roles(self, roles: list[str]) -> list[str]:
        unknown = [role for role in roles if role not in ROLE_NAMES]
        if unknown:
            raise ValidationError(message=f"Unknown roles: {unknown}")
        return sorted(set(roles))

    def _validate_source_connection_name(self, name: str) -> str:
        value = str(name or "").strip()
        if not self._SOURCE_CONNECTION_NAME_RE.fullmatch(value):
            raise ValidationError(
                message="Source connection name must match ^[a-z0-9_-]{1,100}$"
            )
        return value

    def _validate_source_type(self, source_type: str) -> str:
        value = str(source_type or "").strip().lower()
        if value not in SOURCE_CONNECTION_TYPES:
            raise ValidationError(message=f"Unsupported source type: {source_type}")
        return value

    def _validate_source_status(self, status: str) -> str:
        value = str(status or "").strip().lower()
        if value not in SOURCE_CONNECTION_STATUSES:
            raise ValidationError(message=f"Unsupported source connection status: {status}")
        return value

    def _validate_saved_query_page_key(self, page_key: str) -> str:
        value = str(page_key or "").strip()
        if value not in SAVED_QUERY_PAGE_PERMISSIONS:
            raise ValidationError(message=f"Unsupported saved query page_key: {page_key}")
        return value

    @staticmethod
    def _validate_saved_query_name(name: str) -> str:
        value = str(name or "").strip()
        if not value or len(value) > 120:
            raise ValidationError(message="Saved query name must be 1-120 characters")
        return value

    @staticmethod
    def _validate_saved_query_payload(payload: Any) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise ValidationError(message="Saved query payload must be an object")
        return dict(payload)

    def _get_saved_query_record(self, query_id: int) -> SavedQuery:
        saved_query = self._repository.get_saved_query(int(query_id))
        if saved_query is None:
            raise NotFoundError(message=f"Saved query not found: {query_id}")
        return saved_query

    def _build_source_connection(self, payload: dict[str, Any]) -> SourceConnection:
        name = self._validate_source_connection_name(str(payload.get("name", "")))
        source_type = self._validate_source_type(str(payload.get("source_type", "")))
        uri_template = str(payload.get("uri_template", "") or "").strip()
        if not uri_template:
            raise ValidationError(message="Source connection uri_template is required")
        status = self._validate_source_status(str(payload.get("status", "not_tested")))
        last_tested_at = payload.get("last_tested_at")
        if last_tested_at is not None:
            last_tested_at = last_tested_at if hasattr(last_tested_at, "isoformat") else None
        return SourceConnection(
            name=name,
            source_type=source_type,
            uri_template=uri_template,
            credentials_ref=payload.get("credentials_ref"),
            description=str(payload.get("description", "") or ""),
            status=status,
            last_tested_at=last_tested_at,
            last_test_result=dict(payload.get("last_test_result", {}) or {}),
        )

    def list_source_connections(self) -> list[dict[str, Any]]:
        return [self._source_connection_view(item) for item in self._repository.list_source_connections()]

    def get_source_connection(self, name: str) -> dict[str, Any]:
        connection = self._repository.get_source_connection(self._validate_source_connection_name(name))
        if connection is None:
            raise NotFoundError(message=f"Source connection not found: {name}")
        return self._source_connection_view(connection)

    def get_discovery_cache(self, *, profile_id: str, cache_key: str) -> dict[str, Any] | None:
        return self._repository.get_discovery_cache(profile_id=profile_id, cache_key=cache_key)

    def upsert_discovery_cache(
        self,
        *,
        profile_id: str,
        cache_key: str,
        payload: list[dict[str, Any]],
        ttl_seconds: int,
    ) -> dict[str, Any]:
        return self._repository.upsert_discovery_cache(
            profile_id=profile_id,
            cache_key=cache_key,
            payload=payload,
            ttl_seconds=ttl_seconds,
        )

    def list_saved_queries(self, request: Request, *, page_key: str) -> list[dict[str, Any]]:
        page_key = self._validate_saved_query_page_key(page_key)
        principal = self.require_request_permission(
            request,
            permission=SAVED_QUERY_PAGE_PERMISSIONS[page_key],
            audit_resource_type="saved_query",
            audit_resource_id=f"list:{page_key}",
        )
        return [
            self._saved_query_view(item)
            for item in self._repository.list_saved_queries(
                user_id=principal.user_id,
                page_key=page_key,
            )
        ]

    def get_saved_query(self, request: Request, *, query_id: int) -> dict[str, Any]:
        current = self._get_saved_query_record(query_id)
        principal = self.require_request_permission(
            request,
            permission=SAVED_QUERY_PAGE_PERMISSIONS[current.page_key],
            audit_resource_type="saved_query",
            audit_resource_id=str(query_id),
        )
        if current.user_id != principal.user_id and not current.shared:
            raise UnauthorisedError(message=f"Saved query access denied: {query_id}")
        return self._saved_query_view(current)

    def create_saved_query(self, request: Request, payload: dict[str, Any]) -> dict[str, Any]:
        page_key = self._validate_saved_query_page_key(str(payload.get("page_key") or ""))
        principal = self.require_request_permission(
            request,
            permission=SAVED_QUERY_PAGE_PERMISSIONS[page_key],
            audit_resource_type="saved_query",
            audit_resource_id=f"create:{page_key}",
        )
        name = self._validate_saved_query_name(str(payload.get("name") or ""))
        if self._repository.get_saved_query_by_name(
            user_id=principal.user_id,
            page_key=page_key,
            name=name,
        ):
            raise ConflictError(message=f"Saved query already exists: {page_key}/{name}")
        saved = self._repository.create_saved_query(
            SavedQuery(
                user_id=principal.user_id,
                page_key=page_key,
                name=name,
                description=str(payload.get("description") or ""),
                payload=self._validate_saved_query_payload(payload.get("payload")),
                shared=bool(payload.get("shared", False)),
            )
        )
        self._audit_crud(
            actor_user_id=principal.user_id,
            actor_roles=principal.roles,
            action="create",
            resource_type="saved_query",
            resource_id=str(saved.id),
            outcome="success",
            page_key=page_key,
        )
        return self._saved_query_view(saved)

    def update_saved_query(self, request: Request, *, query_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        current = self._get_saved_query_record(query_id)
        principal = self.require_request_permission(
            request,
            permission=SAVED_QUERY_PAGE_PERMISSIONS[current.page_key],
            audit_resource_type="saved_query",
            audit_resource_id=str(query_id),
        )
        if current.user_id != principal.user_id:
            raise UnauthorisedError(message=f"Saved query update denied: {query_id}")
        next_name = current.name
        if payload.get("name") is not None:
            next_name = self._validate_saved_query_name(str(payload.get("name") or ""))
            same_name = self._repository.get_saved_query_by_name(
                user_id=principal.user_id,
                page_key=current.page_key,
                name=next_name,
            )
            if same_name and same_name.id != current.id:
                raise ConflictError(message=f"Saved query already exists: {current.page_key}/{next_name}")
        updated = SavedQuery(
            id=current.id,
            user_id=current.user_id,
            page_key=current.page_key,
            name=next_name,
            description=(
                str(payload.get("description") or "")
                if payload.get("description") is not None
                else current.description
            ),
            payload=(
                self._validate_saved_query_payload(payload.get("payload"))
                if payload.get("payload") is not None
                else current.payload
            ),
            shared=bool(payload.get("shared")) if payload.get("shared") is not None else current.shared,
            created_at=current.created_at,
            updated_at=utcnow(),
        )
        saved = self._repository.update_saved_query(updated)
        self._audit_crud(
            actor_user_id=principal.user_id,
            actor_roles=principal.roles,
            action="update",
            resource_type="saved_query",
            resource_id=str(saved.id),
            outcome="success",
            page_key=saved.page_key,
        )
        return self._saved_query_view(saved)

    def delete_saved_query(self, request: Request, *, query_id: int) -> bool:
        current = self._get_saved_query_record(query_id)
        principal = self.require_request_permission(
            request,
            permission=SAVED_QUERY_PAGE_PERMISSIONS[current.page_key],
            audit_resource_type="saved_query",
            audit_resource_id=str(query_id),
        )
        if current.user_id != principal.user_id:
            raise UnauthorisedError(message=f"Saved query delete denied: {query_id}")
        deleted = self._repository.delete_saved_query(query_id)
        if not deleted:
            raise NotFoundError(message=f"Saved query not found: {query_id}")
        self._audit_crud(
            actor_user_id=principal.user_id,
            actor_roles=principal.roles,
            action="delete",
            resource_type="saved_query",
            resource_id=str(query_id),
            outcome="success",
            page_key=current.page_key,
        )
        return True

    def create_source_connection(
        self,
        payload: dict[str, Any],
        *,
        actor_user_id: str | None,
        actor_roles: list[str] | None,
    ) -> dict[str, Any]:
        source_connection = self._build_source_connection(payload)
        if self._repository.get_source_connection(source_connection.name) is not None:
            raise ConflictError(message=f"Source connection already exists: {source_connection.name}")
        saved = self._repository.upsert_source_connection(source_connection)
        self._audit_crud(
            actor_user_id=actor_user_id,
            actor_roles=actor_roles,
            action="create",
            resource_type="source_connection",
            resource_id=saved.name,
            outcome="success",
            source_type=saved.source_type,
        )
        return self._source_connection_view(saved)

    def update_source_connection(
        self,
        name: str,
        payload: dict[str, Any],
        *,
        actor_user_id: str | None,
        actor_roles: list[str] | None,
    ) -> dict[str, Any]:
        source_name = self._validate_source_connection_name(name)
        current = self._repository.get_source_connection(source_name)
        if current is None:
            raise NotFoundError(message=f"Source connection not found: {name}")
        uri_template = str(payload.get("uri_template", "") or "").strip()
        if not uri_template:
            raise ValidationError(message="Source connection uri_template is required")
        updated = SourceConnection(
            name=current.name,
            source_type=current.source_type,
            uri_template=uri_template,
            credentials_ref=payload.get("credentials_ref"),
            description=str(payload.get("description", "") or ""),
            status=current.status,
            last_tested_at=current.last_tested_at,
            last_test_result=current.last_test_result,
            created_at=current.created_at,
            updated_at=utcnow(),
        )
        saved = self._repository.upsert_source_connection(updated)
        self._audit_crud(
            actor_user_id=actor_user_id,
            actor_roles=actor_roles,
            action="update",
            resource_type="source_connection",
            resource_id=saved.name,
            outcome="success",
            source_type=saved.source_type,
        )
        return self._source_connection_view(saved)

    def delete_source_connection(
        self,
        name: str,
        *,
        actor_user_id: str | None,
        actor_roles: list[str] | None,
    ) -> bool:
        source_name = self._validate_source_connection_name(name)
        current = self._repository.get_source_connection(source_name)
        if current is None:
            raise NotFoundError(message=f"Source connection not found: {name}")
        reference_count = self._repository.count_profiles_using_source_connection(source_name)
        if reference_count:
            noun = "profile" if reference_count == 1 else "profiles"
            raise ConflictError(
                message=(
                    f"Cannot delete source connection {source_name}: "
                    f"unbind {reference_count} {noun} first"
                ),
                details={"profiles_referencing": reference_count},
            )
        deleted = self._repository.delete_source_connection(source_name)
        if not deleted:
            raise NotFoundError(message=f"Source connection not found: {name}")
        self._audit_crud(
            actor_user_id=actor_user_id,
            actor_roles=actor_roles,
            action="delete",
            resource_type="source_connection",
            resource_id=source_name,
            outcome="success",
        )
        return True

    def test_source_connection(
        self,
        name: str,
        *,
        actor_user_id: str | None,
        actor_roles: list[str] | None,
    ) -> dict[str, Any]:
        source_name = self._validate_source_connection_name(name)
        current = self._repository.get_source_connection(source_name)
        if current is None:
            raise NotFoundError(message=f"Source connection not found: {name}")
        result = self._run_source_connection_test(current)
        current.status = "healthy" if result["ok"] else "failing"
        current.last_tested_at = utcnow()
        current.last_test_result = result
        current.updated_at = utcnow()
        saved = self._repository.upsert_source_connection(current)
        self._audit_crud(
            actor_user_id=actor_user_id,
            actor_roles=actor_roles,
            action="test",
            resource_type="source_connection",
            resource_id=source_name,
            outcome="success" if result["ok"] else "failure",
        )
        return self._source_connection_view(saved)

    def test_source_connection_draft(self, payload: dict[str, Any]) -> dict[str, Any]:
        draft = self._build_source_connection(
            {
                **payload,
                "name": "__draft__",
            }
        )
        return self._run_source_connection_test(draft)

    def _run_source_connection_test(self, source_connection: SourceConnection) -> dict[str, Any]:
        started = time.perf_counter()
        if "${" in source_connection.uri_template:
            return {
                "ok": False,
                "latency_ms": 0,
                "error": "Cannot test source connection with unresolved template placeholders",
            }
        if self._connector_manager is None:
            return {
                "ok": False,
                "latency_ms": 0,
                "error": "Connector manager is not initialised",
            }
        try:
            capability = self._connector_manager.test_source_connection(
                source_connection.source_type,
                source_connection.uri_template,
            )
        except Exception as exc:
            return {
                "ok": False,
                "latency_ms": int((time.perf_counter() - started) * 1000),
                "error": str(exc),
            }
        return {
            "ok": True,
            "latency_ms": int((time.perf_counter() - started) * 1000),
            "capability": capability,
        }

    def list_profiles(self) -> list[dict[str, Any]]:
        return [self._profile_view(item) for item in self._repository.list_profiles()]

    def get_profile(self, profile_id: str) -> dict[str, Any]:
        profile = self._repository.get_profile(profile_id)
        if profile is None:
            raise NotFoundError(message=f"Profile not found: {profile_id}")
        return self._profile_view(profile)

    def get_profile_internal(self, profile_id: str) -> dict[str, Any]:
        """Return an internal profile payload with connection secrets intact."""
        profile = self._repository.get_profile(profile_id)
        if profile is None:
            raise NotFoundError(message=f"Profile not found: {profile_id}")
        return self._profile_payload(profile)

    def test_profile_scope(self, request: Request, *, profile_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        principal = self.require_request_permission(
            request,
            permission="profile.manage",
            profile_id=profile_id,
            audit_resource_type="profile",
            audit_resource_id=profile_id,
        )
        current = self._repository.get_profile(profile_id)
        if current is None:
            raise NotFoundError(message=f"Profile not found: {profile_id}")
        profile_payload = self._profile_view(current)
        profile_payload.update(dict(payload.get("profile") or {}))
        profile_payload["profile_id"] = profile_id
        ensure_known_permissions(list(profile_payload.get("allowed_permissions", [])))
        if self._connector_manager is None:
            return {
                "ok": False,
                "profile_id": profile_id,
                "error": "Connector manager is not initialised",
            }
        started = time.perf_counter()
        session = None
        try:
            session = self._connector_manager.for_profile_payload(profile_payload)
            namespaces = self._connector_manager.filter_namespaces(
                session.profile,
                session.connector.list_namespaces(),
            )
            entities_by_namespace: dict[str, list[dict[str, Any]]] = {}
            for namespace_item in namespaces:
                namespace = str(namespace_item.get("name", ""))
                entities_by_namespace[namespace] = self._connector_manager.filter_entities(
                    session.profile,
                    namespace,
                    session.connector.list_entities(namespace),
                )
            result = {
                "ok": True,
                "profile_id": profile_id,
                "latency_ms": int((time.perf_counter() - started) * 1000),
                "namespace_count": len(namespaces),
                "entity_count": sum(len(items) for items in entities_by_namespace.values()),
                "namespaces": namespaces,
                "entities_by_namespace": entities_by_namespace,
            }
        except Exception as exc:
            result = {
                "ok": False,
                "profile_id": profile_id,
                "latency_ms": int((time.perf_counter() - started) * 1000),
                "error": str(exc),
            }
        finally:
            if session is not None:
                close = getattr(session.connector, "close", None)
                if callable(close):
                    close()
        self._audit_crud(
            actor_user_id=principal.user_id,
            actor_roles=principal.roles,
            action="test_scope",
            resource_type="profile",
            resource_id=profile_id,
            outcome="success" if result["ok"] else "failure",
        )
        return result

    def create_profile(self, payload: dict[str, Any], *, actor_user_id: str | None, actor_roles: list[str] | None) -> dict[str, Any]:
        ensure_known_permissions(list(payload.get("allowed_permissions", [])))
        profile = Profile(**payload)
        saved = self._repository.upsert_profile(profile)
        self._audit_crud(
            actor_user_id=actor_user_id,
            actor_roles=actor_roles,
            action="create",
            resource_type="profile",
            resource_id=saved.profile_id,
            outcome="success",
            profile_name=saved.name,
        )
        return self._profile_view(saved)

    def update_profile(self, profile_id: str, payload: dict[str, Any], *, actor_user_id: str | None, actor_roles: list[str] | None) -> dict[str, Any]:
        current = self._repository.get_profile(profile_id)
        if current is None:
            raise NotFoundError(message=f"Profile not found: {profile_id}")
        ensure_known_permissions(list(payload.get("allowed_permissions", [])))
        updated = Profile(profile_id=profile_id, created_at=current.created_at, updated_at=utcnow(), **payload)
        self._repository.upsert_profile(updated)
        self._audit_crud(
            actor_user_id=actor_user_id,
            actor_roles=actor_roles,
            action="update",
            resource_type="profile",
            resource_id=profile_id,
            outcome="success",
            profile_name=updated.name,
        )
        return self._profile_view(updated)

    def delete_profile(self, profile_id: str, *, actor_user_id: str | None, actor_roles: list[str] | None) -> bool:
        deleted = self._repository.delete_profile(profile_id)
        if not deleted:
            raise NotFoundError(message=f"Profile not found: {profile_id}")
        self._audit_crud(
            actor_user_id=actor_user_id,
            actor_roles=actor_roles,
            action="delete",
            resource_type="profile",
            resource_id=profile_id,
            outcome="success",
        )
        return True

    def apply_profile_mask(self, profile_id: str, record: dict[str, Any]) -> dict[str, Any]:
        profile = self._repository.get_profile(profile_id)
        if profile is None:
            raise NotFoundError(message=f"Profile not found: {profile_id}")
        masked = dict(record)
        for field_name in profile.field_exclusions:
            masked.pop(field_name, None)
        for field_name, mask in profile.field_masks.items():
            if field_name in masked:
                masked[field_name] = mask
        return masked

    def list_users(self) -> list[dict[str, Any]]:
        return [self._user_view(item) for item in self._repository.list_users()]

    def get_user(self, user_id: str) -> dict[str, Any]:
        user = self._repository.get_user(user_id)
        if user is None:
            raise NotFoundError(message=f"User not found: {user_id}")
        return self._user_view(user)

    def create_user(self, payload: dict[str, Any], *, actor_user_id: str | None, actor_roles: list[str] | None) -> dict[str, Any]:
        roles = self._validate_roles(list(payload.get("roles", [])))
        user = AccessUser(**{**payload, "roles": roles})
        saved = self._repository.upsert_user(user)
        self._rebuild_rbac()
        self._audit_crud(
            actor_user_id=actor_user_id,
            actor_roles=actor_roles,
            action="create",
            resource_type="user",
            resource_id=saved.user_id,
            outcome="success",
            username=saved.username,
        )
        return self._user_view(saved)

    def update_user(self, user_id: str, payload: dict[str, Any], *, actor_user_id: str | None, actor_roles: list[str] | None) -> dict[str, Any]:
        current = self._repository.get_user(user_id)
        if current is None:
            raise NotFoundError(message=f"User not found: {user_id}")
        roles = self._validate_roles(list(payload.get("roles", [])))
        updated = AccessUser(user_id=user_id, created_at=current.created_at, updated_at=utcnow(), **{**payload, "roles": roles})
        saved = self._repository.upsert_user(updated)
        self._rebuild_rbac()
        self._audit_crud(
            actor_user_id=actor_user_id,
            actor_roles=actor_roles,
            action="update",
            resource_type="user",
            resource_id=user_id,
            outcome="success",
            username=saved.username,
        )
        return self._user_view(saved)

    def delete_user(self, user_id: str, *, actor_user_id: str | None, actor_roles: list[str] | None) -> bool:
        if user_id == self._bootstrap_user_id:
            raise ValidationError(message="Bootstrap admin cannot be deleted")
        deleted = self._repository.delete_user(user_id)
        if not deleted:
            raise NotFoundError(message=f"User not found: {user_id}")
        self._rebuild_rbac()
        self._audit_crud(
            actor_user_id=actor_user_id,
            actor_roles=actor_roles,
            action="delete",
            resource_type="user",
            resource_id=user_id,
            outcome="success",
        )
        return True

    def list_groups(self) -> list[dict[str, Any]]:
        return [self._group_view(item) for item in self._repository.list_groups()]

    def get_group(self, group_id: str) -> dict[str, Any]:
        group = self._repository.get_group(group_id)
        if group is None:
            raise NotFoundError(message=f"Group not found: {group_id}")
        return self._group_view(group)

    def create_group(self, payload: dict[str, Any], *, actor_user_id: str | None, actor_roles: list[str] | None) -> dict[str, Any]:
        roles = self._validate_roles(list(payload.get("roles", [])))
        for user_id in payload.get("member_user_ids", []):
            if self._repository.get_user(user_id) is None:
                raise ValidationError(message=f"Unknown member user: {user_id}")
        group = AccessGroup(**{**payload, "roles": roles})
        saved = self._repository.upsert_group(group)
        self._rebuild_rbac()
        self._audit_crud(
            actor_user_id=actor_user_id,
            actor_roles=actor_roles,
            action="create",
            resource_type="group",
            resource_id=saved.group_id,
            outcome="success",
            group_name=saved.name,
        )
        return self._group_view(saved)

    def update_group(self, group_id: str, payload: dict[str, Any], *, actor_user_id: str | None, actor_roles: list[str] | None) -> dict[str, Any]:
        current = self._repository.get_group(group_id)
        if current is None:
            raise NotFoundError(message=f"Group not found: {group_id}")
        roles = self._validate_roles(list(payload.get("roles", [])))
        for user_id in payload.get("member_user_ids", []):
            if self._repository.get_user(user_id) is None:
                raise ValidationError(message=f"Unknown member user: {user_id}")
        updated = AccessGroup(group_id=group_id, created_at=current.created_at, updated_at=utcnow(), **{**payload, "roles": roles})
        saved = self._repository.upsert_group(updated)
        self._rebuild_rbac()
        self._audit_crud(
            actor_user_id=actor_user_id,
            actor_roles=actor_roles,
            action="update",
            resource_type="group",
            resource_id=saved.group_id,
            outcome="success",
            group_name=saved.name,
        )
        return self._group_view(saved)

    def delete_group(self, group_id: str, *, actor_user_id: str | None, actor_roles: list[str] | None) -> bool:
        deleted = self._repository.delete_group(group_id)
        if not deleted:
            raise NotFoundError(message=f"Group not found: {group_id}")
        self._rebuild_rbac()
        self._audit_crud(
            actor_user_id=actor_user_id,
            actor_roles=actor_roles,
            action="delete",
            resource_type="group",
            resource_id=group_id,
            outcome="success",
        )
        return True

    def create_api_key(self, payload: dict[str, Any], *, actor_user_id: str | None, actor_roles: list[str] | None) -> dict[str, Any]:
        owner_user_id = str(payload.get("owner_user_id", ""))
        owner = self._repository.get_user(owner_user_id)
        if owner is None:
            raise ValidationError(message=f"Unknown owner user: {owner_user_id}")
        scopes = ensure_known_permissions(list(payload.get("scopes", [])))
        profile_ids = list(payload.get("profile_ids", []))
        for profile_id in [item for item in profile_ids if item != "*"]:
            if self._repository.get_profile(profile_id) is None:
                raise ValidationError(message=f"Unknown profile: {profile_id}")
        raw_key = f"cd_{secrets.token_urlsafe(32)}"
        ttl_days = payload.get("ttl_days")
        expires_at = utcnow() + timedelta(days=int(ttl_days)) if ttl_days else None
        api_key = AccessApiKey(
            owner_user_id=owner_user_id,
            name=str(payload.get("name", "")),
            key_prefix="cd_",
            key_hash=hash_api_key(raw_key),
            status="active",
            scopes=scopes or ["*"],
            profile_ids=profile_ids or ["*"],
            expires_at=expires_at,
        )
        saved = self._repository.upsert_api_key(api_key)
        self._audit_crud(
            actor_user_id=actor_user_id,
            actor_roles=actor_roles,
            action="create",
            resource_type="api_key",
            resource_id=saved.api_key_id,
            outcome="success",
            owner_user_id=owner_user_id,
            name=saved.name,
        )
        return {**self._api_key_view(saved), "raw_key": raw_key}

    def list_api_keys(self, owner_user_id: str | None = None) -> list[dict[str, Any]]:
        return [self._api_key_view(item) for item in self._repository.list_api_keys(owner_user_id)]

    def revoke_api_key(self, api_key_id: str, *, actor_user_id: str | None, actor_roles: list[str] | None, reason: str = "revoked") -> bool:
        item = self._repository.get_api_key(api_key_id)
        if item is None:
            raise NotFoundError(message=f"API key not found: {api_key_id}")
        item.status = "revoked"
        item.revoked_at = utcnow()
        self._repository.revoke_api_key(api_key_id, self._repository.serialise_api_key(item))
        self._audit_crud(
            actor_user_id=actor_user_id,
            actor_roles=actor_roles,
            action="revoke",
            resource_type="api_key",
            resource_id=api_key_id,
            outcome="success",
            reason=reason,
        )
        return True

    # ----- Roles (PS-71 §IW3A; canonical cloud_dog_idam role store) -----------
    def ensure_roles_seed(self) -> None:
        """Idempotently seed the baseline admin/user roles (IW3A.4)."""
        with self._role_session_factory() as session:
            SqlAlchemyRoleStore(session).seed_baseline()

    def list_roles(self) -> list[dict[str, Any]]:
        """Return roles in the PS-71 §IW3A.1 column shape (seeds baseline first)."""
        with self._role_session_factory() as session:
            store = SqlAlchemyRoleStore(session)
            store.seed_baseline()
            return store.list_response()

    def get_role(self, role_id: str) -> dict[str, Any]:
        with self._role_session_factory() as session:
            for row in SqlAlchemyRoleStore(session).list_response():
                if row["role_id"] == role_id:
                    return row
        raise NotFoundError(message=f"Role not found: {role_id}")

    def create_role(
        self,
        payload: dict[str, Any],
        *,
        actor_user_id: str | None,
        actor_roles: list[str] | None,
    ) -> dict[str, Any]:
        clean_name = str(payload.get("name", "") or "").strip()
        if not clean_name:
            raise ValidationError(message="Role name is required")
        permissions = {
            str(p).strip() for p in (payload.get("permissions") or []) if str(p).strip()
        }
        with self._role_session_factory() as session:
            store = SqlAlchemyRoleStore(session)
            if store.get_by_name(clean_name) is not None:
                raise ConflictError(message=f"Role already exists: {clean_name}")
            role = store.save(
                Role(
                    name=clean_name,
                    description=str(payload.get("description", "") or ""),
                    permissions=permissions,
                )
            )
            result = {
                "role_id": role.role_id,
                "name": role.name,
                "description": role.description,
                "permissions": sorted(role.permissions),
            }
        self._audit_crud(
            actor_user_id=actor_user_id,
            actor_roles=actor_roles,
            action="create",
            resource_type="role",
            resource_id=result["role_id"],
            outcome="success",
            role_name=result["name"],
        )
        return result

    def update_role(
        self,
        role_id: str,
        payload: dict[str, Any],
        *,
        actor_user_id: str | None,
        actor_roles: list[str] | None,
    ) -> dict[str, Any]:
        raw_perms = payload.get("permissions")
        permissions = (
            {str(p).strip() for p in raw_perms if str(p).strip()}
            if raw_perms is not None
            else None
        )
        with self._role_session_factory() as session:
            store = SqlAlchemyRoleStore(session)
            if store.get(role_id) is None:
                raise NotFoundError(message=f"Role not found: {role_id}")
            role = store.update(
                role_id,
                description=payload.get("description"),
                permissions=permissions,
            )
            result = {
                "role_id": role.role_id,
                "name": role.name,
                "description": role.description,
                "permissions": sorted(role.permissions),
            }
        self._audit_crud(
            actor_user_id=actor_user_id,
            actor_roles=actor_roles,
            action="update",
            resource_type="role",
            resource_id=result["role_id"],
            outcome="success",
            role_name=result["name"],
        )
        return result

    def delete_role(
        self,
        role_id: str,
        *,
        actor_user_id: str | None,
        actor_roles: list[str] | None,
    ) -> bool:
        with self._role_session_factory() as session:
            store = SqlAlchemyRoleStore(session)
            try:
                removed = store.delete(role_id)
            except BaselineRoleProtected as exc:
                raise UnauthorisedError(
                    message=f"Baseline role cannot be deleted: {exc}"
                )
            if not removed:
                raise NotFoundError(message=f"Role not found: {role_id}")
        self._audit_crud(
            actor_user_id=actor_user_id,
            actor_roles=actor_roles,
            action="delete",
            resource_type="role",
            resource_id=role_id,
            outcome="success",
        )
        return True

    def verify_api_key(self, raw_key: str) -> PrincipalContext | None:
        if not raw_key:
            return None
        matched_key = None
        for item in self._repository.list_api_keys():
            if item.status != "active":
                continue
            if item.expires_at is not None and item.expires_at <= utcnow():
                continue
            if key_matches(raw_key, item.key_hash):
                matched_key = item
                break
        if matched_key is None:
            return None

        user = self._repository.get_user(matched_key.owner_user_id)
        if user is None or user.status.lower() != "active":
            return None
        self._rebuild_rbac()
        roles = sorted(self._rbac.get_effective_roles(user.user_id))
        permissions = set(self._rbac.get_effective_permissions(user.user_id))
        scopes = set(matched_key.scopes or ["*"])
        if "*" not in scopes:
            permissions = permissions.intersection(scopes)
        return PrincipalContext(
            user_id=user.user_id,
            username=user.username,
            roles=roles,
            permissions=sorted(permissions),
            api_key_id=matched_key.api_key_id,
            profile_ids=matched_key.profile_ids or ["*"],
            scopes=matched_key.scopes or ["*"],
            tenant_id=user.tenant_id,
        )

    def principal_for_username(self, username: str) -> PrincipalContext | None:
        """Resolve a forwarded (web-trusted) username to its OWN RBAC principal.

        W28A-889-B-R2 / W28A-890: the web tier authenticates the trusted web
        origin with the service api-key (transport trust only) and forwards
        ``X-Request-User``. Authorization MUST be the forwarded user's own RBAC,
        never the service/bootstrap-admin principal — otherwise every web session
        collapses to service-admin. Returns ``None`` for unknown/inactive users so
        the caller denies (401).
        """
        if not username:
            return None
        user = self._repository.get_user_by_username(username)
        if user is None or str(getattr(user, "status", "")).lower() != "active":
            return None
        self._rebuild_rbac()
        roles = sorted(self._rbac.get_effective_roles(user.user_id))
        permissions = sorted(self._rbac.get_effective_permissions(user.user_id))
        return PrincipalContext(
            user_id=user.user_id,
            username=user.username,
            roles=roles,
            permissions=permissions,
            api_key_id="",
            profile_ids=["*"],
            scopes=["*"],
            tenant_id=user.tenant_id,
        )

    def principal_summary(self, principal: PrincipalContext) -> dict[str, Any]:
        """Return a JSON-safe summary of the authenticated principal."""
        return {
            "user_id": principal.user_id,
            "username": principal.username,
            "displayName": principal.username,
            "roles": principal.roles,
            "permissions": principal.permissions,
            "api_key_id": principal.api_key_id,
            "profile_ids": principal.profile_ids,
            "scopes": principal.scopes,
            "tenant_id": principal.tenant_id,
        }

    def ensure_permission(
        self,
        principal: PrincipalContext,
        *,
        permission: str,
        profile_id: str | None = None,
        audit_resource_type: str,
        audit_resource_id: str,
    ) -> None:
        if permission not in PERMISSION_DOMAINS and permission != "*":
            raise ValidationError(message=f"Unknown permission: {permission}")
        if "*" not in principal.permissions and permission not in principal.permissions:
            self._audit_denial(
                actor_user_id=principal.user_id,
                actor_roles=principal.roles,
                permission=permission,
                resource_type=audit_resource_type,
                resource_id=audit_resource_id,
                reason="rbac",
            )
            raise UnauthorisedError(message=f"Missing required permission: {permission}")
        if profile_id is not None:
            if "*" not in principal.profile_ids and profile_id not in principal.profile_ids:
                self._audit_denial(
                    actor_user_id=principal.user_id,
                    actor_roles=principal.roles,
                    permission=permission,
                    resource_type=audit_resource_type,
                    resource_id=audit_resource_id,
                    reason="api_key_profile_scope",
                )
                raise UnauthorisedError(message=f"Profile access denied: {profile_id}")
            profile = self._repository.get_profile(profile_id)
            if profile is None:
                raise NotFoundError(message=f"Profile not found: {profile_id}")
            profile_permissions = set(profile.allowed_permissions or [])
            if "*" not in profile_permissions and permission not in profile_permissions:
                self._audit_denial(
                    actor_user_id=principal.user_id,
                    actor_roles=principal.roles,
                    permission=permission,
                    resource_type=audit_resource_type,
                    resource_id=audit_resource_id,
                    reason="profile_scope",
                )
                raise UnauthorisedError(message=f"Profile does not permit action: {permission}")

    def require_request_permission(
        self,
        request: Request,
        *,
        permission: str,
        profile_id: str | None = None,
        audit_resource_type: str,
        audit_resource_id: str,
    ) -> PrincipalContext:
        principal = self.principal_from_request(request)
        self.ensure_permission(
            principal,
            permission=permission,
            profile_id=profile_id,
            audit_resource_type=audit_resource_type,
            audit_resource_id=audit_resource_id,
        )
        return principal

    def principal_from_request(self, request: Request) -> PrincipalContext:
        principal = getattr(request.state, "principal", None)
        if principal is None:
            raise UnauthorisedError(message="No authenticated principal")
        return principal

    def profile_access_summary(self, principal: PrincipalContext, profile_id: str, permission: str) -> dict[str, Any]:
        self.ensure_permission(
            principal,
            permission=permission,
            profile_id=profile_id,
            audit_resource_type="profile",
            audit_resource_id=profile_id,
        )
        profile = self._repository.get_profile(profile_id)
        assert profile is not None
        return {
            "authorised": True,
            "profile": self._profile_view(profile),
            "permission": permission,
            "principal": {
                "user_id": principal.user_id,
                "username": principal.username,
                "roles": principal.roles,
                "permissions": principal.permissions,
            },
        }

    def _profile_view(self, profile: Profile) -> dict[str, Any]:
        payload = self._profile_payload(profile)
        # W28A-889-B-R2 / W28A-890: never expose the DB-connection password on read.
        if payload.get("source_connection"):
            payload["source_connection"] = _mask_connection_secret(payload["source_connection"])
        return payload

    @staticmethod
    def _profile_payload(profile: Profile) -> dict[str, Any]:
        payload = asdict(profile)
        payload["created_at"] = profile.created_at.isoformat()
        payload["updated_at"] = profile.updated_at.isoformat()
        return payload

    def _source_connection_view(self, source_connection: SourceConnection) -> dict[str, Any]:
        payload = asdict(source_connection)
        payload["created_at"] = source_connection.created_at.isoformat()
        payload["updated_at"] = source_connection.updated_at.isoformat()
        payload["last_tested_at"] = (
            source_connection.last_tested_at.isoformat()
            if source_connection.last_tested_at
            else None
        )
        return payload

    def _saved_query_view(self, saved_query: SavedQuery) -> dict[str, Any]:
        payload = asdict(saved_query)
        payload["created_at"] = saved_query.created_at.isoformat()
        payload["updated_at"] = saved_query.updated_at.isoformat()
        return payload

    def _user_view(self, user: AccessUser) -> dict[str, Any]:
        payload = asdict(user)
        payload["created_at"] = user.created_at.isoformat()
        payload["updated_at"] = user.updated_at.isoformat()
        payload["effective_roles"] = sorted(self._rbac.get_effective_roles(user.user_id)) if self._repository.get_user(user.user_id) else user.roles
        payload["effective_permissions"] = sorted(self._rbac.get_effective_permissions(user.user_id)) if self._repository.get_user(user.user_id) else []
        return payload

    def _group_view(self, group: AccessGroup) -> dict[str, Any]:
        payload = asdict(group)
        payload["created_at"] = group.created_at.isoformat()
        payload["updated_at"] = group.updated_at.isoformat()
        # Surface member_count so the IDAM Groups page shows a real count rather
        # than 0 for a populated group (W28A-889-B-R2).
        payload["member_count"] = len(group.member_user_ids)
        return payload

    def _api_key_view(self, api_key: AccessApiKey) -> dict[str, Any]:
        return {
            "api_key_id": api_key.api_key_id,
            # Alias the canonical identifiers under the keys the shared IDAM
            # API-Keys page reads (id / user_id) so the owner column resolves to
            # the real owner instead of rendering "undefined" (W28A-889-B-R2).
            "id": api_key.api_key_id,
            "user_id": api_key.owner_user_id,
            "owner_user_id": api_key.owner_user_id,
            "name": api_key.name,
            "key_prefix": api_key.key_prefix,
            "status": api_key.status,
            "scopes": api_key.scopes,
            "profile_ids": api_key.profile_ids,
            "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None,
            "created_at": api_key.created_at.isoformat(),
            "revoked_at": api_key.revoked_at.isoformat() if api_key.revoked_at else None,
        }
