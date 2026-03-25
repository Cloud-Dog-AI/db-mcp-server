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
# Description: Canonical access-control dataclasses and role mappings.
# Related requirements: AC-01, AC-03
# Related tests: UT1.3, IT1.1

"""Canonical access-control models for db-mcp-server."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def utcnow() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class Profile:
    """Profile-scoped connection and permission policy."""

    profile_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    source_type: str = ""
    source_connection: str = ""
    description: str = ""
    namespaces: list[str] = field(default_factory=list)
    entities: list[str] = field(default_factory=list)
    enabled_tools: list[str] = field(default_factory=list)
    allowed_permissions: list[str] = field(default_factory=list)
    field_masks: dict[str, str] = field(default_factory=dict)
    field_exclusions: list[str] = field(default_factory=list)
    index_policy: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class AccessUser:
    """User model persisted for profile-based access control."""

    user_id: str = field(default_factory=lambda: str(uuid4()))
    username: str = ""
    email: str = ""
    display_name: str = ""
    status: str = "active"
    roles: list[str] = field(default_factory=list)
    tenant_id: str | None = None
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class AccessGroup:
    """Group model with role assignments and member user ids."""

    group_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""
    roles: list[str] = field(default_factory=list)
    member_user_ids: list[str] = field(default_factory=list)
    tenant_id: str | None = None
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class AccessApiKey:
    """API key record with capability and profile scoping."""

    api_key_id: str = field(default_factory=lambda: str(uuid4()))
    owner_user_id: str = ""
    name: str = ""
    key_prefix: str = "cd_"
    key_hash: str = ""
    status: str = "active"
    scopes: list[str] = field(default_factory=list)
    profile_ids: list[str] = field(default_factory=list)
    expires_at: datetime | None = None
    created_at: datetime = field(default_factory=utcnow)
    revoked_at: datetime | None = None


ROLE_NAMES = ["admin", "data_steward", "developer", "analyst", "auditor"]

DEFAULT_ROLE_PERMISSIONS: dict[str, set[str]] = {
    "admin": {"*"},
    "data_steward": {
        "catalog.read",
        "schema.read",
        "schema.change",
        "relationship.read",
        "relationship.change",
        "content.search",
        "data.read",
        "data.create",
        "data.update",
        "data.delete",
        "index.manage",
        "profile.manage",
        "audit.read",
    },
    "developer": {
        "catalog.read",
        "schema.read",
        "schema.change",
        "relationship.read",
        "content.search",
        "data.read",
        "data.create",
        "data.update",
        "index.manage",
    },
    "analyst": {
        "catalog.read",
        "schema.read",
        "relationship.read",
        "content.search",
        "data.read",
    },
    "auditor": {
        "catalog.read",
        "schema.read",
        "relationship.read",
        "audit.read",
        "data.read",
    },
}


PERMISSION_DOMAINS = {
    "catalog.read",
    "schema.read",
    "schema.change",
    "relationship.read",
    "relationship.change",
    "content.search",
    "data.read",
    "data.create",
    "data.update",
    "data.delete",
    "index.manage",
    "profile.manage",
    "audit.read",
}


def ensure_known_permissions(values: list[str]) -> list[str]:
    """Validate permission strings supplied by callers."""
    unknown = [value for value in values if value not in PERMISSION_DOMAINS and value != "*"]
    if unknown:
        raise ValueError(f"Unknown permissions: {unknown}")
    return values


def serialise_datetime(value: datetime | None) -> str | None:
    """Convert datetimes to ISO-8601 strings for persistence payloads."""
    if value is None:
        return None
    return value.astimezone(timezone.utc).isoformat()


def coerce_datetime(value: Any) -> datetime | None:
    """Convert persisted ISO strings back to datetime values."""
    if value in {None, ""}:
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))
