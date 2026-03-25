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
# Description: SQLAlchemy-backed repository for relationship metadata records.
# Related requirements: RL-01, RL-02, RL-03
# Related tests: UT1.8, IT1.5

"""Relationship metadata repository."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from sqlalchemy import Engine, MetaData, Table, Column, String, Text, delete, select

from src.core.access_control.models import coerce_datetime, serialise_datetime
from src.core.relationships.models import RelationshipRecord


class RelationshipRepository:
    """Persist relationship metadata in the metadata store."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        self._metadata = MetaData()
        self._relationships = Table(
            "relationships",
            self._metadata,
            Column("relationship_id", String(64), primary_key=True),
            Column("profile_id", String(64), nullable=False),
            Column("namespace", String(256), nullable=False),
            Column("entity", String(256), nullable=False),
            Column("payload", Text, nullable=False),
        )
        self._metadata.create_all(self._engine)

    @staticmethod
    def _dump_payload(payload: dict[str, Any]) -> str:
        return json.dumps(payload, sort_keys=True)

    @staticmethod
    def _load_payload(raw: str) -> dict[str, Any]:
        return json.loads(raw)

    @staticmethod
    def _to_payload(record: RelationshipRecord) -> dict[str, Any]:
        payload = asdict(record)
        payload["created_at"] = serialise_datetime(record.created_at)
        payload["updated_at"] = serialise_datetime(record.updated_at)
        return payload

    @staticmethod
    def _from_payload(payload: dict[str, Any]) -> RelationshipRecord:
        item = dict(payload)
        item["created_at"] = coerce_datetime(item.get("created_at"))
        item["updated_at"] = coerce_datetime(item.get("updated_at"))
        return RelationshipRecord(**item)

    def upsert(self, record: RelationshipRecord) -> RelationshipRecord:
        payload = self._to_payload(record)
        with self._engine.begin() as connection:
            connection.execute(delete(self._relationships).where(self._relationships.c.relationship_id == record.relationship_id))
            connection.execute(
                self._relationships.insert().values(
                    relationship_id=record.relationship_id,
                    profile_id=record.profile_id,
                    namespace=record.namespace,
                    entity=record.entity,
                    payload=self._dump_payload(payload),
                )
            )
        return record

    def get(self, relationship_id: str) -> RelationshipRecord | None:
        with self._engine.begin() as connection:
            row = connection.execute(
                select(self._relationships.c.payload).where(self._relationships.c.relationship_id == relationship_id)
            ).first()
        if row is None:
            return None
        return self._from_payload(self._load_payload(row.payload))

    def list_for_entity(self, profile_id: str, namespace: str, entity: str) -> list[RelationshipRecord]:
        with self._engine.begin() as connection:
            rows = connection.execute(
                select(self._relationships.c.payload).where(
                    self._relationships.c.profile_id == profile_id,
                    self._relationships.c.namespace == namespace,
                    self._relationships.c.entity == entity,
                )
            ).all()
        return [self._from_payload(self._load_payload(row.payload)) for row in rows]

    def delete(self, relationship_id: str) -> bool:
        with self._engine.begin() as connection:
            result = connection.execute(delete(self._relationships).where(self._relationships.c.relationship_id == relationship_id))
        return result.rowcount > 0
