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


class SourceConnectionCreateRequest(BaseModel):
    """Payload for creating a named source connection."""

    name: str
    source_type: str
    uri_template: str
    credentials_ref: str | None = None
    description: str = ""


class SourceConnectionUpdateRequest(BaseModel):
    """Payload for updating mutable source-connection fields."""

    uri_template: str
    credentials_ref: str | None = None
    description: str = ""


class SourceConnectionDraftTestRequest(BaseModel):
    """Payload for testing a source-connection draft without persistence."""

    source_type: str
    uri_template: str
    credentials_ref: str | None = None
    description: str = ""


class DiscoveryNamespacesRequest(BaseModel):
    """Payload for namespace discovery."""

    profile_id: str | None = None
    connection_name: str | None = None
    refresh: bool = False
    ttl_seconds: int = 600


class DiscoveryEntitiesRequest(BaseModel):
    """Payload for entity discovery within a namespace."""

    profile_id: str
    namespace: str
    refresh: bool = False
    ttl_seconds: int = 600


class DiscoveryFieldsRequest(BaseModel):
    """Payload for field discovery within an entity."""

    profile_id: str
    namespace: str
    entity: str
    refresh: bool = False
    ttl_seconds: int = 600


class SavedQueryCreateRequest(BaseModel):
    """Payload for creating saved query-builder state."""

    page_key: str
    name: str
    payload: dict[str, Any]
    description: str = ""
    shared: bool = False


class SavedQueryUpdateRequest(BaseModel):
    """Payload for updating saved query-builder state."""

    name: str | None = None
    payload: dict[str, Any] | None = None
    description: str | None = None
    shared: bool | None = None


class ProfileScopeTestRequest(BaseModel):
    """Payload for dry-running a profile's connector scope."""

    profile: dict[str, Any] | None = None


class SchemaChangeApproveRequest(BaseModel):
    """Payload for approving a planned schema change."""

    target_name: str | None = None


class TestDataSeedRequest(BaseModel):
    """Payload for gated test-data seeding."""

    dataset_id: str
    connection_name: str


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


class RoleCreateRequest(BaseModel):
    """Payload for creating a role (PS-71 §IW3A)."""

    name: str
    description: str = ""
    permissions: list[str] = Field(default_factory=list)


class RoleUpdateRequest(BaseModel):
    """Payload for updating a role's description and/or permissions (PS-71 §IW3A)."""

    description: str | None = None
    permissions: list[str] | None = None


class RevokeApiKeyRequest(BaseModel):
    """Payload for revoking an API key."""

    reason: str = "revoked"


class MaskPreviewRequest(BaseModel):
    """Payload for previewing profile masking rules."""

    record: dict[str, Any]
