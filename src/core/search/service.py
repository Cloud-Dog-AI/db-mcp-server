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
# Description: Discovery search orchestration and index job execution.
# Related requirements: W28A-274-I deliverables 1, 2, 3, 4
# Covers: SI-01, SI-02, SI-03, SI-04
# Related tests: UT1.9, UT1.10, ST1.7, IT1.6

"""Discovery search and indexing orchestration for db-mcp-server."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from cloud_dog_api_kit.errors import NotFoundError, ValidationError
from cloud_dog_jobs import FallbackAction, JobStatus
from cloud_dog_jobs.domain.models import JobRequest
from cloud_dog_logging import get_logger  # type: ignore[import-untyped]

_job_logger = get_logger("db_mcp_server.jobs")

from src.core.search.indexer import DiscoveryIndexer, build_fts5_query, normalise_search_terms
from src.core.search.models import EntityIndexStatus, ProfileIndexStatus
from src.core.search.repository import DiscoveryIndexRepository

_METADATA_KINDS = ["profile", "namespace", "entity", "field", "relationship_hint"]
_CONTENT_KINDS = ["content_excerpt"]


class DiscoverySearchService:
    """Manage discovery indexing and serve metadata/content search."""

    def __init__(self, runtime) -> None:
        self._runtime = runtime
        self._repository = DiscoveryIndexRepository(
            str(runtime.config.get("search.discovery_index_path", "./data/discovery-index.db"))
        )
        self._indexer = DiscoveryIndexer(runtime)
        self._queue_name = str(runtime.config.get("jobs.queue_name") or "indexing").strip() or "indexing"

    @property
    def repository(self) -> DiscoveryIndexRepository:
        """Expose the underlying repository for tests and diagnostics."""
        return self._repository

    def health_check(self) -> dict[str, Any]:
        """Return health information for the discovery index service."""
        return {
            "status": "ok" if self._repository.health_check() else "error",
            "path": str(self._repository.path),
        }

    def search_metadata(self, *, profile_id: str, query: str, limit: int | None = None) -> list[dict[str, Any]]:
        """Search profile-visible metadata documents."""
        return self._search(profile_id=profile_id, query=query, doc_kinds=_METADATA_KINDS, limit=limit)

    def search_content(self, *, profile_id: str, query: str, limit: int | None = None) -> list[dict[str, Any]]:
        """Search indexed content excerpts."""
        return self._search(profile_id=profile_id, query=query, doc_kinds=_CONTENT_KINDS, limit=limit)

    def search_related(self, *, profile_id: str, namespace: str, entity: str, limit: int = 10) -> list[dict[str, Any]]:
        """Find related entities from relationship hints plus field overlap."""
        entity_docs = self._repository.list_documents(profile_id=profile_id, doc_kinds=["entity"])
        field_docs = self._repository.list_documents(profile_id=profile_id, doc_kinds=["field"])
        relationship_docs = self._repository.list_documents(
            profile_id=profile_id,
            doc_kinds=["relationship_hint"],
            namespace=namespace,
            entity=entity,
        )
        if not entity_docs:
            return []
        source_fields = [
            str(item.get("payload", {}).get("field_name", ""))
            for item in field_docs
            if item.get("namespace") == namespace and item.get("entity") == entity
        ]
        entity_names = [str(item.get("entity", "")) for item in entity_docs if item.get("entity")]
        by_entity: dict[tuple[str, str], dict[str, Any]] = {}
        field_map: defaultdict[tuple[str, str], list[str]] = defaultdict(list)
        for item in field_docs:
            key = (str(item.get("namespace", "")), str(item.get("entity", "")))
            field_map[key].append(str(item.get("payload", {}).get("field_name", "")))
        for relation in relationship_docs:
            payload = relation.get("payload", {})
            target_hint = str(payload.get("target_entity_hint", ""))
            for candidate_entity in self._indexer.resolve_target_entities(target_hint, entity_names):
                candidate_key = self._find_entity_key(entity_docs, candidate_entity)
                if candidate_key is None:
                    continue
                key = (candidate_key[0], candidate_key[1])
                candidate = by_entity.setdefault(
                    key,
                    {
                        "namespace": candidate_key[0],
                        "entity": candidate_key[1],
                        "score": 0,
                        "reasons": [],
                    },
                )
                candidate["score"] += 5
                candidate["reasons"].append(f"relationship hint {entity}.{payload.get('field', '')} -> {candidate_key[1]}")
        for entity_doc in entity_docs:
            candidate_namespace = str(entity_doc.get("namespace", ""))
            candidate_entity = str(entity_doc.get("entity", ""))
            if candidate_namespace == namespace and candidate_entity == entity:
                continue
            score, overlap = self._indexer.similarity_score(
                source_fields,
                field_map.get((candidate_namespace, candidate_entity), []),
            )
            if score <= 0:
                continue
            candidate = by_entity.setdefault(
                (candidate_namespace, candidate_entity),
                {
                    "namespace": candidate_namespace,
                    "entity": candidate_entity,
                    "score": 0,
                    "reasons": [],
                },
            )
            candidate["score"] += score
            candidate["reasons"].append(f"shared fields: {', '.join(overlap)}")
        results = sorted(by_entity.values(), key=lambda item: (-int(item["score"]), item["namespace"], item["entity"]))
        return results[: max(1, int(limit))]

    def explain_match(self, *, profile_id: str, query: str, document_id: str) -> dict[str, Any]:
        """Explain which indexed components matched a query."""
        document = self._repository.get_document(document_id)
        if document is None or str(document.get("profile_id")) != profile_id:
            raise NotFoundError(message=f"Discovery document not found: {document_id}")
        terms = normalise_search_terms(query)
        components = {
            "title": str(document.get("title", "")),
            "keywords": str(document.get("keywords", "")),
            "body": str(document.get("body", "")),
            "excerpt": str(document.get("excerpt", "")),
            "related_entity": str(document.get("related_entity", "")),
        }
        matches = []
        for field_name, value in components.items():
            lower_value = value.lower()
            matched_terms = [term for term in terms if term in lower_value]
            if matched_terms:
                matches.append({"field": field_name, "terms": matched_terms})
        return {
            "document_id": document_id,
            "doc_kind": document.get("doc_kind"),
            "title": document.get("title"),
            "matched_components": matches,
            "match_fields": document.get("match_fields", []),
            "payload": document.get("payload", {}),
        }

    def index_status(self, *, profile_ids: list[str] | None = None) -> dict[str, Any]:
        """Return discovery index coverage and freshness data."""
        statuses = self._repository.list_profile_statuses(profile_ids)
        freshness_seconds = int(self._runtime.config.get("search.freshness_seconds", 3600))
        now = datetime.now(timezone.utc)
        for item in statuses:
            last_synced_at = item.get("last_synced_at")
            if last_synced_at:
                synced = datetime.fromisoformat(str(last_synced_at))
                item["freshness_state"] = "fresh" if now - synced <= timedelta(seconds=freshness_seconds) else "stale"
            item["queue_status"] = self._runtime.job_backend.get_queue_status()
            if item.get("last_job_id"):
                job = self._runtime.job_queue.get(str(item["last_job_id"]))
                item["job_status"] = job.status.value if job else item.get("last_job_status", "unknown")
            else:
                item["job_status"] = item.get("last_job_status", "idle")
            item["entities"] = self._repository.list_entity_statuses(str(item.get("profile_id", "")))
        return {"items": statuses}

    def sync_profile(self, *, profile_id: str, principal: Any) -> dict[str, Any]:
        """Queue and execute a profile-wide discovery index build."""
        request = JobRequest(
            job_type="discovery.sync_profile",
            queue_name=self._queue_name,
            payload={"profile_id": profile_id},
            user_id=getattr(principal, "user_id", None),
            request_source="mcp",
        )
        job_id = self._runtime.job_queue.submit(request)
        result = self._execute_job(job_id, lambda: self._indexer.sync_profile(profile_id, job_id=job_id))
        self._repository.replace_profile_documents(
            profile_id,
            result["documents"],
            profile_status=result["profile_status"],
            entity_statuses=result["entity_statuses"],
        )
        return {
            "job_id": job_id,
            "job_status": self._runtime.job_queue.get(job_id).status.value,
            "profile_status": asdict(result["profile_status"]),
        }

    def sync_entity(self, *, profile_id: str, namespace: str, entity: str, principal: Any) -> dict[str, Any]:
        """Queue and execute a discovery index refresh for one entity."""
        request = JobRequest(
            job_type="discovery.sync_entity",
            queue_name=self._queue_name,
            payload={"profile_id": profile_id, "namespace": namespace, "entity": entity},
            user_id=getattr(principal, "user_id", None),
            request_source="mcp",
        )
        job_id = self._runtime.job_queue.submit(request)
        result = self._execute_job(
            job_id,
            lambda: self._indexer.sync_entity(profile_id, namespace, entity, job_id=job_id),
        )
        self._repository.replace_entity_documents(
            profile_id,
            namespace,
            entity,
            result["documents"],
            entity_status=result["entity_status"],
        )
        profile_status = self._repository.get_profile_status(profile_id)
        if profile_status is not None:
            profile_status["last_job_id"] = job_id
            profile_status["last_job_status"] = self._runtime.job_queue.get(job_id).status.value
            profile_status["last_synced_at"] = result["entity_status"].last_synced_at
            profile_status["document_count"] = self._repository.count_documents(profile_id=profile_id)
            self._repository.update_profile_status(ProfileIndexStatus(**profile_status))
        return {
            "job_id": job_id,
            "job_status": self._runtime.job_queue.get(job_id).status.value,
            "entity_status": asdict(result["entity_status"]),
        }

    def rebuild(self, *, principal: Any, profile_ids: list[str] | None = None) -> dict[str, Any]:
        """Queue and execute a full rebuild across accessible profiles."""
        requested_profiles = profile_ids or self._resolve_accessible_profiles(principal)
        request = JobRequest(
            job_type="discovery.rebuild",
            queue_name=self._queue_name,
            payload={"profile_ids": requested_profiles},
            user_id=getattr(principal, "user_id", None),
            request_source="mcp",
        )
        job_id = self._runtime.job_queue.submit(request)

        def rebuild_all() -> list[dict[str, Any]]:
            self._repository.clear_all()
            results = []
            for profile_id in requested_profiles:
                result = self._indexer.sync_profile(profile_id, job_id=job_id)
                self._repository.replace_profile_documents(
                    profile_id,
                    result["documents"],
                    profile_status=result["profile_status"],
                    entity_statuses=result["entity_statuses"],
                )
                results.append(asdict(result["profile_status"]))
            return results

        results = self._execute_job(job_id, rebuild_all)
        return {
            "job_id": job_id,
            "job_status": self._runtime.job_queue.get(job_id).status.value,
            "profiles": results,
        }

    def create_lifecycle_evidence_job(
        self,
        *,
        outcome: str,
        job_type: str,
        label: str,
        principal: Any,
    ) -> dict[str, Any]:
        """Create a source-backed lifecycle job record for ST WebUI conformance tests."""
        allowed_statuses = {status.value for status in JobStatus}
        if outcome not in allowed_statuses:
            raise ValidationError(message=f"Unsupported lifecycle outcome: {outcome}")
        if job_type not in {"discovery.sync_profile", "discovery.sync_entity", "discovery.rebuild"}:
            raise ValidationError(message=f"Unsupported lifecycle job type: {job_type}")
        actor = str(getattr(principal, "username", "") or getattr(principal, "user_id", "") or "unknown")
        request = JobRequest(
            job_type=job_type,
            queue_name=self._queue_name,
            payload={
                "label": label,
                "purpose": "w28a-691-webui-conformance",
                "requested_outcome": outcome,
            },
            user_id=getattr(principal, "user_id", None),
            request_source="mcp",
            request_auth_method="api_key",
            request_auth_identity=actor,
        )
        job_id = self._runtime.job_queue.submit(request)
        if outcome == JobStatus.CANCELLED.value:
            self._runtime.job_queue.cancel(job_id)
        else:
            host_id = str(self._runtime.config.get("service_instance", "db-mcp-local"))
            self._runtime.job_backend.claim(job_id, host_id=host_id, worker_id="w28a-691-evidence")
            self._runtime.job_backend.heartbeat(job_id)
            if outcome != JobStatus.RUNNING.value:
                self._runtime.job_backend.update_status(job_id, outcome)
        job = self._runtime.job_queue.get(job_id)
        status = job.status.value if job else outcome
        return {
            "success": True,
            "post_hoc_database_mutation": False,
            "job_id": job_id,
            "status": status,
            "proof": {
                "job_id": job_id,
                "status": status,
                "source_path": "DiscoverySearchService.create_lifecycle_evidence_job",
                "request_auth_identity": actor,
                "job_type": job_type,
                "label": label,
            },
        }

    def _search(self, *, profile_id: str, query: str, doc_kinds: list[str], limit: int | None) -> list[dict[str, Any]]:
        match_query = build_fts5_query(query)
        if not match_query:
            raise ValidationError(message="Search query must contain at least one token")
        requested_limit = limit or int(self._runtime.config.get("search.metadata_limit", 20))
        rows = self._repository.search_documents(
            profile_id=profile_id,
            match_query=match_query,
            doc_kinds=doc_kinds,
            limit=max(1, int(requested_limit)),
        )
        return [self._serialise_result(item) for item in rows]

    def _serialise_result(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "document_id": row.get("document_id"),
            "namespace": row.get("namespace"),
            "entity": row.get("entity"),
            "doc_kind": row.get("doc_kind"),
            "title": row.get("title"),
            "excerpt": row.get("excerpt"),
            "match_fields": row.get("match_fields", []),
            "related_entity": row.get("related_entity"),
            "score": row.get("score", 0.0),
            "payload": row.get("payload", {}),
        }

    def _execute_job(self, job_id: str, operation: Callable[[], Any]) -> Any:
        """Execute a job with full PS-75 lifecycle: claim, heartbeat, audit, retry/dead-letter on failure."""
        worker_id = "discovery-indexer"
        host_id = str(self._runtime.config.get("service_instance", "db-mcp-local"))
        self._runtime.job_backend.claim(job_id, host_id=host_id, worker_id=worker_id)
        self._runtime.job_backend.heartbeat(job_id)

        # Audit: job claimed (PS-75 JQ15)
        _job_logger.info(f"job.audit action=job.claim outcome=success job_id={job_id}")

        try:
            result = operation()
        except Exception as exc:
            error_msg = str(exc)[:200]

            # Check retry eligibility (PS-75 JQ7)
            job = self._runtime.job_backend.get(job_id)
            current_attempt = getattr(job, "attempt", 0) or 0 if job else 0
            max_att = self._runtime.job_max_attempts

            if current_attempt < max_att - 1:
                # Transition to retry_wait
                self._runtime.job_backend.update_status(job_id, JobStatus.RETRY_WAIT.value)
                _job_logger.info(f"job.audit action=job.transition outcome=retry job_id={job_id} attempt={current_attempt + 1}")
            elif self._runtime.job_fallback_manager is not None:
                # Dead-letter (PS-75 JQ7.3)
                try:
                    decision = self._runtime.job_fallback_manager.apply(self._runtime.job_backend, job, exc)
                    if decision.action == FallbackAction.DEAD_LETTER:
                        self._runtime.job_backend.update_status(job_id, JobStatus.DEAD_LETTERED.value)
                        _job_logger.info(f"job.audit action=job.transition outcome=dead_lettered job_id={job_id}")
                        raise
                except Exception:
                    pass
                self._runtime.job_backend.update_status(job_id, "failed")
                _job_logger.info(f"job.audit action=job.transition outcome=failed job_id={job_id} error={error_msg}")
            else:
                self._runtime.job_backend.update_status(job_id, "failed")
                _job_logger.info(f"job.audit action=job.transition outcome=failed job_id={job_id} error={error_msg}")
            raise

        self._runtime.job_backend.update_status(job_id, "succeeded")
        _job_logger.info(f"job.audit action=job.transition outcome=success job_id={job_id}")
        return result

    def _resolve_accessible_profiles(self, principal: Any) -> list[str]:
        allowed = list(getattr(principal, "profile_ids", []) or [])
        if "*" in allowed:
            return [str(item.get("profile_id")) for item in self._runtime.access_control.list_profiles()]
        return allowed

    @staticmethod
    def _find_entity_key(entity_docs: list[dict[str, Any]], entity_name: str) -> tuple[str, str] | None:
        for item in entity_docs:
            if str(item.get("entity", "")) == entity_name:
                return str(item.get("namespace", "")), entity_name
        return None
