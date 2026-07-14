# Copyright 2026 Cloud-Dog, Viewdeck Engineering Limited
# Licensed under the Apache License, Version 2.0.
"""Compatibility exports for platform-owned relational connectors."""

from cloud_dog_db.connectors import (
    MariaDBConnector as MariaDBConnectorBase,
    PostgreSQLConnector as PostgreSQLConnectorBase,
    build_connection_uri as _build_uri,
)
from cloud_dog_db.connectors.relational import RelationalConnector

__all__ = [
    "MariaDBConnectorBase",
    "PostgreSQLConnectorBase",
    "RelationalConnector",
    "_build_uri",
]
