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

from cloud_dog_db.sql import Boolean, Column, DateTime, Engine, Integer, MetaData, String, Table, Text, delete, select, update

from src.core.access_control.models import (
    AccessApiKey,
    AccessGroup,
    AccessUser,
    Profile,
    SavedQuery,
    SourceConnection,
    coerce_datetime,
    serialise_datetime,
    utcnow,
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
        self._source_connections = Table(
            "source_connections",
            self._metadata,
            Column("name", String(100), primary_key=True),
            Column("source_type", String(50), nullable=False),
            Column("uri_template", String(1024), nullable=False),
            Column("credentials_ref", String(512), nullable=True),
            Column("description", Text, nullable=False, default=""),
            Column("status", String(20), nullable=False, default="not_tested"),
            Column("last_tested_at", DateTime(timezone=True), nullable=True),
            Column("last_test_result", Text, nullable=False, default="{}"),
            Column("created_at", DateTime(timezone=True), nullable=False),
            Column("updated_at", DateTime(timezone=True), nullable=False),
        )
        self._discovery_cache = Table(
            "discovery_cache",
            self._metadata,
            Column("profile_id", String(64), primary_key=True),
            Column("cache_key", String(120), primary_key=True),
            Column("payload", Text, nullable=False),
            Column("refreshed_at", DateTime(timezone=True), nullable=False),
            Column("ttl_seconds", Integer, nullable=False, default=600),
        )
        self._saved_queries = Table(
            "saved_queries",
            self._metadata,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("user_id", String(64), nullable=False),
            Column("page_key", String(64), nullable=False),
            Column("name", String(120), nullable=False),
            Column("description", Text, nullable=False, default=""),
            Column("payload", Text, nullable=False),
            Column("shared", Boolean, nullable=False, default=False),
            Column("created_at", DateTime(timezone=True), nullable=False),
            Column("updated_at", DateTime(timezone=True), nullable=False),
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
    def _source_connection_to_values(connection: SourceConnection) -> dict[str, Any]:
        return {
            "name": connection.name,
            "source_type": connection.source_type,
            "uri_template": connection.uri_template,
            "credentials_ref": connection.credentials_ref,
            "description": connection.description,
            "status": connection.status,
            "last_tested_at": connection.last_tested_at,
            "last_test_result": json.dumps(connection.last_test_result, sort_keys=True),
            "created_at": connection.created_at,
            "updated_at": connection.updated_at,
        }

    @staticmethod
    def _source_connection_from_row(row: Any) -> SourceConnection:
        return SourceConnection(
            name=row.name,
            source_type=row.source_type,
            uri_template=row.uri_template,
            credentials_ref=row.credentials_ref,
            description=row.description or "",
            status=row.status,
            last_tested_at=coerce_datetime(row.last_tested_at),
            last_test_result=json.loads(row.last_test_result or "{}"),
            created_at=coerce_datetime(row.created_at),
            updated_at=coerce_datetime(row.updated_at),
        )

    @staticmethod
    def _saved_query_to_values(saved_query: SavedQuery) -> dict[str, Any]:
        values = {
            "user_id": saved_query.user_id,
            "page_key": saved_query.page_key,
            "name": saved_query.name,
            "description": saved_query.description,
            "payload": json.dumps(saved_query.payload, sort_keys=True),
            "shared": bool(saved_query.shared),
            "created_at": saved_query.created_at,
            "updated_at": saved_query.updated_at,
        }
        if saved_query.id is not None:
            values["id"] = saved_query.id
        return values

    @staticmethod
    def _saved_query_from_row(row: Any) -> SavedQuery:
        item = row._mapping
        payload = item["payload"]
        if isinstance(payload, str):
            payload = json.loads(payload or "{}")
        return SavedQuery(
            id=int(item["id"]),
            user_id=item["user_id"],
            page_key=item["page_key"],
            name=item["name"],
            description=item["description"] or "",
            payload=dict(payload or {}),
            shared=bool(item["shared"]),
            created_at=coerce_datetime(item["created_at"]),
            updated_at=coerce_datetime(item["updated_at"]),
        )

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

    def upsert_source_connection(self, source_connection: SourceConnection) -> SourceConnection:
        values = self._source_connection_to_values(source_connection)
        with self._engine.begin() as connection:
            connection.execute(
                delete(self._source_connections).where(
                    self._source_connections.c.name == source_connection.name
                )
            )
            connection.execute(self._source_connections.insert().values(**values))
        return source_connection

    def get_source_connection(self, name: str) -> SourceConnection | None:
        with self._engine.begin() as connection:
            row = connection.execute(
                select(self._source_connections).where(self._source_connections.c.name == name)
            ).first()
        if row is None:
            return None
        return self._source_connection_from_row(row)

    def list_source_connections(self) -> list[SourceConnection]:
        with self._engine.begin() as connection:
            rows = connection.execute(select(self._source_connections)).all()
        return [self._source_connection_from_row(row) for row in rows]

    def delete_source_connection(self, name: str) -> bool:
        with self._engine.begin() as connection:
            result = connection.execute(
                delete(self._source_connections).where(self._source_connections.c.name == name)
            )
        return result.rowcount > 0

    def count_profiles_using_source_connection(self, name: str) -> int:
        return sum(1 for profile in self.list_profiles() if profile.source_connection == name)

    def upsert_discovery_cache(
        self,
        *,
        profile_id: str,
        cache_key: str,
        payload: list[dict[str, Any]],
        ttl_seconds: int = 600,
    ) -> dict[str, Any]:
        values = {
            "profile_id": profile_id,
            "cache_key": cache_key,
            "payload": json.dumps(payload, sort_keys=True),
            "refreshed_at": utcnow(),
            "ttl_seconds": max(1, int(ttl_seconds)),
        }
        with self._engine.begin() as connection:
            connection.execute(
                delete(self._discovery_cache).where(
                    (self._discovery_cache.c.profile_id == profile_id)
                    & (self._discovery_cache.c.cache_key == cache_key)
                )
            )
            connection.execute(self._discovery_cache.insert().values(**values))
        return {
            **values,
            "payload": payload,
        }

    def get_discovery_cache(self, *, profile_id: str, cache_key: str) -> dict[str, Any] | None:
        with self._engine.begin() as connection:
            row = connection.execute(
                select(self._discovery_cache).where(
                    (self._discovery_cache.c.profile_id == profile_id)
                    & (self._discovery_cache.c.cache_key == cache_key)
                )
            ).first()
        if row is None:
            return None
        item = row._mapping
        payload = item["payload"]
        if isinstance(payload, str):
            payload = json.loads(payload or "[]")
        return {
            "profile_id": item["profile_id"],
            "cache_key": item["cache_key"],
            "payload": payload,
            "refreshed_at": coerce_datetime(item["refreshed_at"]),
            "ttl_seconds": int(item["ttl_seconds"] or 600),
        }

    def create_saved_query(self, saved_query: SavedQuery) -> SavedQuery:
        values = self._saved_query_to_values(saved_query)
        with self._engine.begin() as connection:
            result = connection.execute(self._saved_queries.insert().values(**values))
        query_id = int(result.inserted_primary_key[0])
        saved = self.get_saved_query(query_id)
        if saved is None:
            raise RuntimeError(f"Saved query insert failed: {query_id}")
        return saved

    def get_saved_query(self, query_id: int) -> SavedQuery | None:
        with self._engine.begin() as connection:
            row = connection.execute(
                select(self._saved_queries).where(self._saved_queries.c.id == query_id)
            ).first()
        if row is None:
            return None
        return self._saved_query_from_row(row)

    def get_saved_query_by_name(
        self,
        *,
        user_id: str,
        page_key: str,
        name: str,
    ) -> SavedQuery | None:
        with self._engine.begin() as connection:
            row = connection.execute(
                select(self._saved_queries).where(
                    (self._saved_queries.c.user_id == user_id)
                    & (self._saved_queries.c.page_key == page_key)
                    & (self._saved_queries.c.name == name)
                )
            ).first()
        if row is None:
            return None
        return self._saved_query_from_row(row)

    def list_saved_queries(self, *, user_id: str, page_key: str) -> list[SavedQuery]:
        with self._engine.begin() as connection:
            rows = connection.execute(
                select(self._saved_queries).where(
                    (self._saved_queries.c.page_key == page_key)
                    & (
                        (self._saved_queries.c.user_id == user_id)
                        | (self._saved_queries.c.shared == True)  # noqa: E712
                    )
                )
            ).all()
        return [self._saved_query_from_row(row) for row in rows]

    def update_saved_query(self, saved_query: SavedQuery) -> SavedQuery:
        if saved_query.id is None:
            raise ValueError("saved_query.id is required for update")
        values = self._saved_query_to_values(saved_query)
        with self._engine.begin() as connection:
            connection.execute(
                update(self._saved_queries)
                .where(self._saved_queries.c.id == saved_query.id)
                .values(**values)
            )
        saved = self.get_saved_query(saved_query.id)
        if saved is None:
            raise RuntimeError(f"Saved query update failed: {saved_query.id}")
        return saved

    def delete_saved_query(self, query_id: int) -> bool:
        with self._engine.begin() as connection:
            result = connection.execute(delete(self._saved_queries).where(self._saved_queries.c.id == query_id))
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
