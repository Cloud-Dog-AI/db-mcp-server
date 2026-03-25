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
# Description: Metadata repository for persisted schema-change history.
# Related requirements: SC-01, SC-02, W28A-274-L deliverables 1, 4
# Related tests: UT1.12, ST1.6, IT1.7

"""Repository for persisted schema-change history."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import Column, Engine, MetaData, String, Table, Text, delete, desc, select

from src.core.access_control.models import serialise_datetime
from src.core.schema.models import SchemaChangeRecord


class SchemaChangeRepository:
    """Persist schema-change plans and results in the metadata store."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        self._metadata = MetaData()
        self._records = Table(
            "schema_change_history",
            self._metadata,
            Column("plan_id", String(64), primary_key=True),
            Column("profile_id", String(64), nullable=False),
            Column("status", String(32), nullable=False),
            Column("updated_at", String(64), nullable=False),
            Column("payload", Text, nullable=False),
        )
        self._metadata.create_all(self._engine)

    @staticmethod
    def _dump_payload(payload: dict[str, Any]) -> str:
        return json.dumps(payload, sort_keys=True)

    @staticmethod
    def _load_payload(raw: str) -> dict[str, Any]:
        return json.loads(raw)

    def upsert(self, record: SchemaChangeRecord) -> SchemaChangeRecord:
        payload = record.to_payload()
        with self._engine.begin() as connection:
            connection.execute(delete(self._records).where(self._records.c.plan_id == record.plan_id))
            connection.execute(
                self._records.insert().values(
                    plan_id=record.plan_id,
                    profile_id=record.profile_id,
                    status=record.status,
                    updated_at=serialise_datetime(record.updated_at) or "",
                    payload=self._dump_payload(payload),
                )
            )
        return record

    def get(self, plan_id: str) -> SchemaChangeRecord | None:
        with self._engine.begin() as connection:
            row = connection.execute(
                select(self._records.c.payload).where(self._records.c.plan_id == plan_id)
            ).first()
        if row is None:
            return None
        return SchemaChangeRecord.from_payload(self._load_payload(row.payload))

    def list(
        self,
        *,
        profile_id: str | None = None,
        status: str | None = None,
        limit: int = 20,
    ) -> list[SchemaChangeRecord]:
        statement = select(self._records.c.payload).order_by(desc(self._records.c.updated_at)).limit(max(1, min(limit, 200)))
        if profile_id:
            statement = statement.where(self._records.c.profile_id == profile_id)
        if status:
            statement = statement.where(self._records.c.status == status)
        with self._engine.begin() as connection:
            rows = connection.execute(statement).all()
        return [SchemaChangeRecord.from_payload(self._load_payload(row.payload)) for row in rows]
