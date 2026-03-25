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
# Description: Common connector protocol for db-mcp-server source adapters.
# Related requirements: CN-01, NF-04
# Related tests: UT1.4, ST1.3, IT1.2

"""Common connector protocol for db-mcp-server source adapters."""

from __future__ import annotations

from typing import Any, Protocol


class ConnectorContract(Protocol):
    """Common adapter contract used across source connectors."""

    def capability_report(self) -> dict[str, Any]: ...
    def list_namespaces(self) -> list[dict[str, Any]]: ...
    def list_entities(self, namespace: str) -> list[dict[str, Any]]: ...
    def describe_entity(self, namespace: str, entity: str) -> dict[str, Any]: ...
    def describe_fields(self, namespace: str, entity: str) -> dict[str, Any]: ...
    def read(
        self,
        namespace: str,
        entity: str,
        filter: dict[str, Any] | None = None,
        projection: dict[str, Any] | None = None,
        sort: list[dict[str, Any]] | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]: ...
    def create(self, namespace: str, entity: str, document: dict[str, Any]) -> dict[str, Any]: ...
    def update(self, namespace: str, entity: str, filter: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]: ...
    def delete(self, namespace: str, entity: str, filter: dict[str, Any]) -> dict[str, Any]: ...
    def count(self, namespace: str, entity: str, filter: dict[str, Any] | None = None) -> int: ...
    def sample_shapes(self, namespace: str, entity: str, n: int = 10) -> list[dict[str, Any]]: ...
    def list_indexes(self, namespace: str, entity: str) -> list[dict[str, Any]]: ...
    def schema_change_plan(self, operation: dict[str, Any]) -> dict[str, Any]: ...
    def schema_change_apply(self, plan: dict[str, Any]) -> dict[str, Any]: ...
    def extract_relationships(self, namespace: str, entity: str) -> list[dict[str, Any]]: ...
