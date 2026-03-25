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
# Description: MCP server entry point for db-mcp-server.
# Related requirements: W28A-274-A deliverable 1
# Related tests: ST1.1

"""Start the db-mcp-server MCP surface."""

from __future__ import annotations

import uvicorn

from src.common.config_loader import load_runtime_config
from src.servers.mcp.app import create_mcp_app


def main() -> None:
    """Load config and run the MCP server."""
    config = load_runtime_config()
    uvicorn.run(
        create_mcp_app(),
        host=str(config.get("mcp_server.host", "0.0.0.0")),
        port=int(config.get("mcp_server.port", 8088)),
        log_level=str(config.get("log.level", "info")).lower(),
    )


if __name__ == "__main__":
    main()
