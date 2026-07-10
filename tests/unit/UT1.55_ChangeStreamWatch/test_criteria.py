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
# Description: UT1.55 — database change-watch criteria matching.
# Related requirements: CSTREAM-DB-002
# Related tests: UT1.55

"""UT1.55 — database change-watch criteria matching (PS-102 CSTREAM-DB-002)."""

from __future__ import annotations

import pytest

from cloud_dog_api_kit.change_stream.errors import InvalidCriteria
from src.core.change_stream.criteria import ChangeCandidate, match, validate_criteria

pytestmark = [pytest.mark.unit, pytest.mark.UT, pytest.mark.internal]


def _candidate(**kw) -> ChangeCandidate:
    base = dict(namespace="public", entity="orders", action="created", object_ref="1")
    base.update(kw)
    return ChangeCandidate(**base)


@pytest.mark.req("CSTREAM-DB-002")
def test_empty_criteria_matches_everything() -> None:
    assert match({}, _candidate()) == {"all": True}


@pytest.mark.req("CSTREAM-DB-002")
def test_namespace_and_entity_exact_match() -> None:
    got = match({"namespace": "public", "entity": "orders"}, _candidate())
    assert got == {"namespace": "public", "entity": "orders"}
    assert match({"entity": "users"}, _candidate()) is None
    assert match({"namespace": "reporting"}, _candidate()) is None


@pytest.mark.req("CSTREAM-DB-002")
def test_entity_list_and_pattern() -> None:
    assert match({"entity": ["orders", "users"]}, _candidate()) is not None
    assert match({"entity_pattern": "ord*"}, _candidate()) == {"entity_pattern": "orders"}
    assert match({"entity_pattern": "re:^ord"}, _candidate()) is not None
    assert match({"entity_pattern": "user*"}, _candidate()) is None


@pytest.mark.req("CSTREAM-DB-002")
def test_action_filter() -> None:
    assert match({"action": "created"}, _candidate(action="created")) is not None
    assert match({"action": ["updated", "deleted"]}, _candidate(action="created")) is None


@pytest.mark.req("CSTREAM-DB-002")
def test_value_criteria_exact_and_regex() -> None:
    cand = _candidate(values={"status": "shipped", "region": "eu"})
    assert match({"value": {"status": "shipped"}}, cand) == {"value": {"status": "shipped"}}
    assert match({"value": {"status": "pending"}}, cand) is None
    assert match({"value": {"region": "re:^e"}}, cand) is not None
    assert match({"value_keys": ["status", "region"]}, cand) is not None
    assert match({"value_keys": ["missing"]}, cand) is None


@pytest.mark.req("CSTREAM-DB-002")
def test_value_criteria_never_matches_binary_or_missing_snapshot() -> None:
    # Binary / non-scalar row values are excluded from value matching (safe/bounded).
    cand = _candidate(values={"blob": b"\x00\x01", "big": {"nested": 1}})
    assert match({"value_keys": ["blob"]}, cand) is None
    assert match({"value": {"blob": "x"}}, cand) is None
    # A filter-scoped bulk update has no per-row snapshot -> value criteria never match.
    assert match({"value": {"status": "x"}}, _candidate(values={})) is None


@pytest.mark.req("CSTREAM-DB-002")
def test_validate_rejects_unknown_field_and_bad_regex_and_action() -> None:
    with pytest.raises(InvalidCriteria):
        validate_criteria({"nope": 1})
    with pytest.raises(InvalidCriteria):
        validate_criteria({"entity_pattern": "re:([unclosed"})
    with pytest.raises(InvalidCriteria):
        validate_criteria({"action": "exploded"})
    with pytest.raises(InvalidCriteria):
        validate_criteria({"value": "not-a-mapping"})
    # valid criteria pass silently
    validate_criteria({"namespace": "public", "entity": ["a", "b"], "action": ["created", "updated"], "value": {"k": "re:v"}})
