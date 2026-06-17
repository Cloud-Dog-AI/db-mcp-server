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
# Description: IDAM role-cascade negative IT (W28E-1824 / PS-IDAM-ROLE-CASCADE §4).
# Related requirements: FR-003, CS-002, CS-004 (anon / wrong-role / live cascade)
# Related tests: IT1.14

"""D5 (W28E-1808B): PS-IDAM-ROLE-CASCADE §4 live group-membership cascade +
anon / wrong-role negatives, exercised against the real AccessControlService,
the real cloud_dog_idam RBACEngine, and the real sqlite repository (no mocks).

Proves the deny -> add-to-group -> allow -> remove-from-group -> deny cascade
with cache invalidation (no restart), and that an unauthenticated request and a
wrong-role principal are denied.
"""

from __future__ import annotations

import uuid

import pytest
from cloud_dog_api_kit.errors.exceptions import UnauthorisedError
from starlette.requests import Request

from src.common.runtime import RuntimeFactory

pytestmark = [pytest.mark.integration, pytest.mark.timeout(120)]

# A read permission granted by the built-in "analyst" role (DEFAULT_ROLE_PERMISSIONS).
_GROUP_PERMISSION = "schema.read"
# A permission no read role grants (admin-only) — for the wrong-role negative.
_ADMIN_PERMISSION = "admin.manage"


def _anon_request() -> Request:
    return Request({"type": "http", "method": "GET", "path": "/x", "headers": [], "query_string": b"", "client": ("203.0.113.9", 5)})


@pytest.mark.IT
@pytest.mark.mcp
@pytest.mark.req("FR-003")
def test_idam_group_membership_cascade_and_negatives() -> None:
    runtime = RuntimeFactory.create(["tests/env-UT"])
    access = runtime.access_control
    suffix = uuid.uuid4().hex[:8]

    # ── 1. A user with no roles + no group membership is default-denied ──────────
    user = access.create_user(
        {"username": f"casc-{suffix}", "display_name": "Cascade User", "roles": []},
        actor_user_id="admin", actor_roles=["admin"],
    )
    user_id = user["user_id"]
    assert access._rbac.has_permission(user_id, _GROUP_PERMISSION) is False, "no-membership user must be denied"

    # ── 2. group-admin adds the user to a group whose role grants the permission ─
    group = access.create_group(
        {"name": f"casc-grp-{suffix}", "roles": ["analyst"], "member_user_ids": [user_id]},
        actor_user_id="admin", actor_roles=["admin"],
    )
    group_id = group["group_id"]
    # cache invalidation occurred via create_group -> _rebuild_rbac()
    assert access._rbac.has_permission(user_id, _GROUP_PERMISSION) is True, "group member must inherit the role grant"

    # ── 3. wrong-role: the analyst-via-group user still cannot do admin-only ops ─
    assert access._rbac.has_permission(user_id, _ADMIN_PERMISSION) is False, "analyst must NOT have admin permission"

    # ── 4. group-admin removes the user from the group -> permission revoked ─────
    access.update_group(
        group_id,
        {"name": f"casc-grp-{suffix}", "roles": ["analyst"], "member_user_ids": []},
        actor_user_id="admin", actor_roles=["admin"],
    )
    assert access._rbac.has_permission(user_id, _GROUP_PERMISSION) is False, "removed member must lose grant without restart"

    # ── 5. anonymous request (no principal) is denied (401) ─────────────────────
    with pytest.raises(UnauthorisedError):
        access.principal_from_request(_anon_request())
