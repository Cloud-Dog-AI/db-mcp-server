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
# Description: Access-control service exports for db-mcp-server.
# Related requirements: AC-01, AC-02, AC-03, CFG-01
# Related tests: UT1.3, ST1.2, IT1.1

"""Access-control service exports for db-mcp-server."""

from src.core.access_control.service import AccessControlService, PrincipalContext

__all__ = ["AccessControlService", "PrincipalContext"]
