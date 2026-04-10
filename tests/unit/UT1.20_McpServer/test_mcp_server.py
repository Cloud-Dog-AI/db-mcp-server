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
# Description: Unit tests for MCP surface middleware configuration.
# Related requirements: W28A-274-A deliverables 1, 2
# Related tests: UT1.20

from __future__ import annotations

import pytest
from cloud_dog_api_kit.middleware import TimeoutMiddleware

from src.servers.mcp.app import create_mcp_app

pytestmark = pytest.mark.unit


def test_mcp_surface_raises_request_timeout_budget() -> None:
    app = create_mcp_app(["tests/env-UT"])
    for middleware in app.user_middleware:
        if middleware.cls is TimeoutMiddleware:
            assert middleware.kwargs["timeout_seconds"] == 120.0
            break
    else:
        pytest.fail("TimeoutMiddleware not installed")
