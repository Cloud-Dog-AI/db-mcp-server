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
# Description: Unit tests for structured filter parsing and Mongo translation.
# Related requirements: CO-01, NF-01, CN-01
# Related tests: UT1.5

from __future__ import annotations

import pytest

from cloud_dog_api_kit.errors import ValidationError

from src.core.filters import FilterCondition, FilterGroup, MongoDBFilterTranslator, parse_filter

pytestmark = [pytest.mark.unit]
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.probe  # W28C-1711-R3.5 invalid-binding archived (NF-001)


def test_parse_filter_accepts_legacy_mapping_and_nested_groups() -> None:
    legacy = parse_filter({"status": "active", "country": "UK"})
    assert isinstance(legacy, FilterGroup)
    assert len(legacy.conditions) == 2

    nested = parse_filter(
        {
            "op": "and",
            "conditions": [
                {"field": "status", "operator": "eq", "value": "active"},
                {
                    "op": "or",
                    "conditions": [
                        {"field": "country", "operator": "eq", "value": "UK"},
                        {"field": "country", "operator": "eq", "value": "US"},
                    ],
                },
            ],
        }
    )
    assert isinstance(nested, FilterGroup)
    assert nested.op == "and"
    assert isinstance(nested.conditions[0], FilterCondition)
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.probe  # W28C-1711-R3.5 invalid-binding archived (NF-001)


def test_translate_filter_to_mongodb_query() -> None:
    translator = MongoDBFilterTranslator()
    node = parse_filter(
        {
            "op": "and",
            "conditions": [
                {"field": "status", "operator": "eq", "value": "active"},
                {"field": "quantity", "operator": "gte", "value": 20},
                {
                    "op": "or",
                    "conditions": [
                        {"field": "country", "operator": "eq", "value": "UK"},
                        {"field": "country", "operator": "starts_with", "value": "U"},
                    ],
                },
            ],
        }
    )
    assert translator.translate(node) == {
        "$and": [
            {"status": "active"},
            {"quantity": {"$gte": 20}},
            {"$or": [{"country": "UK"}, {"country": {"$regex": "^U"}}]},
        ]
    }
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.probe  # W28C-1711-R3.5 invalid-binding archived (NF-001)


def test_filter_parser_rejects_invalid_input() -> None:
    with pytest.raises(ValidationError):
        parse_filter({"op": "xor", "conditions": []})
    with pytest.raises(ValidationError):
        parse_filter({"field": "name", "operator": "unknown", "value": "x"})
    with pytest.raises(ValidationError):
        parse_filter({"op": "not", "conditions": []})
