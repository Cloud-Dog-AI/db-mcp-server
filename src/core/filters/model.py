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
# Description: Structured filter model and parser for connector-safe query input.
# Related requirements: CO-01, NF-01, CN-01
# Related tests: UT1.5, ST1.5, IT1.3, IT1.4

"""Structured filter model and parsing helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from cloud_dog_api_kit.errors import ValidationError

SUPPORTED_OPERATORS = {
    "eq",
    "neq",
    "gt",
    "gte",
    "lt",
    "lte",
    "in",
    "not_in",
    "contains",
    "starts_with",
    "ends_with",
    "exists",
    "not_exists",
    "regex",
    "is_null",
    "is_not_null",
}
SUPPORTED_GROUP_OPS = {"and", "or", "not"}


@dataclass(slots=True)
class FilterCondition:
    """Single structured filter condition."""

    field: str
    operator: str
    value: Any = None


@dataclass(slots=True)
class FilterGroup:
    """Logical group of filter conditions or nested groups."""

    op: str
    conditions: list[FilterCondition | FilterGroup]


FilterNode = FilterCondition | FilterGroup


def parse_filter(raw: dict[str, Any] | None) -> FilterNode:
    """Parse a raw JSON-like payload into a structured filter node.

    Backwards compatibility:
    - `None` or `{}` becomes an empty `and` group.
    - Plain mapping filters such as `{"status": "active"}` are accepted and
      converted into equality conditions.
    """
    if raw is None or raw == {}:
        return FilterGroup(op="and", conditions=[])
    if not isinstance(raw, dict):
        raise ValidationError(message="Structured filter must be a JSON object")
    if "op" in raw:
        return _parse_group(raw)
    if "field" in raw and "operator" in raw:
        return _parse_condition(raw)
    return FilterGroup(
        op="and",
        conditions=[
            FilterCondition(field=str(key), operator="eq", value=value)
            for key, value in raw.items()
        ],
    )


def _parse_group(raw: dict[str, Any]) -> FilterGroup:
    op = str(raw.get("op", "")).lower().strip()
    if op not in SUPPORTED_GROUP_OPS:
        raise ValidationError(message=f"Unsupported filter group operator: {op}")
    raw_conditions = raw.get("conditions", [])
    if not isinstance(raw_conditions, list):
        raise ValidationError(message="Filter group conditions must be a list")
    conditions = [parse_filter(item) for item in raw_conditions]
    if op == "not" and len(conditions) != 1:
        raise ValidationError(message="Filter group operator 'not' requires exactly one condition")
    return FilterGroup(op=op, conditions=conditions)


def _parse_condition(raw: dict[str, Any]) -> FilterCondition:
    field = str(raw.get("field", "")).strip()
    operator = str(raw.get("operator", "")).lower().strip()
    if not field:
        raise ValidationError(message="Filter condition field is required")
    if operator not in SUPPORTED_OPERATORS:
        raise ValidationError(message=f"Unsupported filter operator: {operator}")
    return FilterCondition(field=field, operator=operator, value=raw.get("value"))
