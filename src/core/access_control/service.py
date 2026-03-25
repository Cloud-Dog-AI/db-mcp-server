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

import secrets
from dataclasses import asdict, dataclass
from datetime import timedelta
from typing import Any

from fastapi import Request
from sqlalchemy import Engine

from cloud_dog_api_kit.errors import NotFoundError, UnauthorisedError, ValidationError
from cloud_dog_idam.api_keys.hashing import hash_api_key, key_matches
from cloud_dog_idam import RBACEngine
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
    ensure_known_permissions,
    utcnow,
)
from src.core.access_control.repository import AccessControlRepository


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

    def __init__(self, *, config: Any, engine: Engine, audit_logger: AuditLogger) -> None:
        self._config = config
        self._repository = AccessControlRepository(engine)
        self._audit_logger = audit_logger
        configured_permissions = config.get("access_control.roles", {}) or {}
        role_permissions = {
            role: set(values)
            for role, values in configured_permissions.items()
        } or DEFAULT_ROLE_PERMISSIONS
        self._role_permissions = role_permissions
        self._rbac = RBACEngine(role_permissions=self._role_permissions)
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

    def _rebuild_rbac(self) -> None:
        self._rbac = RBACEngine(role_permissions=self._role_permissions)
        for user in self._repository.list_users():
            for role in user.roles:
                self._rbac.assign_role_to_user(user.user_id, role)
        for group in self._repository.list_groups():
            for member_id in group.member_user_ids:
                self._rbac.add_user_to_group(member_id, group.group_id)
            for role in group.roles:
                self._rbac.assign_role_to_group(group.group_id, role)

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

    def list_profiles(self) -> list[dict[str, Any]]:
        return [self._profile_view(item) for item in self._repository.list_profiles()]

    def get_profile(self, profile_id: str) -> dict[str, Any]:
        profile = self._repository.get_profile(profile_id)
        if profile is None:
            raise NotFoundError(message=f"Profile not found: {profile_id}")
        return self._profile_view(profile)

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
        payload = asdict(profile)
        payload["created_at"] = profile.created_at.isoformat()
        payload["updated_at"] = profile.updated_at.isoformat()
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
        return payload

    def _api_key_view(self, api_key: AccessApiKey) -> dict[str, Any]:
        return {
            "api_key_id": api_key.api_key_id,
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
