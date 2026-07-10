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
# Description: Database change-watch adapter over the common change-stream foundation.
# Related requirements: CSTREAM-DB-001, CSTREAM-DB-002 (PS-102 §4.4)

"""Database change-watch adapter (PS-102 §4.4, CSTREAM-DB-001/002).

``WatchService`` is a *thin adapter* over the common change-stream foundation
published in ``cloud_dog_api_kit.change_stream`` (PS-102 §9 / RULES §1.4). It:

* builds a :class:`~cloud_dog_api_kit.change_stream.WatchCoordinator` whose
  per-watch journal is the durable :class:`SqlJournal` (backed by the service's
  ``cloud_dog_db`` metadata engine) so a watch backlog survives restart
  (CSTREAM-007);
* wires the coordinator's ``on_emit`` hook to the service's
  ``cloud_dog_api_kit.a2a.events`` broadcaster via ``make_broadcast_hook`` for
  live SSE fan-out (PS-102 §5.2) — no bespoke broadcaster;
* wires the coordinator's ``audit_sink`` to ``cloud_dog_logging`` (CSTREAM-010);
* enforces RBAC/tenancy at the adapter boundary — a watch is scoped to a tenant
  + database profile; cross-tenant reads are a hard failure (CSTREAM-009);
* translates database mutations db-mcp itself performs (create/update/delete +
  schema-change) into the canonical :class:`ChangeEvent` envelope and emits them
  to every *live* watch whose criteria match (CSTREAM-DB-001/002).

Native database-CDC note (PS-102 §6, honest disposition)
--------------------------------------------------------
The native-first change-capture mechanism db-mcp uses is **server-mediated
capture**: the change is captured at the exact point db-mcp performs the
mutation through its connectors, so there is no polling, no busy-wait, and
transaction/commit ordering is preserved by the connector's own ``begin()``
transaction (the event is emitted only after the mutation commits). This is
genuine, ordered capture for every change that flows through db-mcp.

Database-native notification/log CDC (PostgreSQL LISTEN/NOTIFY + logical
decoding, MySQL/MariaDB binlog, MongoDB change streams, CouchDB ``_changes``)
would additionally capture *out-of-band* changes made by other clients directly
against the underlying database. Those mechanisms are **not** exposed by the
shared ``cloud_dog_db`` / ``cloud_dog_db.nosql`` data-access layer (its document,
search, and wide-column repositories expose only CRUD — no ``watch()`` /
``_changes`` / oplog / binlog / LISTEN-NOTIFY primitive; see
``NATIVE_CDC_SUPPORT`` below). RULES §1.4 / §6.88 forbid db-mcp reaching around
that layer to a direct driver (``pymongo``/``couchdb``/``elasticsearch``/
``opensearchpy``/``cassandra-driver``) to implement CDC itself. This adapter
therefore does not fabricate out-of-band CDC; ``NATIVE_CDC_SUPPORT`` records the
honest per-type disposition for the surface/health endpoints.
"""

from __future__ import annotations

import contextlib
import threading
import uuid
from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from typing import Any

from cloud_dog_api_kit.change_stream import (
    ACTIONS,
    ChangeEvent,
    WatchCoordinator,
    WatchSpec,
    make_broadcast_hook,
)
from cloud_dog_api_kit.change_stream.db_journal import SqlJournal
from cloud_dog_api_kit.change_stream.errors import (
    InvalidCriteria,
    WatchNotFound,
)
from cloud_dog_api_kit.change_stream.journal import InMemoryJournal, Journal

from src.core.change_stream.criteria import (
    ChangeCandidate,
    validate_criteria,
)
from src.core.change_stream.criteria import (
    match as criteria_match,
)

SERVICE_ID = "db-mcp"
_SOURCE_TYPE = "db_entity"

