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
# Description: Database change-watch criteria matching (PS-102 CSTREAM-DB-002).
# Related requirements: CSTREAM-DB-001, CSTREAM-DB-002

"""Database change-watch criteria matching (PS-102 CSTREAM-DB-002).

The criteria matcher is a *pure* function over a proposed :class:`ChangeCandidate`
(namespace + entity + action + optionally the changed row/document values) and a
watch's declarative ``criteria`` mapping. It decides whether an observed database
change matches a watch and, when it does, returns the ``criteria_match``
provenance the common
:class:`cloud_dog_api_kit.change_stream.ChangeEvent` envelope requires so a
consumer can prove the event is not a false positive (PS-102 §4).

Supported criteria fields (CSTREAM-DB-002):

* ``namespace`` — exact schema/database name (or list of names).
* ``entity`` — exact table/collection name (or list of names).
* ``entity_pattern`` — glob or ``re:`` regex over the table/collection name.
* ``action`` — one action verb or a list of verbs from the canonical set.
* ``value`` — mapping of column/field-key -> required value (exact or ``re:``);
  matched only against the *redacted-safe*, primitive scalar fields of the
  changed row when a row snapshot is available (never against binary/large
  values), so this criterion is safe and bounded.
* ``value_keys`` — list of column/field keys that MUST be present in the row.

No criterion means "match everything" (an unfiltered watch on the profile). This
module owns NO journal / cursor / queue logic — that all lives in the common
foundation (RULES §1.4).
"""

from __future__ import annotations

import fnmatch
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from cloud_dog_api_kit.change_stream import ACTIONS
from cloud_dog_api_kit.change_stream.errors import InvalidCriteria

_REGEX_PREFIX = "re:"

# Criteria keys this service understands (CSTREAM-DB-002). Unknown keys are a hard
# InvalidCriteria at watch-create time rather than a silent no-op.
_KNOWN_CRITERIA = frozenset(
    {
        "namespace",
        "entity",
        "entity_pattern",
        "action",
        "value",
        "value_keys",
    }
)

# Only primitive scalar row values are safe/bounded to evaluate value criteria
# against (binary/blob/nested payloads are excluded — never matched, never rest).
_SCALAR_TYPES = (str, int, float, bool)


@dataclass(frozen=True)
class ChangeCandidate:
    """A proposed database change evaluated against a watch's criteria.

    ``values`` is the changed row/document as a plain mapping of column/field ->
    value when a bounded snapshot is available (e.g. the created row or the
    ``$set`` payload); it may be empty for filter-scoped bulk updates/deletes
    where no per-row snapshot is captured. The candidate carries no secrets — the
    coordinator redacts metadata before it rests in the journal, and value
    criteria only ever look at primitive scalar fields.
    """

    namespace: str
    entity: str
    action: str
    object_ref: str
    object_version: str = ""
    values: Mapping[str, Any] = field(default_factory=dict)


def validate_criteria(criteria: Mapping[str, Any]) -> None:
    """Validate a watch's criteria mapping, raising ``InvalidCriteria`` on error.

    Called at watch-create time so an unsupported field / bad regex / unknown
    action verb is rejected *before* the watch starts (PS-102 §5.1).
    """
    if not isinstance(criteria, Mapping):
        raise InvalidCriteria("criteria must be a mapping")
    unknown = set(criteria) - _KNOWN_CRITERIA
    if unknown:
        raise InvalidCriteria(
            f"unsupported criteria field(s): {', '.join(sorted(unknown))}; "
            f"supported: {', '.join(sorted(_KNOWN_CRITERIA))}"
        )
    actions = criteria.get("action")
    if actions is not None:
        for verb in _as_list(actions):
            if verb not in ACTIONS:
                raise InvalidCriteria(
                    f"unknown action verb {verb!r}; valid: {', '.join(sorted(ACTIONS))}"
                )
    keys = criteria.get("value_keys")
    if keys is not None and not isinstance(keys, (list, tuple)):
        raise InvalidCriteria("value_keys must be a list of column/field key names")
    values = criteria.get("value")
    if values is not None and not isinstance(values, Mapping):
        raise InvalidCriteria("value criterion must be a mapping of key -> value")
    # compile the entity_pattern regex eagerly to surface a bad pattern now
    raw = criteria.get("entity_pattern")
    if isinstance(raw, str) and raw.startswith(_REGEX_PREFIX):
        _compile_regex(raw)
    if isinstance(values, Mapping):
        for value in values.values():
            if isinstance(value, str) and value.startswith(_REGEX_PREFIX):
                _compile_regex(value)


