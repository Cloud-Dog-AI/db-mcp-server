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
# Description: Relationship metadata models for curated and inferred links.
# Related requirements: RL-01, RL-02, RL-03
# Related tests: UT1.8, IT1.5

"""Relationship metadata models."""

from __future__ import annotations

from dataclasses import dataclass, field as dataclass_field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def utcnow() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class RelationshipRecord:
    """Relationship metadata persisted in the metadata store."""

    relationship_id: str = dataclass_field(default_factory=lambda: str(uuid4()))
    profile_id: str = ""
    namespace: str = ""
    entity: str = ""
    field: str = ""
    target_namespace: str = ""
    target_entity: str = ""
    relationship_type: str = "reference_candidate"
    provenance: str = "curated"
    confidence: float | None = None
    description: str = ""
    metadata: dict[str, Any] = dataclass_field(default_factory=dict)
    created_at: datetime = dataclass_field(default_factory=utcnow)
    updated_at: datetime = dataclass_field(default_factory=utcnow)