# The connector ``source_type`` a profile resolves to, keyed to its honest
# change-capture disposition (PS-102 §6 / CSTREAM-DB-003). ``server_mediated`` is
# proven end-to-end (changes that flow through db-mcp). ``native_capable`` marks
# a database engine that HAS a native notification/log CDC primitive that db-mcp
# does not yet expose because ``cloud_dog_db``/``cloud_dog_db.nosql`` provides no
# such primitive (RULES §1.4 / §6.88) — recorded truthfully, not faked.
NATIVE_CDC_SUPPORT: Mapping[str, Mapping[str, Any]] = {
    "postgresql": {
        "server_mediated": True,
        "native_mechanism": "LISTEN/NOTIFY + logical decoding",
        "native_available_via_cloud_dog_db": False,
    },
    "mariadb": {
        "server_mediated": True,
        "native_mechanism": "binlog row events",
        "native_available_via_cloud_dog_db": False,
    },
    "mongodb": {
        "server_mediated": True,
        "native_mechanism": "change streams",
        "native_available_via_cloud_dog_db": False,
    },
    "couchdb": {
        "server_mediated": True,
        "native_mechanism": "_changes feed",
        "native_available_via_cloud_dog_db": False,
    },
    "opensearch": {
        "server_mediated": True,
        "native_mechanism": "none (no first-class CDC)",
        "native_available_via_cloud_dog_db": False,
    },
    "elasticsearch": {
        "server_mediated": True,
        "native_mechanism": "none (no first-class CDC)",
        "native_available_via_cloud_dog_db": False,
    },
    "cassandra": {
        "server_mediated": True,
        "native_mechanism": "CDC commitlog (out-of-band tooling)",
        "native_available_via_cloud_dog_db": False,
    },
}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class WatchService:
    """Per-service change-watch adapter binding the common coordinator to DB ops.

    Args:
        service_id: stable service identifier for the envelope (``db-mcp``).
        engine: an optional SQLAlchemy ``Engine`` (the ``cloud_dog_db`` metadata
            engine). When supplied, watches journal durably via
            :class:`SqlJournal`; when ``None`` (unit tests / no DB) a bounded
            in-memory journal is used so the adapter still functions without a
            live database.
        broadcaster: an optional ``cloud_dog_api_kit.a2a.events`` broadcaster;
            when supplied, emitted events fan out live via ``make_broadcast_hook``.
        audit_sink: optional ``(kind, mapping)`` callable — the service wires
            ``cloud_dog_logging`` here.
        broadcast_scheduler: optional scheduler for the (async) broadcast publish
            so the sync emit path never blocks a request/worker (CSTREAM-002).
    """

    def __init__(
        self,
        *,
        service_id: str = SERVICE_ID,
        engine: Any | None = None,
        broadcaster: Any | None = None,
        audit_sink: Callable[[str, Mapping[str, Any]], None] | None = None,
        broadcast_scheduler: Callable[[Any], None] | None = None,
    ) -> None:
        self._service_id = service_id
        self._engine = engine
        self._lock = threading.RLock()
        # watch_id -> declarative spec view (tenant/profile/criteria) kept for
        # criteria evaluation + RBAC scoping. The coordinator owns state/journal.
        self._specs: dict[str, WatchSpec] = {}
        self._criteria: dict[str, Mapping[str, Any]] = {}

        on_emit = None
        if broadcaster is not None:
            on_emit = make_broadcast_hook(broadcaster, scheduler=broadcast_scheduler)

        # Ensure the durable journal table exists once (idempotent).
        if engine is not None:
            with contextlib.suppress(Exception):  # pragma: no cover - schema may already exist
                SqlJournal.create_schema(engine)

        self._coordinator = WatchCoordinator(
            journal_factory=self._journal_factory,
            on_emit=on_emit,
            audit_sink=audit_sink,
        )

    # ------------------------------------------------------------------
    # journal factory (durable SqlJournal, else bounded in-memory)
    # ------------------------------------------------------------------
    def _journal_factory(self, spec: WatchSpec) -> Journal:
        if self._engine is not None:
            return SqlJournal(
                self._engine,
                spec.watch_id,
                max_size=spec.journal_max,
                ttl_seconds=spec.journal_ttl_seconds,
            )
        return InMemoryJournal(max_size=spec.journal_max, ttl_seconds=spec.journal_ttl_seconds)

    @property
    def coordinator(self) -> WatchCoordinator:
        return self._coordinator

    @staticmethod
    def native_cdc_support() -> dict[str, dict[str, Any]]:
        """Return the honest per-source-type CDC disposition (PS-102 §6)."""
        return {k: dict(v) for k, v in NATIVE_CDC_SUPPORT.items()}

    # ------------------------------------------------------------------
    # RBAC / tenancy boundary (CSTREAM-009)
    # ------------------------------------------------------------------
    def _require_owner(self, watch_id: str, tenant_id: str) -> WatchSpec:
        """Return the spec if the caller's tenant owns the watch, else raise.

        Cross-tenant / cross-profile access is a hard failure — the watch is
        scoped to the tenant it was created under (PS-102 §7). Existence is not
        leaked across tenants: a mismatch reports not-found.
        """
        spec = self._specs.get(watch_id)
        if spec is None:
            raise WatchNotFound(f"no watch {watch_id!r}")
        if tenant_id is not None and spec.tenant_id != tenant_id:
            raise WatchNotFound(f"no watch {watch_id!r}")
        return spec

    # ------------------------------------------------------------------
    # lifecycle (create/list/status/pause/resume/delete) — PS-102 §5.1
    # ------------------------------------------------------------------
    def create_watch(
        self,
        *,
        profile_id: str,
        tenant_id: str,
        actor: str,
        criteria: Mapping[str, Any] | None = None,
        max_batch: int = 100,
        max_inflight: int = 4,
        journal_max: int = 1000,
        journal_ttl_seconds: float | None = None,
        watch_id: str | None = None,
    ) -> dict[str, Any]:
        resolved_criteria = dict(criteria or {})
        validate_criteria(resolved_criteria)
        if max_batch < 1 or max_inflight < 1 or journal_max < 1:
            raise InvalidCriteria("max_batch, max_inflight and journal_max must be >= 1")
        wid = watch_id or f"dbw-{uuid.uuid4().hex[:16]}"
        spec = WatchSpec(
            watch_id=wid,
            service_id=self._service_id,
            profile_id=profile_id,
            tenant_id=tenant_id,
            actor=actor,
            criteria=resolved_criteria,
            max_batch=max_batch,
            max_inflight=max_inflight,
            journal_max=journal_max,
            journal_ttl_seconds=journal_ttl_seconds,
        )
        with self._lock:
            status = self._coordinator.create_watch(spec)
            self._specs[wid] = spec
            self._criteria[wid] = resolved_criteria
        return self._watch_view(spec, status)

    def list_watches(self, *, tenant_id: str) -> list[dict[str, Any]]:
        with self._lock:
            out: list[dict[str, Any]] = []
            for wid, spec in self._specs.items():
                if spec.tenant_id != tenant_id:
                    continue
                out.append(self._watch_view(spec, self._coordinator.get_status(wid)))
            return out

    def get_watch(self, watch_id: str, *, tenant_id: str) -> dict[str, Any]:
        spec = self._require_owner(watch_id, tenant_id)
        return self._watch_view(spec, self._coordinator.get_status(watch_id))

    def get_status(self, watch_id: str, *, tenant_id: str) -> dict[str, Any]:
        self._require_owner(watch_id, tenant_id)
        return self._status_view(self._coordinator.get_status(watch_id))

    def pause(self, watch_id: str, *, tenant_id: str) -> dict[str, Any]:
        self._require_owner(watch_id, tenant_id)
        return self._status_view(self._coordinator.pause(watch_id))

    def resume(self, watch_id: str, *, tenant_id: str) -> dict[str, Any]:
        self._require_owner(watch_id, tenant_id)
        return self._status_view(self._coordinator.resume(watch_id))

    def delete(self, watch_id: str, *, tenant_id: str) -> dict[str, Any]:
        self._require_owner(watch_id, tenant_id)
        with self._lock:
            self._coordinator.delete(watch_id)
            self._specs.pop(watch_id, None)
            self._criteria.pop(watch_id, None)
        return {"watch_id": watch_id, "deleted": True}

    # ------------------------------------------------------------------
    # retrieval / ack / recover — PS-102 §5.2 (pull-batch base mode)
    # ------------------------------------------------------------------
    def get_batch(
        self,
        watch_id: str,
        *,
        tenant_id: str,
        since_cursor: str | None = None,
        max_batch: int | None = None,
    ) -> dict[str, Any]:
        self._require_owner(watch_id, tenant_id)
        result = self._coordinator.get_batch(watch_id, since_cursor=since_cursor, max_batch=max_batch)
        return WatchCoordinator.batch_to_dict(result, redact=True)

    def ack(self, watch_id: str, *, tenant_id: str, ack_cursor: str) -> dict[str, Any]:
        self._require_owner(watch_id, tenant_id)
        return self._status_view(self._coordinator.ack(watch_id, ack_cursor))

    def recover(
        self, watch_id: str, *, tenant_id: str, since_cursor: str | None = None
    ) -> dict[str, Any]:
        self._require_owner(watch_id, tenant_id)
        cursor = self._coordinator.recover(watch_id, since_cursor=since_cursor)
        return {"watch_id": watch_id, "resume_cursor": cursor}

    def test_event(
        self,
        watch_id: str,
        *,
        tenant_id: str,
        action: str = "created",
        object_ref: str = "test",
        **meta: Any,
    ) -> dict[str, Any]:
        """Inject a deterministic synthetic event (PS-102 §5.8)."""
        self._require_owner(watch_id, tenant_id)
        if action not in ACTIONS:
            raise InvalidCriteria(f"unknown action verb {action!r}")
        seq = self._coordinator.test_event(watch_id, action=action, object_ref=object_ref, **meta)
        return {"watch_id": watch_id, "emitted_seq": seq, "action": action, "object_ref": object_ref}

    # ------------------------------------------------------------------
    # health (PS-102 §5.9) — aggregated for the service /health
    # ------------------------------------------------------------------
    def health(self) -> dict[str, int]:
        with self._lock:
            return self._coordinator.health()

    # ------------------------------------------------------------------
    # domain-event capture (CSTREAM-DB-001) — called by the content tools after
    # a create/update/delete commits, and by schema changes after apply.
    # ------------------------------------------------------------------
    def observe_change(
        self,
        *,
        tenant_id: str,
        profile_id: str,
        source_type: str,
        namespace: str,
        entity: str,
        action: str,
        object_ref: str,
        object_version: str = "",
        values: Mapping[str, Any] | None = None,
        row_count: int | None = None,
        actor: str | None = None,
        correlation_id: str | None = None,
        summary: str = "",
    ) -> list[str]:
        """Fan a single observed DB change into every matching *live* watch.

        Returns the list of watch ids the change was emitted to (may be empty).
        This is the server-mediated capture path (PS-102 §6 native-first): the
        change is captured after db-mcp performs (and commits) the mutation, so
        there is no polling and no busy-wait; ordering follows the committing
        transaction.
        """
        if action not in ACTIONS:
            # Defensive: an unknown verb is a contract error, but capture must
            # never crash the mutating request path — skip silently.
            return []
        row_values = dict(values or {})
        candidate = ChangeCandidate(
            namespace=namespace,
            entity=entity,
            action=action,
            object_ref=object_ref,
            object_version=object_version,
            values=row_values,
        )
        emitted: list[str] = []
        # snapshot targets under lock; emit outside the lock is fine (coordinator
        # is single-process and its own emit is cheap + bounded).
        with self._lock:
            targets = [
                (wid, spec, self._criteria.get(wid, {}))
                for wid, spec in self._specs.items()
                if spec.tenant_id == tenant_id and spec.profile_id == profile_id
            ]
        for wid, spec, crit in targets:
            # only emit to live watches; a paused watch retains its cursor and is
            # not fed new events (PS-102 §5.1).
            status = self._coordinator.get_status(wid)
            if status.state != "live":
                continue
            matched = criteria_match(crit, candidate)
            if matched is None:
                continue
            event = self._build_event(
                spec=spec,
                source_type=source_type,
                candidate=candidate,
                criteria_match=matched,
                row_count=row_count,
                actor=actor,
                correlation_id=correlation_id,
                summary=summary,
            )
            try:
                self._coordinator.emit(wid, event)
                emitted.append(wid)
            except Exception:  # pragma: no cover - a paused/removed watch races
                continue
        return emitted

    # ------------------------------------------------------------------
    # envelope + view builders
    # ------------------------------------------------------------------
    def _build_event(
        self,
        *,
        spec: WatchSpec,
        source_type: str,
        candidate: ChangeCandidate,
        criteria_match: Mapping[str, Any],
        row_count: int | None,
        actor: str | None,
        correlation_id: str | None,
        summary: str,
    ) -> ChangeEvent:
        # per-service typed metadata extension (PS-102 §4.1 db-mcp row). Only
        # bounded, primitive scalar row values are carried; redaction is applied
        # by the journal/envelope before anything rests or is emitted.
        typed_metadata: dict[str, Any] = {
            "source_type": source_type,
            "namespace": candidate.namespace,
            "entity": candidate.entity,
            "capture": "server_mediated",
        }
        if row_count is not None:
            typed_metadata["row_count"] = int(row_count)
        scalar_values = {
            key: val
            for key, val in candidate.values.items()
            if isinstance(val, (str, int, float, bool)) and not isinstance(val, (bytes, bytearray))
        }
        if scalar_values:
            typed_metadata["values"] = scalar_values
        return ChangeEvent(
            watch_id=spec.watch_id,
            service_id=self._service_id,
            profile_id=spec.profile_id,
            source_type=_SOURCE_TYPE,
            source_ref=f"{spec.profile_id}:{candidate.namespace}.{candidate.entity}",
            action=candidate.action,
            object_ref=candidate.object_ref,
            object_version=candidate.object_version or candidate.object_ref,
            tenant_id=spec.tenant_id,
            event_time=_utc_now(),
            observed_time=_utc_now(),
            criteria_match=dict(criteria_match),
            summary=summary or _default_summary(candidate),
            metadata=typed_metadata,
            correlation_id=correlation_id,
            actor={"id": actor, "type": "user"} if actor else None,
            provenance={
                "capture": "server_mediated",
                "source_type": source_type,
                "namespace": candidate.namespace,
                "entity": candidate.entity,
            },
        )

    def _watch_view(self, spec: WatchSpec, status: Any) -> dict[str, Any]:
        return {
            "watch_id": spec.watch_id,
            "service_id": spec.service_id,
            "profile_id": spec.profile_id,
            "tenant_id": spec.tenant_id,
            "actor": spec.actor,
            "criteria": dict(spec.criteria),
            "max_batch": spec.max_batch,
            "max_inflight": spec.max_inflight,
            "journal_max": spec.journal_max,
            "journal_ttl_seconds": spec.journal_ttl_seconds,
            "status": self._status_view(status),
        }

    @staticmethod
    def _status_view(status: Any) -> dict[str, Any]:
        return {
            "watch_id": status.watch_id,
            "tenant_id": status.tenant_id,
            "state": status.state,
            "journal_depth": status.depth,
            "earliest_seq": status.earliest_seq,
            "latest_seq": status.latest_seq,
            "ack_seq": status.ack_seq,
            "inflight": status.inflight,
            "throttled": status.throttled,
            "trimmed_total": status.trimmed_total,
        }