def match(criteria: Mapping[str, Any], candidate: ChangeCandidate) -> dict[str, Any] | None:
    """Return a ``criteria_match`` mapping if the candidate matches, else ``None``.

    An empty ``criteria`` mapping matches everything and returns ``{"all": True}``
    so the envelope's ``criteria_match`` is never empty (CSTREAM-004). When any
    criterion fails, the whole watch does NOT match and ``None`` is returned.
    """
    if not criteria:
        return {"all": True}

    matched: dict[str, Any] = {}

    if "namespace" in criteria:
        wanted = _as_list(criteria["namespace"])
        if candidate.namespace not in wanted:
            return None
        matched["namespace"] = candidate.namespace

    if "entity" in criteria:
        wanted = _as_list(criteria["entity"])
        if candidate.entity not in wanted:
            return None
        matched["entity"] = candidate.entity

    if "entity_pattern" in criteria:
        hit = _text_match(str(criteria["entity_pattern"]), candidate.entity)
        if hit is None:
            return None
        matched["entity_pattern"] = candidate.entity

    if "action" in criteria:
        wanted = _as_list(criteria["action"])
        if candidate.action not in wanted:
            return None
        matched["action"] = candidate.action

    scalars = _scalar_values(candidate.values)

    if "value_keys" in criteria:
        required = [str(k) for k in _as_list(criteria["value_keys"])]
        missing = [k for k in required if k not in scalars]
        if missing:
            return None
        matched["value_keys"] = required

    if "value" in criteria:
        wanted_values = criteria["value"]
        matched_values: dict[str, Any] = {}
        for key, expected in wanted_values.items():
            if key not in scalars:
                return None
            actual = scalars[key]
            if isinstance(expected, str) and expected.startswith(_REGEX_PREFIX):
                if _text_match(expected, str(actual)) is None:
                    return None
            elif str(actual) != str(expected):
                return None
            matched_values[key] = actual
        matched["value"] = matched_values

    return matched


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _as_list(value: Any) -> list[Any]:
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]


def _scalar_values(values: Mapping[str, Any]) -> dict[str, Any]:
    """Return only the primitive scalar row fields, safe/bounded for matching."""
    if not isinstance(values, Mapping):
        return {}
    return {
        str(key): val
        for key, val in values.items()
        if isinstance(val, _SCALAR_TYPES) and not isinstance(val, (bytes, bytearray))
    }


def _compile_regex(raw: str) -> re.Pattern[str]:
    pattern = raw[len(_REGEX_PREFIX):]
    try:
        return re.compile(pattern)
    except re.error as exc:
        raise InvalidCriteria(f"invalid regex {pattern!r}: {exc}") from exc


def _text_match(pattern: str, value: str) -> str | None:
    """Return the matched value/substring when ``pattern`` matches ``value``.

    ``re:`` prefix -> regex ``search``; otherwise a case-sensitive ``fnmatch``
    glob. Returns ``None`` on no match.
    """
    if pattern.startswith(_REGEX_PREFIX):
        compiled = _compile_regex(pattern)
        m = compiled.search(value or "")
        return m.group(0) if m is not None else None
    if fnmatch.fnmatchcase(value or "", pattern):
        return value
    return None
