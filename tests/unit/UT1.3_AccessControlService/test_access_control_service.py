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
def access_control(tmp_path: Path) -> AccessControlService:
    """Create an isolated access-control service bound to a temp SQLite store."""
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
