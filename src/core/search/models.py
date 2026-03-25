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
# Description: Discovery index models for db-mcp-server search and indexing.
# Related requirements: W28A-274-I deliverables 1, 2, 3, 4
# Related tests: UT1.9, UT1.10, ST1.7, IT1.6

"""Discovery index models for db-mcp-server."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def utcnow_iso() -> str:
    """Return the current UTC time in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class DiscoveryDocument:
    """Normalised record persisted into the discovery search index."""

    document_id: str
    profile_id: str
    namespace: str
    entity: str
    doc_kind: str
    title: str
    keywords: str = ""
    body: str = ""
    excerpt: str = ""
    related_entity: str = ""
    match_fields: list[str] = field(default_factory=list)
    payload: dict[str, Any] = field(default_factory=dict)
    updated_at: str = field(default_factory=utcnow_iso)


@dataclass(slots=True)
class ProfileIndexStatus:
    """Aggregated indexing status for a profile."""

    profile_id: str
    last_job_id: str = ""
    last_job_status: str = "idle"
    last_synced_at: str | None = None
    freshness_state: str = "never_indexed"
    namespace_count: int = 0
    entity_count: int = 0
    field_count: int = 0
    relationship_count: int = 0
    content_count: int = 0
    document_count: int = 0
    error: str = ""


@dataclass(slots=True)
class EntityIndexStatus:
    """Per-entity indexing status within a profile."""

    profile_id: str
    namespace: str
    entity: str
    last_job_id: str = ""
    last_job_status: str = "idle"
    last_synced_at: str | None = None
    document_count: int = 0
    field_count: int = 0
    relationship_count: int = 0
    content_count: int = 0
    error: str = ""
