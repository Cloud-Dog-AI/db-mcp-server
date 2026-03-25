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
# Description: SQLAlchemy-backed metadata repository for access control state.
# Related requirements: AC-01, CFG-01
# Related tests: UT1.3, ST1.2, IT1.1

"""Repository for db-mcp-server access-control state."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from sqlalchemy import Boolean, Engine, MetaData, Table, Column, String, Text, select, update, delete

from src.core.access_control.models import (
    AccessApiKey,
    AccessGroup,
    AccessUser,
    Profile,
    coerce_datetime,
    serialise_datetime,
)


class AccessControlRepository:
    """Persist access-control records in the metadata store."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        self._metadata = MetaData()
        self._profiles = Table(
            "access_profiles",
            self._metadata,
            Column("profile_id", String(64), primary_key=True),
            Column("payload", Text, nullable=False),
        )
        self._users = Table(
            "access_users",
            self._metadata,
            Column("user_id", String(64), primary_key=True),
            Column("payload", Text, nullable=False),
        )
        self._groups = Table(
            "access_groups",
            self._metadata,
            Column("group_id", String(64), primary_key=True),
            Column("payload", Text, nullable=False),
        )
        self._api_keys = Table(
            "access_api_keys",
            self._metadata,
            Column("api_key_id", String(64), primary_key=True),
            Column("owner_user_id", String(64), nullable=False),
            Column("key_hash", String(256), nullable=False),
            Column("status", String(32), nullable=False),
            Column("is_bootstrap", Boolean, nullable=False, default=False),
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
    def _profile_to_payload(profile: Profile) -> dict[str, Any]:
        payload = asdict(profile)
        payload["created_at"] = serialise_datetime(profile.created_at)
        payload["updated_at"] = serialise_datetime(profile.updated_at)
        return payload

    @staticmethod
    def _profile_from_payload(payload: dict[str, Any]) -> Profile:
        payload = dict(payload)
        payload["created_at"] = coerce_datetime(payload.get("created_at"))
        payload["updated_at"] = coerce_datetime(payload.get("updated_at"))
        return Profile(**payload)

    @staticmethod
    def _user_to_payload(user: AccessUser) -> dict[str, Any]:
        payload = asdict(user)
        payload["created_at"] = serialise_datetime(user.created_at)
        payload["updated_at"] = serialise_datetime(user.updated_at)
        return payload

    @staticmethod
    def _user_from_payload(payload: dict[str, Any]) -> AccessUser:
        payload = dict(payload)
        payload["created_at"] = coerce_datetime(payload.get("created_at"))
        payload["updated_at"] = coerce_datetime(payload.get("updated_at"))
        return AccessUser(**payload)

    @staticmethod
    def _group_to_payload(group: AccessGroup) -> dict[str, Any]:
        payload = asdict(group)
        payload["created_at"] = serialise_datetime(group.created_at)
        payload["updated_at"] = serialise_datetime(group.updated_at)
        return payload

    @staticmethod
    def _group_from_payload(payload: dict[str, Any]) -> AccessGroup:
        payload = dict(payload)
        payload["created_at"] = coerce_datetime(payload.get("created_at"))
        payload["updated_at"] = coerce_datetime(payload.get("updated_at"))
        return AccessGroup(**payload)

    @staticmethod
    def _api_key_to_payload(api_key: AccessApiKey) -> dict[str, Any]:
        payload = asdict(api_key)
        payload["created_at"] = serialise_datetime(api_key.created_at)
        payload["expires_at"] = serialise_datetime(api_key.expires_at)
        payload["revoked_at"] = serialise_datetime(api_key.revoked_at)
        return payload

    @staticmethod
    def _api_key_from_payload(payload: dict[str, Any]) -> AccessApiKey:
        payload = dict(payload)
        payload["created_at"] = coerce_datetime(payload.get("created_at"))
        payload["expires_at"] = coerce_datetime(payload.get("expires_at"))
        payload["revoked_at"] = coerce_datetime(payload.get("revoked_at"))
        return AccessApiKey(**payload)

    def upsert_profile(self, profile: Profile) -> Profile:
        payload = self._profile_to_payload(profile)
        with self._engine.begin() as connection:
            connection.execute(
                self._profiles.delete().where(self._profiles.c.profile_id == profile.profile_id)
            )
            connection.execute(
                self._profiles.insert().values(
                    profile_id=profile.profile_id,
                    payload=self._dump_payload(payload),
                )
            )
        return profile

    def get_profile(self, profile_id: str) -> Profile | None:
        with self._engine.begin() as connection:
            row = connection.execute(
                select(self._profiles.c.payload).where(self._profiles.c.profile_id == profile_id)
            ).first()
        if row is None:
            return None
        return self._profile_from_payload(self._load_payload(row.payload))

    def list_profiles(self) -> list[Profile]:
        with self._engine.begin() as connection:
            rows = connection.execute(select(self._profiles.c.payload)).all()
        return [self._profile_from_payload(self._load_payload(row.payload)) for row in rows]

    def delete_profile(self, profile_id: str) -> bool:
        with self._engine.begin() as connection:
            result = connection.execute(delete(self._profiles).where(self._profiles.c.profile_id == profile_id))
        return result.rowcount > 0

    def upsert_user(self, user: AccessUser) -> AccessUser:
        payload = self._user_to_payload(user)
        with self._engine.begin() as connection:
            connection.execute(delete(self._users).where(self._users.c.user_id == user.user_id))
            connection.execute(
                self._users.insert().values(user_id=user.user_id, payload=self._dump_payload(payload))
            )
        return user

    def get_user(self, user_id: str) -> AccessUser | None:
        with self._engine.begin() as connection:
            row = connection.execute(select(self._users.c.payload).where(self._users.c.user_id == user_id)).first()
        if row is None:
            return None
        return self._user_from_payload(self._load_payload(row.payload))

    def get_user_by_username(self, username: str) -> AccessUser | None:
        for user in self.list_users():
            if user.username == username:
                return user
        return None

    def list_users(self) -> list[AccessUser]:
        with self._engine.begin() as connection:
            rows = connection.execute(select(self._users.c.payload)).all()
        return [self._user_from_payload(self._load_payload(row.payload)) for row in rows]

    def delete_user(self, user_id: str) -> bool:
        with self._engine.begin() as connection:
            result = connection.execute(delete(self._users).where(self._users.c.user_id == user_id))
        return result.rowcount > 0

    def upsert_group(self, group: AccessGroup) -> AccessGroup:
        payload = self._group_to_payload(group)
        with self._engine.begin() as connection:
            connection.execute(delete(self._groups).where(self._groups.c.group_id == group.group_id))
            connection.execute(
                self._groups.insert().values(group_id=group.group_id, payload=self._dump_payload(payload))
            )
        return group

    def get_group(self, group_id: str) -> AccessGroup | None:
        with self._engine.begin() as connection:
            row = connection.execute(select(self._groups.c.payload).where(self._groups.c.group_id == group_id)).first()
        if row is None:
            return None
        return self._group_from_payload(self._load_payload(row.payload))

    def list_groups(self) -> list[AccessGroup]:
        with self._engine.begin() as connection:
            rows = connection.execute(select(self._groups.c.payload)).all()
        return [self._group_from_payload(self._load_payload(row.payload)) for row in rows]

    def delete_group(self, group_id: str) -> bool:
        with self._engine.begin() as connection:
            result = connection.execute(delete(self._groups).where(self._groups.c.group_id == group_id))
        return result.rowcount > 0

    def upsert_api_key(self, api_key: AccessApiKey, *, is_bootstrap: bool = False) -> AccessApiKey:
        payload = self._api_key_to_payload(api_key)
        with self._engine.begin() as connection:
            connection.execute(delete(self._api_keys).where(self._api_keys.c.api_key_id == api_key.api_key_id))
            connection.execute(
                self._api_keys.insert().values(
                    api_key_id=api_key.api_key_id,
                    owner_user_id=api_key.owner_user_id,
                    key_hash=api_key.key_hash,
                    status=api_key.status,
                    is_bootstrap=is_bootstrap,
                    payload=self._dump_payload(payload),
                )
        )
        return api_key

    def serialise_api_key(self, api_key: AccessApiKey) -> dict[str, Any]:
        """Return a persistence-ready API-key payload."""
        return self._api_key_to_payload(api_key)

    def get_api_key(self, api_key_id: str) -> AccessApiKey | None:
        with self._engine.begin() as connection:
            row = connection.execute(select(self._api_keys.c.payload).where(self._api_keys.c.api_key_id == api_key_id)).first()
        if row is None:
            return None
        return self._api_key_from_payload(self._load_payload(row.payload))

    def list_api_keys(self, owner_user_id: str | None = None) -> list[AccessApiKey]:
        with self._engine.begin() as connection:
            statement = select(self._api_keys.c.payload)
            if owner_user_id:
                statement = statement.where(self._api_keys.c.owner_user_id == owner_user_id)
            rows = connection.execute(statement).all()
        return [self._api_key_from_payload(self._load_payload(row.payload)) for row in rows]

    def find_api_key_by_hash(self, key_hash: str) -> AccessApiKey | None:
        with self._engine.begin() as connection:
            row = connection.execute(
                select(self._api_keys.c.payload).where(self._api_keys.c.key_hash == key_hash)
            ).first()
        if row is None:
            return None
        return self._api_key_from_payload(self._load_payload(row.payload))

    def revoke_api_key(self, api_key_id: str, payload: dict[str, Any]) -> bool:
        with self._engine.begin() as connection:
            result = connection.execute(
                update(self._api_keys)
                .where(self._api_keys.c.api_key_id == api_key_id)
                .values(status="revoked", payload=self._dump_payload(payload))
            )
        return result.rowcount > 0
