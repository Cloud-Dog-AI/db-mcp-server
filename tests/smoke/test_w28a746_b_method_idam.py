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
# Description: W28A-746 b-method local smoke for db-mcp IDAM and profile scope.
# Related requirements: AC-01, AC-03, AC-04, AC-05, AC-06, CFG-01
# Related tests: W28A-746 T0/T1/T2/T3

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import create_engine

from cloud_dog_api_kit.errors import UnauthorisedError
from cloud_dog_logging import get_audit_logger, setup_logging

from src.common.config_loader import load_runtime_config
from src.core.access_control.service import AccessControlService

pytestmark = [pytest.mark.unit, pytest.mark.security]


@pytest.fixture()
def access_control(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> AccessControlService:
    """Create an isolated access-control service for W28A-746 b-method checks."""
    monkeypatch.setenv("CLOUD_DOG__FLAT_LOGIN__DEMO_KEYS_DIR", str(tmp_path / "flat_role_keys"))
    setup_logging(
        {
            "service_name": "db-mcp-server",
            "service_instance": "w28a746-smoke",
            "environment": "test",
            "log": {"console": False, "audit_log": str(tmp_path / "audit.log.jsonl")},
        }
    )
    config = load_runtime_config(["tests/env-UT"])
    engine = create_engine(f"sqlite:///{tmp_path / 'metadata.db'}")
    return AccessControlService(config=config, engine=engine, audit_logger=get_audit_logger())


def test_t1_flat_roles_and_secret_masking(access_control: AccessControlService) -> None:
    """T1/T2: common IDAM roles exist and non-admin profile reads are masked."""
    profile = access_control.create_profile(
        {
            "name": "w28a746-mask",
            "source_type": "postgresql",
            "source_connection": "postgresql://reporter:TopSecretPw@db2.example.net:5432/app",
            "allowed_permissions": ["data.read"],
            "field_masks": {"salary": "***MASKED***"},
            "field_exclusions": ["ssn"],
        },
        actor_user_id="bootstrap-admin",
        actor_roles=["admin"],
    )

    assert "TopSecretPw" not in profile["source_connection"]
    assert profile["source_connection"] == "postgresql://reporter:****@db2.example.net:5432/app"
    assert access_control.apply_profile_mask(
        profile["profile_id"],
        {"salary": 120000, "ssn": "999", "name": "Alice"},
    ) == {"salary": "***MASKED***", "name": "Alice"}

    roles = {role["name"] for role in access_control.list_roles()}
    assert {"admin", "user", "group-admin", "restricted", "job-control", "audit-log"} <= roles


def test_t2_role_rbac_and_t3_group_membership_cascade(access_control: AccessControlService) -> None:
    """T2/T3: adding/removing group membership changes effective permissions live."""
    profile = access_control.create_profile(
        {
            "name": "w28a746-cascade",
            "source_type": "mongodb",
            "source_connection": "mongodb://mongo.example.net:27017",
            "allowed_permissions": ["data.read"],
        },
        actor_user_id="bootstrap-admin",
        actor_roles=["admin"],
    )
    user = access_control.create_user(
        {
            "username": "w28a746-user",
            "display_name": "W28A746 User",
            "roles": [],
        },
        actor_user_id="bootstrap-admin",
        actor_roles=["admin"],
    )
    key = access_control.create_api_key(
        {
            "owner_user_id": user["user_id"],
            "name": "w28a746-user-key",
            "scopes": ["data.read"],
            "profile_ids": [profile["profile_id"]],
        },
        actor_user_id="bootstrap-admin",
        actor_roles=["admin"],
    )

    before = access_control.verify_api_key(key["raw_key"])
    assert before is not None
    with pytest.raises(UnauthorisedError):
        access_control.ensure_permission(
            before,
            permission="data.read",
            profile_id=profile["profile_id"],
            audit_resource_type="profile",
            audit_resource_id=profile["profile_id"],
        )

    group = access_control.create_group(
        {
            "name": "w28a746-analysts",
            "roles": ["analyst"],
            "member_user_ids": [user["user_id"]],
        },
        actor_user_id="bootstrap-admin",
        actor_roles=["admin"],
    )

    after_add = access_control.verify_api_key(key["raw_key"])
    assert after_add is not None
    access_control.ensure_permission(
        after_add,
        permission="data.read",
        profile_id=profile["profile_id"],
        audit_resource_type="profile",
        audit_resource_id=profile["profile_id"],
    )
    assert "analyst" in after_add.roles

    access_control.update_group(
        group["group_id"],
        {"name": "w28a746-analysts", "roles": ["analyst"], "member_user_ids": []},
        actor_user_id="bootstrap-admin",
        actor_roles=["admin"],
    )
    after_remove = access_control.verify_api_key(key["raw_key"])
    assert after_remove is not None
    with pytest.raises(UnauthorisedError):
        access_control.ensure_permission(
            after_remove,
            permission="data.read",
            profile_id=profile["profile_id"],
            audit_resource_type="profile",
            audit_resource_id=profile["profile_id"],
        )
