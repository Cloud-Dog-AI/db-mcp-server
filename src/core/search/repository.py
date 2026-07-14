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
# Description: SQLite FTS5 repository for db-mcp-server discovery search.
# Related requirements: W28A-274-I deliverables 1, 2, 3, 4
# Related tests: UT1.9, UT1.10, ST1.7, IT1.6

"""SQLite-backed discovery index repository."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any, Iterable

from cloud_dog_db.sql import SQLiteConnection, SQLiteRow, connect_sqlite

from src.common.storage_paths import ensure_directory, normalise_fs_path, parent_fs_path
from src.core.search.models import DiscoveryDocument, EntityIndexStatus, ProfileIndexStatus


class DiscoveryIndexRepository:
    """Persist and query discovery documents using SQLite FTS5."""

    def __init__(self, database_path: str) -> None:
        self._path = normalise_fs_path(database_path)
        ensure_directory(parent_fs_path(self._path))
        self._initialise()

    @property
    def path(self) -> str:
        """Return the SQLite path backing the discovery index."""
        return self._path

    def health_check(self) -> bool:
        """Return whether the repository can execute a trivial query."""
        with self._connect() as connection:
            row = connection.execute("SELECT 1 AS ok").fetchone()
        return bool(row and row["ok"] == 1)

    def replace_profile_documents(
        self,
        profile_id: str,
        documents: Iterable[DiscoveryDocument],
        *,
        profile_status: ProfileIndexStatus,
        entity_statuses: Iterable[EntityIndexStatus],
    ) -> None:
        """Replace all indexed documents and status rows for a profile."""
        with self._connect() as connection:
            connection.execute("DELETE FROM discovery_fts WHERE profile_id = ?", (profile_id,))
            connection.execute("DELETE FROM discovery_documents WHERE profile_id = ?", (profile_id,))
            connection.execute("DELETE FROM entity_index_status WHERE profile_id = ?", (profile_id,))
            for document in documents:
                self._insert_document(connection, document)
            self._upsert_profile_status(connection, profile_status)
            for status in entity_statuses:
                self._upsert_entity_status(connection, status)
            connection.commit()

    def replace_entity_documents(
        self,
        profile_id: str,
        namespace: str,
        entity: str,
        documents: Iterable[DiscoveryDocument],
        *,
        entity_status: EntityIndexStatus,
    ) -> None:
        """Replace indexed documents and status rows for a single entity."""
        with self._connect() as connection:
            connection.execute(
                "DELETE FROM discovery_fts WHERE profile_id = ? AND namespace = ? AND entity = ?",
                (profile_id, namespace, entity),
            )
            connection.execute(
                "DELETE FROM discovery_documents WHERE profile_id = ? AND namespace = ? AND entity = ?",
                (profile_id, namespace, entity),
            )
            for document in documents:
                self._insert_document(connection, document)
            self._upsert_entity_status(connection, entity_status)
            connection.commit()

    def update_profile_status(self, status: ProfileIndexStatus) -> None:
        """Upsert aggregated profile indexing status."""
        with self._connect() as connection:
            self._upsert_profile_status(connection, status)
            connection.commit()

    def update_entity_status(self, status: EntityIndexStatus) -> None:
        """Upsert per-entity indexing status."""
        with self._connect() as connection:
            self._upsert_entity_status(connection, status)
            connection.commit()

    def get_profile_status(self, profile_id: str) -> dict[str, Any] | None:
        """Return aggregated indexing status for a profile."""
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload FROM profile_index_status WHERE profile_id = ?",
                (profile_id,),
            ).fetchone()
        if row is None:
            return None
        return json.loads(row["payload"])

    def list_profile_statuses(self, profile_ids: list[str] | None = None) -> list[dict[str, Any]]:
        """List profile indexing status rows."""
        query = "SELECT payload FROM profile_index_status"
        params: list[Any] = []
        if profile_ids:
            placeholders = ",".join("?" for _ in profile_ids)
            query += f" WHERE profile_id IN ({placeholders})"
            params.extend(profile_ids)
        query += " ORDER BY profile_id"
        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [json.loads(row["payload"]) for row in rows]

    def list_entity_statuses(self, profile_id: str) -> list[dict[str, Any]]:
        """List entity indexing status rows for a profile."""
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload FROM entity_index_status WHERE profile_id = ? ORDER BY namespace, entity",
                (profile_id,),
            ).fetchall()
        return [json.loads(row["payload"]) for row in rows]

    def search_documents(
        self,
        *,
        profile_id: str,
        match_query: str,
        doc_kinds: list[str],
        limit: int,
    ) -> list[dict[str, Any]]:
        """Search discovery documents by profile and document kind."""
        placeholders = ",".join("?" for _ in doc_kinds)
        sql = f"""
            SELECT
                d.document_id,
                d.profile_id,
                d.namespace,
                d.entity,
                d.doc_kind,
                d.title,
                d.keywords,
                d.body,
                d.excerpt,
                d.related_entity,
                d.match_fields,
                d.payload,
                d.updated_at,
                bm25(discovery_fts, 8.0, 5.0, 3.0, 2.0, 1.0) AS score
            FROM discovery_fts
            JOIN discovery_documents AS d ON d.document_id = discovery_fts.document_id
            WHERE discovery_fts MATCH ?
              AND d.profile_id = ?
              AND d.doc_kind IN ({placeholders})
            ORDER BY score
            LIMIT ?
        """
        params: list[Any] = [match_query, profile_id, *doc_kinds, int(limit)]
        with self._connect() as connection:
            rows = connection.execute(sql, params).fetchall()
        return [self._row_to_document(row) for row in rows]

    def get_document(self, document_id: str) -> dict[str, Any] | None:
        """Fetch a discovery document by identifier."""
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM discovery_documents WHERE document_id = ?",
                (document_id,),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_document(row)

    def list_documents(
        self,
        *,
        profile_id: str,
        doc_kinds: list[str] | None = None,
        namespace: str | None = None,
        entity: str | None = None,
    ) -> list[dict[str, Any]]:
        """List discovery documents filtered by profile, kind, and entity."""
        clauses = ["profile_id = ?"]
        params: list[Any] = [profile_id]
        if doc_kinds:
            placeholders = ",".join("?" for _ in doc_kinds)
            clauses.append(f"doc_kind IN ({placeholders})")
            params.extend(doc_kinds)
        if namespace is not None:
            clauses.append("namespace = ?")
            params.append(namespace)
        if entity is not None:
            clauses.append("entity = ?")
            params.append(entity)
        sql = (
            "SELECT * FROM discovery_documents WHERE "
            + " AND ".join(clauses)
            + " ORDER BY namespace, entity, doc_kind, document_id"
        )
        with self._connect() as connection:
            rows = connection.execute(sql, params).fetchall()
        return [self._row_to_document(row) for row in rows]

    def count_documents(self, *, profile_id: str) -> int:
        """Return the number of indexed documents for a profile."""
        with self._connect() as connection:
            row = connection.execute(
                "SELECT COUNT(*) AS count FROM discovery_documents WHERE profile_id = ?",
                (profile_id,),
            ).fetchone()
        return int(row["count"] if row else 0)

    def clear_all(self) -> None:
        """Remove all index documents and status rows."""
        with self._connect() as connection:
            connection.execute("DELETE FROM discovery_fts")
            connection.execute("DELETE FROM discovery_documents")
            connection.execute("DELETE FROM profile_index_status")
            connection.execute("DELETE FROM entity_index_status")
            connection.commit()

    def _initialise(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS discovery_documents (
                    document_id TEXT PRIMARY KEY,
                    profile_id TEXT NOT NULL,
                    namespace TEXT NOT NULL,
                    entity TEXT NOT NULL,
                    doc_kind TEXT NOT NULL,
                    title TEXT NOT NULL,
                    keywords TEXT NOT NULL,
                    body TEXT NOT NULL,
                    excerpt TEXT NOT NULL,
                    related_entity TEXT NOT NULL,
                    match_fields TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE VIRTUAL TABLE IF NOT EXISTS discovery_fts USING fts5(
                    document_id UNINDEXED,
                    profile_id UNINDEXED,
                    namespace UNINDEXED,
                    entity UNINDEXED,
                    doc_kind UNINDEXED,
                    title,
                    keywords,
                    body,
                    excerpt,
                    related_entity,
                    tokenize = 'porter unicode61'
                );

                CREATE TABLE IF NOT EXISTS profile_index_status (
                    profile_id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS entity_index_status (
                    profile_id TEXT NOT NULL,
                    namespace TEXT NOT NULL,
                    entity TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    PRIMARY KEY (profile_id, namespace, entity)
                );

                CREATE INDEX IF NOT EXISTS idx_discovery_documents_profile
                    ON discovery_documents(profile_id, namespace, entity, doc_kind);
                """
            )
            connection.commit()

    def _connect(self) -> SQLiteConnection:
        return connect_sqlite(str(self._path))

    @staticmethod
    def _insert_document(connection: SQLiteConnection, document: DiscoveryDocument) -> None:
        connection.execute(
            """
            INSERT OR REPLACE INTO discovery_documents (
                document_id,
                profile_id,
                namespace,
                entity,
                doc_kind,
                title,
                keywords,
                body,
                excerpt,
                related_entity,
                match_fields,
                payload,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                document.document_id,
                document.profile_id,
                document.namespace,
                document.entity,
                document.doc_kind,
                document.title,
                document.keywords,
                document.body,
                document.excerpt,
                document.related_entity,
                json.dumps(document.match_fields, sort_keys=True),
                json.dumps(document.payload, sort_keys=True),
                document.updated_at,
            ),
        )
        connection.execute(
            "DELETE FROM discovery_fts WHERE document_id = ?",
            (document.document_id,),
        )
        connection.execute(
            """
            INSERT INTO discovery_fts (
                document_id,
                profile_id,
                namespace,
                entity,
                doc_kind,
                title,
                keywords,
                body,
                excerpt,
                related_entity
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                document.document_id,
                document.profile_id,
                document.namespace,
                document.entity,
                document.doc_kind,
                document.title,
                document.keywords,
                document.body,
                document.excerpt,
                document.related_entity,
            ),
        )

    @staticmethod
    def _upsert_profile_status(connection: SQLiteConnection, status: ProfileIndexStatus) -> None:
        connection.execute(
            "INSERT OR REPLACE INTO profile_index_status (profile_id, payload) VALUES (?, ?)",
            (
                status.profile_id,
                json.dumps(asdict(status), sort_keys=True),
            ),
        )

    @staticmethod
    def _upsert_entity_status(connection: SQLiteConnection, status: EntityIndexStatus) -> None:
        connection.execute(
            """
            INSERT OR REPLACE INTO entity_index_status (profile_id, namespace, entity, payload)
            VALUES (?, ?, ?, ?)
            """,
            (
                status.profile_id,
                status.namespace,
                status.entity,
                json.dumps(asdict(status), sort_keys=True),
            ),
        )

    @staticmethod
    def _row_to_document(row: SQLiteRow) -> dict[str, Any]:
        payload = dict(row)
        payload["match_fields"] = json.loads(payload.get("match_fields") or "[]")
        payload["payload"] = json.loads(payload.get("payload") or "{}")
        return payload