def make_audit_sink(audit_logger: Any) -> Callable[[str, Mapping[str, Any]], None]:
    """Build a coordinator ``audit_sink`` that writes to ``cloud_dog_logging``.

    The common :class:`WatchCoordinator` calls ``audit_sink(kind, row)`` for every
    lifecycle / emission / delivery / ack / recover / throttle event (CSTREAM-010).
    This adapter maps each to the platform ``AuditLogger.log_crud`` so watch audit
    lands in the same privileged audit stream as the rest of the service — no
    bespoke audit writer (RULES §1.4).
    """
    from cloud_dog_logging import Actor, Target

    def _sink(kind: str, row: Mapping[str, Any]) -> None:
        watch_id = str(row.get("watch_id", ""))
        actor = str(row.get("actor") or "system")
        details = {k: v for k, v in row.items() if k not in {"watch_id", "actor"}}
        with contextlib.suppress(Exception):  # pragma: no cover - audit must never break the flow
            audit_logger.log_crud(
                actor=Actor(type="user", id=actor, roles=[]),
                action=f"change_watch.{kind}",
                target=Target(type="change_watch", id=watch_id or "-"),
                outcome="success",
                **({"detail": details} if details else {}),
            )

    return _sink


def _default_summary(candidate: ChangeCandidate) -> str:
    return f"{candidate.action} {candidate.namespace}.{candidate.entity}/{candidate.object_ref}".strip()
