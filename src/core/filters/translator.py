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
# Description: Connector-specific structured filter translators.
# Related requirements: CO-01, NF-01, CN-01
# Related tests: UT1.5, ST1.5, IT1.3, IT1.4

"""Structured filter translators."""

from __future__ import annotations

import re
from typing import Any, Protocol

from cloud_dog_api_kit.errors import ValidationError

from src.core.filters.model import FilterCondition, FilterGroup, FilterNode


class FilterTranslator(Protocol):
    """Connector contract for structured filter translation."""

    def translate(self, filter_node: FilterNode) -> Any:
        """Translate a structured filter node to a connector-native query."""


class MongoDBFilterTranslator:
    """Translate structured filter nodes into `pymongo` query documents."""

    def translate(self, filter_node: FilterNode) -> dict[str, Any]:
        if isinstance(filter_node, FilterCondition):
            return self._translate_condition(filter_node)
        return self._translate_group(filter_node)

    def _translate_group(self, group: FilterGroup) -> dict[str, Any]:
        translated = [self.translate(item) for item in group.conditions]
        translated = [item for item in translated if item not in ({}, None)]
        if not translated:
            return {}
        if group.op == "and":
            if len(translated) == 1:
                return translated[0]
            return {"$and": translated}
        if group.op == "or":
            return {"$or": translated}
        if group.op == "not":
            return {"$nor": translated}
        raise ValidationError(message=f"Unsupported filter group operator: {group.op}")

    def _translate_condition(self, condition: FilterCondition) -> dict[str, Any]:
        field = condition.field
        operator = condition.operator
        value = condition.value
        if operator == "eq":
            return {field: value}
        if operator == "neq":
            return {field: {"$ne": value}}
        if operator == "gt":
            return {field: {"$gt": value}}
        if operator == "gte":
            return {field: {"$gte": value}}
        if operator == "lt":
            return {field: {"$lt": value}}
        if operator == "lte":
            return {field: {"$lte": value}}
        if operator == "in":
            return {field: {"$in": list(value or [])}}
        if operator == "not_in":
            return {field: {"$nin": list(value or [])}}
        if operator == "contains":
            return {field: {"$regex": re.escape(str(value or ""))}}
        if operator == "starts_with":
            return {field: {"$regex": f"^{re.escape(str(value or ''))}"}}
        if operator == "ends_with":
            return {field: {"$regex": f"{re.escape(str(value or ''))}$"}}
        if operator == "exists":
            return {field: {"$exists": bool(value)}}
        if operator == "not_exists":
            return {field: {"$exists": False}}
        if operator == "regex":
            return {field: {"$regex": str(value or "")}}
        if operator == "is_null":
            return {field: None}
        if operator == "is_not_null":
            return {field: {"$ne": None}}
        raise ValidationError(message=f"Unsupported filter operator: {operator}")


class CouchDBFilterTranslator(MongoDBFilterTranslator):
    """Translate structured filters into the shared Mango-compatible selector subset."""


class OpenSearchFilterTranslator:
    """Translate structured filters into OpenSearch query DSL clauses."""

    def translate(self, filter_node: FilterNode) -> dict[str, Any]:
        if isinstance(filter_node, FilterCondition):
            return self._translate_condition(filter_node)
        return self._translate_group(filter_node)

    def _translate_group(self, group: FilterGroup) -> dict[str, Any]:
        translated = [self.translate(item) for item in group.conditions]
        translated = [item for item in translated if item not in ({}, None)]
        if not translated:
            return {}
        if group.op == "and":
            if len(translated) == 1:
                return translated[0]
            return {"bool": {"must": translated}}
        if group.op == "or":
            return {"bool": {"should": translated, "minimum_should_match": 1}}
        if group.op == "not":
            return {"bool": {"must_not": translated}}
        raise ValidationError(message=f"Unsupported filter group operator: {group.op}")

    def _translate_condition(self, condition: FilterCondition) -> dict[str, Any]:
        field = condition.field
        operator = condition.operator
        value = condition.value
        if operator == "eq":
            return {"term": {field: value}}
        if operator == "neq":
            return {"bool": {"must_not": [{"term": {field: value}}]}}
        if operator == "gt":
            return {"range": {field: {"gt": value}}}
        if operator == "gte":
            return {"range": {field: {"gte": value}}}
        if operator == "lt":
            return {"range": {field: {"lt": value}}}
        if operator == "lte":
            return {"range": {field: {"lte": value}}}
        if operator == "in":
            return {"terms": {field: list(value or [])}}
        if operator == "not_in":
            return {"bool": {"must_not": [{"terms": {field: list(value or [])}}]}}
        if operator == "contains":
            return {"wildcard": {field: {"value": f"*{str(value or '')}*"}}}
        if operator == "starts_with":
            return {"wildcard": {field: {"value": f"{str(value or '')}*"}}}
        if operator == "ends_with":
            return {"wildcard": {field: {"value": f"*{str(value or '')}"}}}
        if operator == "exists":
            return {"exists": {"field": field}} if bool(value) else {"bool": {"must_not": [{"exists": {"field": field}}]}}
        if operator == "not_exists":
            return {"bool": {"must_not": [{"exists": {"field": field}}]}}
        if operator == "regex":
            return {"regexp": {field: {"value": str(value or "")}}}
        if operator == "is_null":
            return {"bool": {"must_not": [{"exists": {"field": field}}]}}
        if operator == "is_not_null":
            return {"exists": {"field": field}}
        raise ValidationError(message=f"Unsupported filter operator: {operator}")


class ElasticsearchFilterTranslator(OpenSearchFilterTranslator):
    """Translate structured filters into Elasticsearch query DSL clauses.

    Elasticsearch and OpenSearch share the same query DSL for the filter
    operations supported by the connector contract, so this class inherits
    the full OpenSearch translator implementation.
    """


class CassandraFilterTranslator:
    """Translate structured filters into Cassandra-compatible flat equality dicts.

    Cassandra CQL only supports equality-based WHERE clauses on partition
    and clustering key columns (without ALLOW FILTERING). This translator
    reduces filter nodes to ``{column: value}`` equality pairs.
    """

    def translate(self, filter_node: FilterNode) -> dict[str, Any]:
        """Translate a filter node to a flat column=value dict.

        Args:
            filter_node: Structured filter node.

        Returns:
            Dict suitable for ``CassandraConnector._build_where``.

        Raises:
            ValidationError: For unsupported operators or nested groups.
        """
        if isinstance(filter_node, FilterCondition):
            return self._translate_condition(filter_node)
        return self._translate_group(filter_node)

    def _translate_group(self, group: FilterGroup) -> dict[str, Any]:
        if group.op != "and":
            raise ValidationError(
                message=f"Cassandra only supports 'and' filter groups, got: {group.op}"
            )
        result: dict[str, Any] = {}
        for condition in group.conditions:
            result.update(self.translate(condition))
        return result

    def _translate_condition(self, condition: FilterCondition) -> dict[str, Any]:
        if condition.operator != "eq":
            raise ValidationError(
                message=f"Cassandra filter only supports 'eq' operator, got: {condition.operator}"
            )
        return {condition.field: condition.value}
