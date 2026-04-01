#!/usr/bin/env python3
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
# Description: A2A server entry point for db-mcp-server.
# Related requirements: W28A-274-A deliverable 1
# Related tests: ST1.1

"""Start the db-mcp-server A2A surface."""

from __future__ import annotations

import uvicorn

from src.common.config_loader import load_runtime_config
from src.servers.a2a.app import create_a2a_app


def main() -> None:
    """Load config and run the A2A server."""
    config = load_runtime_config()
    uvicorn.run(
        create_a2a_app(),
        host=str(config.get("a2a_server.host")),
        port=int(config.get("a2a_server.port")),
        log_level=str(config.get("log.level", "info")).lower(),
    )


if __name__ == "__main__":
    main()
