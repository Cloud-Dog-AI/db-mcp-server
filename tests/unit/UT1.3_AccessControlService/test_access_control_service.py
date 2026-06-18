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
# Description: Unit tests for profile masking, RBAC, and API-key scoping.
# Related requirements: AC-01, AC-03
# Related tests: UT1.3

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import create_engine

from cloud_dog_logging import setup_logging, get_audit_logger

from src.common.config_loader import load_runtime_config
from src.core.access_control.service import AccessControlService

pytestmark = pytest.mark.unit


@pytest.fixture()
def access_control(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> AccessControlService:
    """Create an isolated access-control service bound to a temp SQLite store."""
    monkeypatch.setenv("CLOUD_DOG__FLAT_LOGIN__DEMO_KEYS_DIR", str(tmp_path / "flat_role_keys"))
    setup_logging(
        {
            "service_name": "db-mcp-server",
            "service_instance": "ut-access-control",
            "environment": "test",
            "log": {"console": False, "audit_log": str(tmp_path / "audit.log.jsonl")},
        }
    )
    config = load_runtime_config(["tests/env-UT"])
    engine = create_engine(f"sqlite:///{tmp_path / 'metadata.db'}")
    return AccessControlService(config=config, engine=engine, audit_logger=get_audit_logger())


def _demo_key(tmp_path: Path, role: str) -> str:
    return (tmp_path / "flat_role_keys" / f"{role}.key").read_text(encoding="utf-8").strip()
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-003")


def test_profile_masking_enforces_exclusions_and_masks(access_control: AccessControlService) -> None:
    """Profile field policy should mask configured fields and exclude hidden fields."""
    profile = access_control.create_profile(
        {
            "name": "finance-profile",
            "source_type": "mongodb",
            "source_connection": "mongo0",
            "allowed_permissions": ["data.read"],
            "field_masks": {"salary": "***MASKED***"},
            "field_exclusions": ["ssn"],
        },
        actor_user_id="bootstrap-admin",
        actor_roles=["admin"],
    )

    masked = access_control.apply_profile_mask(
        profile["profile_id"],
        {"salary": 100000, "ssn": "123-45-6789", "department": "ops"},
    )

    assert masked == {"salary": "***MASKED***", "department": "ops"}
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-003")


def test_internal_profile_lookup_preserves_connection_secret(access_control: AccessControlService) -> None:
    """Internal connector resolution needs the real DB credential, unlike API views."""
    created = access_control.create_profile(
        {
            "name": "finance-profile",
            "source_type": "mongodb",
            "source_connection": "mongodb://admin:mongo-test-p4ssw0rd@mongo0.example.net:27017/db?authSource=admin",
            "allowed_permissions": ["data.read"],
        },
        actor_user_id="bootstrap-admin",
        actor_roles=["admin"],
    )

    external = access_control.get_profile(created["profile_id"])
    internal = access_control.get_profile_internal(created["profile_id"])

    assert "mongo-test-p4ssw0rd" not in external["source_connection"]
    assert "mongo-test-p4ssw0rd" in internal["source_connection"]
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-003")


def test_profile_update_preserves_masked_connection_secret(access_control: AccessControlService) -> None:
    """Read-edit-save profile updates should not persist the API's masked password."""
    created = access_control.create_profile(
        {
            "name": "masked-postgres",
            "source_type": "postgresql",
            "source_connection": "postgresql://postgres:real-db-pass@example.net:5432/app",
            "allowed_permissions": ["catalog.read", "data.read"],
        },
        actor_user_id="bootstrap-admin",
        actor_roles=["admin"],
    )
    external = access_control.get_profile(created["profile_id"])

    access_control.update_profile(
        created["profile_id"],
        {
            "name": external["name"],
            "source_type": external["source_type"],
            "source_connection": external["source_connection"],
            "description": external["description"],
            "namespaces": external["namespaces"],
            "entities": external["entities"],
            "enabled_tools": external["enabled_tools"],
            "allowed_permissions": external["allowed_permissions"],
            "field_masks": {"email": "***MASKED***"},
            "field_exclusions": external["field_exclusions"],
            "index_policy": external["index_policy"],
        },
        actor_user_id="bootstrap-admin",
        actor_roles=["admin"],
    )

    internal = access_control.get_profile_internal(created["profile_id"])
    refreshed = access_control.get_profile(created["profile_id"])

    assert internal["source_connection"] == "postgresql://postgres:real-db-pass@example.net:5432/app"
    assert refreshed["source_connection"] == "postgresql://postgres:****@example.net:5432/app"
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-003")


def test_verify_api_key_applies_role_permissions_and_key_scopes(access_control: AccessControlService) -> None:
    """API keys should inherit user/group RBAC and then be reduced by key scopes."""
    profile = access_control.create_profile(
        {
            "name": "catalogue",
            "source_type": "opensearch",
            "source_connection": "os0",
            "allowed_permissions": ["catalog.read", "data.read", "data.update"],
        },
        actor_user_id="bootstrap-admin",
        actor_roles=["admin"],
    )
    user = access_control.create_user(
        {
            "username": "analyst-a",
            "display_name": "Analyst A",
            "roles": ["analyst"],
        },
        actor_user_id="bootstrap-admin",
        actor_roles=["admin"],
    )
    api_key = access_control.create_api_key(
        {
            "owner_user_id": user["user_id"],
            "name": "analyst-key",
            "scopes": ["data.read"],
            "profile_ids": [profile["profile_id"]],
        },
        actor_user_id="bootstrap-admin",
        actor_roles=["admin"],
    )

    principal = access_control.verify_api_key(api_key["raw_key"])

    assert principal is not None
    assert principal.user_id == user["user_id"]
    assert principal.roles == ["analyst"]
    assert principal.permissions == ["data.read"]
    assert principal.profile_ids == [profile["profile_id"]]


@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-003")
def test_rotate_api_key_revokes_old_key_and_preserves_scope(access_control: AccessControlService) -> None:
    """Rotating an API key should invalidate the old secret and preserve bindings."""
    profile = access_control.create_profile(
        {
            "name": "rotation-profile",
            "source_type": "mongodb",
            "source_connection": "mongo0",
            "allowed_permissions": ["catalog.read", "data.read"],
        },
        actor_user_id="bootstrap-admin",
        actor_roles=["admin"],
    )
    user = access_control.create_user(
        {
            "username": "rotation-analyst",
            "display_name": "Rotation Analyst",
            "roles": ["analyst"],
        },
        actor_user_id="bootstrap-admin",
        actor_roles=["admin"],
    )
    created = access_control.create_api_key(
        {
            "owner_user_id": user["user_id"],
            "name": "rotation-key",
            "scopes": ["data.read"],
            "profile_ids": [profile["profile_id"]],
        },
        actor_user_id="bootstrap-admin",
        actor_roles=["admin"],
    )

    rotated = access_control.rotate_api_key(
        created["api_key_id"],
        actor_user_id="bootstrap-admin",
        actor_roles=["admin"],
        reason="unit-test",
    )

    assert access_control.verify_api_key(created["raw_key"]) is None
    principal = access_control.verify_api_key(rotated["raw_key"])
    assert principal is not None
    assert principal.api_key_id == rotated["api_key"]["api_key_id"]
    assert principal.permissions == ["data.read"]
    assert principal.profile_ids == [profile["profile_id"]]
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-003")


def test_group_role_assignments_contribute_to_effective_permissions(access_control: AccessControlService) -> None:
    """Group roles should extend a user's effective RBAC permissions."""
    user = access_control.create_user(
        {
            "username": "dev-a",
            "display_name": "Developer A",
            "roles": ["analyst"],
        },
        actor_user_id="bootstrap-admin",
        actor_roles=["admin"],
    )
    access_control.create_group(
        {
            "name": "schema-admins",
            "roles": ["developer"],
            "member_user_ids": [user["user_id"]],
        },
        actor_user_id="bootstrap-admin",
        actor_roles=["admin"],
    )

    updated_user = access_control.get_user(user["user_id"])

    assert "developer" in updated_user["effective_roles"]
    assert "schema.change" in updated_user["effective_permissions"]
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-003")


def test_flat_demo_keys_resolve_to_three_flat_roles(access_control: AccessControlService, tmp_path: Path) -> None:
    """The api-key login lane seeds admin, read-write, and read-only demo keys."""
    admin = access_control.verify_api_key(_demo_key(tmp_path, "admin"))
    read_write = access_control.verify_api_key(_demo_key(tmp_path, "read-write"))
    read_only = access_control.verify_api_key(_demo_key(tmp_path, "read-only"))

    assert admin is not None and admin.roles == ["admin"] and "*" in admin.permissions
    assert read_write is not None and read_write.roles == ["read-write"]
    assert "data.create" in read_write.permissions
    assert "profile.manage" in read_write.permissions
    assert read_only is not None and read_only.roles == ["read-only"]
    assert "data.read" in read_only.permissions
    assert "data.create" not in read_only.permissions
    assert "profile.manage" not in read_only.permissions
