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
# Description: Authenticated-non-admin -> 403/deny + profile password masking
#              (W28A-889-B-R2 / W28A-890 db-mcp identity-collapse fix).
# Related requirements: AC-01, AC-02, AC-03
# Related tests: UT1.51

"""
UT1.51 - db-mcp web-tier identity-collapse hardening (W28A-889-B-R2 / W28A-890).

Before the fix, the web tier injected the service api-key (bootstrap-admin / `*`)
for ANY session, so every web caller authorized as service-admin. Two component
seams are pinned here (the full create_api_app path is exercised live on preprod;
locally it depends on a platform-idam version that this checkout cannot resolve):

  1. AccessControlService.principal_for_username + profile password masking;
  2. APIKeyAuthMiddleware webui identity-forwarding (forward the caller's OWN RBAC,
     gated so only an admin/service transport key may forward identity).
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from cloud_dog_api_kit.errors import UnauthorisedError
from cloud_dog_logging import get_audit_logger, setup_logging

from src.common.config_loader import load_runtime_config
from src.common.http import APIKeyAuthMiddleware
from src.core.access_control.service import AccessControlService, _mask_connection_secret

pytestmark = [pytest.mark.unit]


# ---------------------------------------------------------------------------
# 1. AccessControlService: principal_for_username + profile password masking
# ---------------------------------------------------------------------------

@pytest.fixture()
def access(tmp_path: Path) -> AccessControlService:
    setup_logging(
        {
            "service_name": "db-mcp-server",
            "service_instance": "ut-authed-non-admin",
            "environment": "test",
            "log": {"console": False, "audit_log": str(tmp_path / "audit.log.jsonl")},
        }
    )
    config = load_runtime_config(["tests/env-UT"])
    engine = create_engine(f"sqlite:///{tmp_path / 'metadata.db'}")
    return AccessControlService(config=config, engine=engine, audit_logger=get_audit_logger())


def _make_nonadmin(access: AccessControlService, username: str = "nonadmin1") -> str:
    access.create_user(
        {"username": username, "display_name": "Non Admin", "roles": []},
        actor_user_id="bootstrap-admin",
        actor_roles=["admin"],
    )
    return username
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.probe  # rtt-2026-06-12 INST3: KEEP-AS-PROBE pending operator REQ-binding


def test_principal_for_admin_has_wildcard(access: AccessControlService) -> None:
    principal = access.principal_for_username("bootstrap-admin")
    assert principal is not None
    assert "*" in principal.permissions
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.probe  # rtt-2026-06-12 INST3: KEEP-AS-PROBE pending operator REQ-binding


def test_principal_for_nonadmin_is_denied_profile_manage(access: AccessControlService) -> None:
    user = _make_nonadmin(access)
    principal = access.principal_for_username(user)
    assert principal is not None
    assert "*" not in principal.permissions
    with pytest.raises(UnauthorisedError):
        access.ensure_permission(
            principal,
            permission="profile.manage",
            audit_resource_type="profile",
            audit_resource_id="list",
        )
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.probe  # rtt-2026-06-12 INST3: KEEP-AS-PROBE pending operator REQ-binding


def test_principal_for_unknown_user_is_none(access: AccessControlService) -> None:
    assert access.principal_for_username("ghost-user-not-real") is None
    assert access.principal_for_username("") is None
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.probe  # rtt-2026-06-12 INST3: KEEP-AS-PROBE pending operator REQ-binding


def test_profile_view_masks_connection_password(access: AccessControlService) -> None:
    created = access.create_profile(
        {
            "name": "pg-prod",
            "source_type": "postgresql",
            "source_connection": "postgresql://dbuser:SuperSecretPw@db2.app.vpc0:5432/app",
            "allowed_permissions": ["data.read"],
        },
        actor_user_id="bootstrap-admin",
        actor_roles=["admin"],
    )
    assert created["source_connection"] == "postgresql://dbuser:****@db2.app.vpc0:5432/app"
    listed = access.list_profiles()
    assert all("SuperSecretPw" not in str(p.get("source_connection")) for p in listed)
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.probe  # rtt-2026-06-12 INST3: KEEP-AS-PROBE pending operator REQ-binding


def test_mask_connection_secret_forms() -> None:
    assert _mask_connection_secret("postgresql://u:p@h:5432/d") == "postgresql://u:****@h:5432/d"
    assert _mask_connection_secret("mysql://root:s3cr3t@db1/app") == "mysql://root:****@db1/app"
    assert "topsecret" not in _mask_connection_secret("host=db;password=topsecret;db=app")
    # No-credential strings are returned unchanged.
    assert _mask_connection_secret("mongo0") == "mongo0"
    assert _mask_connection_secret("") == ""


# ---------------------------------------------------------------------------
# 2. APIKeyAuthMiddleware: webui identity forwarding (gated, no escalation)
# ---------------------------------------------------------------------------

ADMIN_PRINCIPAL = {"user_id": "bootstrap-admin", "username": "bootstrap-admin", "roles": ["admin"], "permissions": ["*"], "principal": SimpleNamespace(user_id="bootstrap-admin")}
NONADMIN_PRINCIPAL = {"user_id": "u-nonadmin", "username": "nonadmin", "roles": [], "permissions": [], "principal": SimpleNamespace(user_id="u-nonadmin")}


def _principal_obj(user_id, username, permissions):
    return SimpleNamespace(
        user_id=user_id, username=username, roles=[], permissions=permissions,
        api_key_id="", profile_ids=["*"], scopes=["*"], tenant_id=None,
    )


@pytest.fixture()
def mw_client() -> TestClient:
    app = FastAPI()

    @app.get("/protected")
    async def protected(request: Request):
        return {"username": request.state.username, "permissions": list(request.state.permissions or [])}

    async def verify_api_key(key: str):
        if key == "service-key":
            return dict(ADMIN_PRINCIPAL)
        if key == "nonadmin-key":
            return dict(NONADMIN_PRINCIPAL)
        return None

    def resolve_web_user(username: str):
        users = {
            "bootstrap-admin": _principal_obj("bootstrap-admin", "bootstrap-admin", ["*"]),
            "analyst": _principal_obj("u-analyst", "analyst", ["data.read"]),
        }
        return users.get(username)

    app.add_middleware(
        APIKeyAuthMiddleware,
        verify_api_key=verify_api_key,
        resolve_web_user=resolve_web_user,
    )
    return TestClient(app)
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.probe  # rtt-2026-06-12 INST3: KEEP-AS-PROBE pending operator REQ-binding


def test_service_key_only_is_admin_unchanged(mw_client: TestClient) -> None:
    r = mw_client.get("/protected", headers={"X-API-Key": "service-key"})
    assert r.status_code == 200
    assert r.json()["permissions"] == ["*"]
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.probe  # rtt-2026-06-12 INST3: KEEP-AS-PROBE pending operator REQ-binding


def test_webui_forwarded_nonadmin_is_reresolved_not_admin(mw_client: TestClient) -> None:
    r = mw_client.get(
        "/protected",
        headers={"X-API-Key": "service-key", "X-Request-Source": "webui", "X-Request-User": "analyst"},
    )
    assert r.status_code == 200
    assert r.json()["permissions"] == ["data.read"]  # forwarded user's OWN RBAC, not "*"
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.probe  # rtt-2026-06-12 INST3: KEEP-AS-PROBE pending operator REQ-binding


def test_webui_forwarded_unknown_user_denied(mw_client: TestClient) -> None:
    r = mw_client.get(
        "/protected",
        headers={"X-API-Key": "service-key", "X-Request-Source": "webui", "X-Request-User": "ghost"},
    )
    assert r.status_code == 401
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.probe  # rtt-2026-06-12 INST3: KEEP-AS-PROBE pending operator REQ-binding


def test_nonadmin_key_cannot_escalate_via_webui_header(mw_client: TestClient) -> None:
    # A non-admin transport key forwarding X-Request-User=bootstrap-admin must NOT
    # be honoured (gate: only an admin/service transport "*" may forward identity).
    r = mw_client.get(
        "/protected",
        headers={"X-API-Key": "nonadmin-key", "X-Request-Source": "webui", "X-Request-User": "bootstrap-admin"},
    )
    assert r.status_code == 200
    assert r.json()["permissions"] == []  # stays the non-admin's own (empty) permissions
