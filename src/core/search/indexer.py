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
# Description: Discovery index document normalisation and indexing pipeline.
# Related requirements: W28A-274-I deliverables 1, 2
# Related tests: UT1.9, ST1.7, IT1.6

"""Discovery index document normalisation and indexing pipeline."""

from __future__ import annotations

import re
from collections import Counter
from datetime import datetime, timezone
from hashlib import md5
from typing import Any

from src.core.search.models import DiscoveryDocument, EntityIndexStatus, ProfileIndexStatus

_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")
_GENERIC_FIELD_TOKENS = {"id", "_id", "created", "updated", "date", "status"}


def normalise_search_terms(query: str) -> list[str]:
    """Split a free-text query into normalised FTS5-safe tokens."""
    return [token.lower() for token in _TOKEN_RE.findall(query or "") if token.strip()]


def build_fts5_query(query: str) -> str:
    """Build a simple AND-prefix FTS5 query from free text."""
    tokens = normalise_search_terms(query)
    if not tokens:
        return ""
    return " AND ".join(f'{token}*' for token in tokens)


class DiscoveryIndexer:
    """Build discovery documents from connector-visible metadata and content."""

    def __init__(self, runtime) -> None:
        self._runtime = runtime

    def sync_profile(self, profile_id: str, *, job_id: str) -> dict[str, Any]:
        """Build a full discovery index for a profile."""
        profile = self._runtime.access_control.get_profile(profile_id)
        session = self._runtime.connectors.for_profile(profile_id)
        documents: list[DiscoveryDocument] = []
        entity_statuses: list[EntityIndexStatus] = []
        counts: Counter[str] = Counter()
        namespaces_indexed: set[str] = set()
        try:
            namespaces = self._runtime.connectors.filter_namespaces(
                session.profile,
                session.connector.list_namespaces(),
            )
            documents.append(self._build_profile_document(profile))
            for namespace_item in namespaces:
                namespace = str(namespace_item.get("name", ""))
                namespaces_indexed.add(namespace)
                documents.append(self._build_namespace_document(profile_id, namespace, profile))
                entities = self._runtime.connectors.filter_entities(
                    session.profile,
                    namespace,
                    session.connector.list_entities(namespace),
                )
                for entity_item in entities:
                    entity = str(entity_item.get("name", ""))
                    entity_documents, entity_counts = self._build_entity_documents(
                        session,
                        profile_id=profile_id,
                        namespace=namespace,
                        entity=entity,
                    )
                    documents.extend(entity_documents)
                    counts.update(entity_counts)
                    entity_statuses.append(
                        EntityIndexStatus(
                            profile_id=profile_id,
                            namespace=namespace,
                            entity=entity,
                            last_job_id=job_id,
                            last_job_status="succeeded",
                            last_synced_at=self._now(),
                            document_count=len(entity_documents),
                            field_count=entity_counts["field"],
                            relationship_count=entity_counts["relationship_hint"],
                            content_count=entity_counts["content_excerpt"],
                        )
                    )
            status = ProfileIndexStatus(
                profile_id=profile_id,
                last_job_id=job_id,
                last_job_status="succeeded",
                last_synced_at=self._now(),
                freshness_state="fresh",
                namespace_count=len(namespaces_indexed),
                entity_count=sum(1 for item in entity_statuses),
                field_count=counts["field"],
                relationship_count=counts["relationship_hint"],
                content_count=counts["content_excerpt"],
                document_count=len(documents),
            )
            return {
                "documents": documents,
                "profile_status": status,
                "entity_statuses": entity_statuses,
            }
        finally:
            close = getattr(session.connector, "close", None)
            if callable(close):
                close()

    def sync_entity(self, profile_id: str, namespace: str, entity: str, *, job_id: str) -> dict[str, Any]:
        """Build discovery documents for a single entity within a profile."""
        session = self._runtime.connectors.for_profile(profile_id)
        try:
            self._runtime.connectors.ensure_entity_allowed(session.profile, namespace, entity)
            documents, counts = self._build_entity_documents(
                session,
                profile_id=profile_id,
                namespace=namespace,
                entity=entity,
            )
            status = EntityIndexStatus(
                profile_id=profile_id,
                namespace=namespace,
                entity=entity,
                last_job_id=job_id,
                last_job_status="succeeded",
                last_synced_at=self._now(),
                document_count=len(documents),
                field_count=counts["field"],
                relationship_count=counts["relationship_hint"],
                content_count=counts["content_excerpt"],
            )
            return {"documents": documents, "entity_status": status}
        finally:
            close = getattr(session.connector, "close", None)
            if callable(close):
                close()

    def _build_entity_documents(self, session, *, profile_id: str, namespace: str, entity: str) -> tuple[list[DiscoveryDocument], Counter[str]]:
        profile = session.profile
        detail = session.connector.describe_entity(namespace, entity)
        field_detail = session.connector.describe_fields(namespace, entity)
        relationships = session.connector.extract_relationships(namespace, entity)
        documents: list[DiscoveryDocument] = []
        counts: Counter[str] = Counter()

        fields = list(field_detail.get("fields", []))
        entity_body = (
            f"Entity {entity} in namespace {namespace}. "
            f"Document count {detail.get('document_count', 0)}. "
            f"Fields: {', '.join(str(field.get('name', '')) for field in fields)}"
        )
        documents.append(
            DiscoveryDocument(
                document_id=f"entity:{profile_id}:{namespace}:{entity}",
                profile_id=profile_id,
                namespace=namespace,
                entity=entity,
                doc_kind="entity",
                title=f"{entity} entity",
                keywords=self._keywords(namespace, entity, detail.get("entity", "")),
                body=entity_body,
                excerpt=entity_body,
                match_fields=["entity", "namespace"],
                payload={
                    "namespace": namespace,
                    "entity": entity,
                    "document_count": detail.get("document_count", 0),
                    "indexes": detail.get("indexes", []),
                },
            )
        )
        counts["entity"] += 1

        for field in fields:
            field_name = str(field.get("name", ""))
            type_names = [str(item) for item in field.get("types", [])]
            body = (
                f"Field {field_name} on {entity} in {namespace}. "
                f"Types: {', '.join(type_names) if type_names else 'unknown'}."
            )
            documents.append(
                DiscoveryDocument(
                    document_id=f"field:{profile_id}:{namespace}:{entity}:{field_name}",
                    profile_id=profile_id,
                    namespace=namespace,
                    entity=entity,
                    doc_kind="field",
                    title=f"{entity}.{field_name}",
                    keywords=self._keywords(namespace, entity, field_name, *type_names),
                    body=body,
                    excerpt=body,
                    match_fields=["field", "types"],
                    payload={
                        "namespace": namespace,
                        "entity": entity,
                        "field_name": field_name,
                        "types": type_names,
                    },
                )
            )
            counts["field"] += 1

        for relationship in relationships:
            field_name = str(relationship.get("field", ""))
            target_hint = str(relationship.get("target_entity_hint", "") or "")
            body = (
                f"Relationship hint for {entity}.{field_name} in {namespace}. "
                f"Target hint: {target_hint or 'unknown'}"
            )
            documents.append(
                DiscoveryDocument(
                    document_id=f"relationship:{profile_id}:{namespace}:{entity}:{field_name}",
                    profile_id=profile_id,
                    namespace=namespace,
                    entity=entity,
                    doc_kind="relationship_hint",
                    title=f"{entity}.{field_name} relationship",
                    keywords=self._keywords(namespace, entity, field_name, target_hint),
                    body=body,
                    excerpt=body,
                    related_entity=target_hint,
                    match_fields=["field", "target_entity_hint"],
                    payload={
                        "namespace": namespace,
                        "entity": entity,
                        "field": field_name,
                        "target_entity_hint": target_hint,
                        "relationship_type": relationship.get("relationship_type", "reference_candidate"),
                    },
                )
            )
            counts["relationship_hint"] += 1

        policy = self._index_policy(profile)
        if policy["enabled"] and policy["include_content"]:
            limit = int(policy["max_documents_per_entity"])
            rows = session.connector.read(namespace, entity, limit=limit)
            for row in rows:
                document = self._build_content_document(
                    profile=profile,
                    profile_id=profile_id,
                    namespace=namespace,
                    entity=entity,
                    row=row,
                    max_excerpt_chars=int(policy["max_excerpt_chars"]),
                    explicit_fields=[str(item) for item in policy["content_fields"]],
                )
                if document is not None:
                    documents.append(document)
                    counts["content_excerpt"] += 1

        return documents, counts

    def _build_content_document(
        self,
        *,
        profile: dict[str, Any],
        profile_id: str,
        namespace: str,
        entity: str,
        row: dict[str, Any],
        max_excerpt_chars: int,
        explicit_fields: list[str],
    ) -> DiscoveryDocument | None:
        row_id = str(row.get("_id", row.get("id", "")) or "")
        allowed_fields = []
        masks = set(profile.get("field_masks", {}).keys())
        exclusions = set(profile.get("field_exclusions", []))
        for key, value in row.items():
            if key in {"_id", "id"}:
                continue
            if key in exclusions or key in masks:
                continue
            if explicit_fields and key not in explicit_fields:
                continue
            if isinstance(value, str) and value.strip():
                allowed_fields.append((key, value.strip()))
        if not explicit_fields:
            allowed_fields = [item for item in allowed_fields if len(item[1]) <= max_excerpt_chars]
        if not allowed_fields:
            return None
        excerpt_parts = [f"{key}: {value}" for key, value in allowed_fields]
        excerpt = " | ".join(excerpt_parts)[:max_excerpt_chars]
        title = f"{entity} excerpt {row_id or 'row'}"
        return DiscoveryDocument(
            document_id=f"content:{profile_id}:{namespace}:{entity}:{row_id or md5(excerpt.encode('utf-8')).hexdigest()}",
            profile_id=profile_id,
            namespace=namespace,
            entity=entity,
            doc_kind="content_excerpt",
            title=title,
            keywords=self._keywords(namespace, entity, *(key for key, _ in allowed_fields)),
            body=excerpt,
            excerpt=excerpt,
            match_fields=[key for key, _ in allowed_fields],
            payload={
                "namespace": namespace,
                "entity": entity,
                "record_id": row_id,
                "indexed_fields": [key for key, _ in allowed_fields],
            },
        )

    def _build_profile_document(self, profile: dict[str, Any]) -> DiscoveryDocument:
        profile_id = str(profile.get("profile_id", ""))
        description = str(profile.get("description", "") or "")
        source_type = str(profile.get("source_type", "") or "")
        body = f"Profile {profile.get('name', profile_id)}. Source type {source_type}. {description}".strip()
        return DiscoveryDocument(
            document_id=f"profile:{profile_id}",
            profile_id=profile_id,
            namespace="",
            entity="",
            doc_kind="profile",
            title=str(profile.get("name", profile_id)),
            keywords=self._keywords(str(profile.get("name", "")), source_type),
            body=body,
            excerpt=body,
            match_fields=["name", "description", "source_type"],
            payload={
                "profile_id": profile_id,
                "name": profile.get("name", ""),
                "description": description,
                "source_type": source_type,
            },
        )

    def _build_namespace_document(self, profile_id: str, namespace: str, profile: dict[str, Any]) -> DiscoveryDocument:
        body = (
            f"Namespace {namespace} visible to profile {profile.get('name', profile_id)}. "
            f"Source type {profile.get('source_type', '')}."
        )
        return DiscoveryDocument(
            document_id=f"namespace:{profile_id}:{namespace}",
            profile_id=profile_id,
            namespace=namespace,
            entity="",
            doc_kind="namespace",
            title=namespace,
            keywords=self._keywords(namespace),
            body=body,
            excerpt=body,
            match_fields=["namespace"],
            payload={"profile_id": profile_id, "namespace": namespace},
        )

    def _index_policy(self, profile: dict[str, Any]) -> dict[str, Any]:
        policy = dict(profile.get("index_policy") or {})
        return {
            "enabled": bool(policy.get("enabled", True)),
            "include_content": bool(policy.get("include_content", True)),
            "content_fields": list(policy.get("content_fields", [])),
            "max_documents_per_entity": int(
                policy.get(
                    "max_documents_per_entity",
                    self._runtime.config.get("search.max_documents_per_entity", 10),
                )
            ),
            "max_excerpt_chars": int(
                policy.get(
                    "max_excerpt_chars",
                    self._runtime.config.get("search.max_excerpt_chars", 240),
                )
            ),
        }

    @staticmethod
    def _keywords(*parts: Any) -> str:
        tokens: list[str] = []
        for part in parts:
            text = str(part or "").strip()
            if not text:
                continue
            tokens.append(text)
            tokens.extend(normalise_search_terms(text))
            if text.endswith("s"):
                tokens.append(text[:-1])
            else:
                tokens.append(f"{text}s")
        return " ".join(token for token in tokens if token)

    @staticmethod
    def similarity_score(source_fields: list[str], candidate_fields: list[str]) -> tuple[int, list[str]]:
        """Return a simple overlap score between two field-name sets."""
        source = {field.lower() for field in source_fields if field.lower() not in _GENERIC_FIELD_TOKENS}
        candidate = {field.lower() for field in candidate_fields if field.lower() not in _GENERIC_FIELD_TOKENS}
        overlap = sorted(source.intersection(candidate))
        return len(overlap), overlap

    @staticmethod
    def resolve_target_entities(target_hint: str, entity_names: list[str]) -> list[str]:
        """Return candidate entity names that resemble a relationship target hint."""
        hint = target_hint.lower().strip()
        if not hint:
            return []
        matches = []
        for entity_name in entity_names:
            value = entity_name.lower().strip()
            variants = {value, value.rstrip("s"), f"{value}s"}
            hint_variants = {hint, hint.rstrip("s"), f"{hint}s"}
            if variants.intersection(hint_variants):
                matches.append(entity_name)
        return sorted(set(matches))

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()
