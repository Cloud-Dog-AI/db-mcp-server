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
# Description: Unit tests for MongoDB URI resolution from runtime config.
# Related requirements: CN-01, CFG-01
# Related tests: W28A-497

from __future__ import annotations

import pytest

from cloud_dog_api_kit.errors import ValidationError

from src.core.connectors.mongodb.service import resolve_mongodb_uri

pytestmark = pytest.mark.unit


class DummyConfig:
    """Minimal config stub supporting dotted lookups used by the connector."""

    def __init__(self, values: dict[str, object]) -> None:
        self._values = values

    def get(self, path: str, default: object = None) -> object:
        return self._values.get(path, default)


def test_resolve_mongodb_uri_prefers_profile_uri() -> None:
    """An explicit profile URI should take precedence over runtime defaults."""
    config = DummyConfig({"connectors.mongodb.default_uri": "mongodb://ignored"})
    profile = {"source_connection": "mongodb://profile-uri"}
    assert resolve_mongodb_uri(config, profile) == "mongodb://profile-uri"


def test_resolve_mongodb_uri_uses_configured_default_uri() -> None:
    """A configured default URI should be used when the profile is symbolic."""
    config = DummyConfig({"connectors.mongodb.default_uri": "mongodb://default-uri"})
    profile = {"source_connection": "default"}
    assert resolve_mongodb_uri(config, profile) == "mongodb://default-uri"


def test_resolve_mongodb_uri_builds_uri_from_structured_defaults() -> None:
    """Structured MongoDB settings should be assembled into a connection URI."""
    config = DummyConfig(
        {
            "connectors.mongodb.default_uri": "",
            "connectors.mongodb.default_host": "mongo1.db.example.com",
            "connectors.mongodb.default_port": "27017",
            "connectors.mongodb.default_username": "root@example.com",
            "connectors.mongodb.default_password": "p@ss word",
            "connectors.mongodb.default_auth_database": "admin",
            "connectors.mongodb.default_query": "ssl=false",
        }
    )
    profile = {"source_connection": "default"}
    assert (
        resolve_mongodb_uri(config, profile)
        == "mongodb://root%40example.com:p%40ss+word@mongo1.db.example.com:27017/admin?ssl=false"
    )


def test_resolve_mongodb_uri_rejects_missing_settings() -> None:
    """Missing MongoDB config should still fail with a clear validation error."""
    config = DummyConfig({"connectors.mongodb.default_uri": ""})
    profile = {"source_connection": "default"}
    with pytest.raises(ValidationError, match="MongoDB connector URI is not configured"):
        resolve_mongodb_uri(config, profile)
