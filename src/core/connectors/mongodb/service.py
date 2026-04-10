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
# Description: MongoDB connector service resolving profiles and access checks.
# Related requirements: CN-01, AC-01, AC-02
# Related tests: ST1.3, IT1.2

"""MongoDB connector service for profile-scoped operations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import quote_plus

from fastapi import Request
from pymongo.errors import PyMongoError

from cloud_dog_api_kit.errors import InternalError, NotFoundError, ValidationError
from cloud_dog_logging import Actor, Target

from src.core.connectors.mongodb.adapter import MongoDBConnector


@dataclass(slots=True)
class MongoProfileSession:
    """Resolved MongoDB profile session."""

    profile: dict[str, Any]
    connector: MongoDBConnector


def resolve_mongodb_uri(config: Any, profile: dict[str, Any]) -> str:
    """Resolve a MongoDB URI from profile settings or runtime defaults."""
    source_connection = str(profile.get("source_connection", "") or "").strip()
    if source_connection and "://" in source_connection:
        return source_connection

    default_uri = str(config.get("connectors.mongodb.default_uri", "") or "").strip()
    if default_uri:
        return default_uri

    host = str(config.get("connectors.mongodb.default_host", "") or "").strip()
    port = str(config.get("connectors.mongodb.default_port", "") or "").strip()
    if not host:
        raise ValidationError(message="MongoDB connector URI is not configured")

    username = str(config.get("connectors.mongodb.default_username", "") or "").strip()
    password = str(config.get("connectors.mongodb.default_password", "") or "").strip()
    auth_database = str(config.get("connectors.mongodb.default_auth_database", "") or "").strip()
    query = str(config.get("connectors.mongodb.default_query", "") or "").strip()

    authority = host if not port else f"{host}:{port}"
    if username:
        credentials = quote_plus(username)
        if password:
            credentials = f"{credentials}:{quote_plus(password)}"
        authority = f"{credentials}@{authority}"

    path = f"/{auth_database}" if auth_database else ""
    suffix = f"?{query}" if query else ""
    return f"mongodb://{authority}{path}{suffix}"


class MongoDBConnectorService:
    """Resolve MongoDB profiles and execute audited connector operations."""

    def __init__(self, runtime) -> None:
        self._runtime = runtime

    def _resolve_uri(self, profile: dict[str, Any]) -> str:
        return resolve_mongodb_uri(self._runtime.config, profile)

    def for_profile(self, profile_id: str) -> MongoProfileSession:
        profile = self._runtime.access_control.get_profile(profile_id)
        if profile["source_type"] != "mongodb":
            raise ValidationError(message=f"Profile {profile_id} is not a MongoDB profile")
        connector = MongoDBConnector(
            uri=self._resolve_uri(profile),
            timeout_ms=int(self._runtime.config.get("connectors.mongodb.timeout_ms", 30000)),
        )
        try:
            connector.validate_profile()
        except PyMongoError as exc:
            connector.close()
            raise InternalError(message=f"MongoDB connection failed: {exc}") from exc
        return MongoProfileSession(profile=profile, connector=connector)

    def execute(
        self,
        request: Request,
        *,
        profile_id: str,
        permission: str,
        audit_action: str,
        audit_target_id: str,
        callback,
    ) -> Any:
        principal = self._runtime.access_control.require_request_permission(
            request,
            permission=permission,
            profile_id=profile_id,
            audit_resource_type="profile",
            audit_resource_id=profile_id,
        )
        session = self.for_profile(profile_id)
        try:
            result = callback(session.connector, session.profile)
        except PyMongoError as exc:
            self._runtime.audit_logger.log_tool_call(
                actor=Actor(type="user", id=principal.user_id, roles=principal.roles),
                tool=audit_action,
                params={"profile_id": profile_id, "target": audit_target_id},
                outcome="failure",
                duration_ms=0,
                target=Target(type="mongodb", id=audit_target_id or profile_id),
                error=str(exc),
            )
            raise InternalError(message=f"MongoDB operation failed: {exc}") from exc
        finally:
            session.connector.close()
        self._runtime.audit_logger.log_tool_call(
            actor=Actor(type="user", id=principal.user_id, roles=principal.roles),
            tool=audit_action,
            params={"profile_id": profile_id, "target": audit_target_id},
            outcome="success",
            duration_ms=0,
            target=Target(type="mongodb", id=audit_target_id or profile_id),
        )
        return result
