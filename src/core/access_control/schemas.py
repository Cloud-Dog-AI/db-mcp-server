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
# Description: Pydantic schemas for access-control APIs and MCP tools.
# Related requirements: AC-01, CFG-01
# Related tests: ST1.2, IT1.1

"""Pydantic contracts for access-control routes and tools."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ProfileUpsertRequest(BaseModel):
    """Payload for creating or updating a profile."""

    name: str
    source_type: str
    source_connection: str
    description: str = ""
    namespaces: list[str] = Field(default_factory=list)
    entities: list[str] = Field(default_factory=list)
    enabled_tools: list[str] = Field(default_factory=list)
    allowed_permissions: list[str] = Field(default_factory=list)
    field_masks: dict[str, str] = Field(default_factory=dict)
    field_exclusions: list[str] = Field(default_factory=list)
    index_policy: dict[str, Any] = Field(default_factory=dict)


class UserUpsertRequest(BaseModel):
    """Payload for creating or updating a user."""

    username: str
    email: str = ""
    display_name: str = ""
    status: str = "active"
    roles: list[str] = Field(default_factory=list)
    tenant_id: str | None = None


class GroupUpsertRequest(BaseModel):
    """Payload for creating or updating a group."""

    name: str
    description: str = ""
    roles: list[str] = Field(default_factory=list)
    member_user_ids: list[str] = Field(default_factory=list)
    tenant_id: str | None = None


class ApiKeyCreateRequest(BaseModel):
    """Payload for creating a scoped API key."""

    owner_user_id: str
    name: str
    scopes: list[str] = Field(default_factory=list)
    profile_ids: list[str] = Field(default_factory=list)
    ttl_days: int | None = None


class RevokeApiKeyRequest(BaseModel):
    """Payload for revoking an API key."""

    reason: str = "revoked"


class MaskPreviewRequest(BaseModel):
    """Payload for previewing profile masking rules."""

    record: dict[str, Any]
