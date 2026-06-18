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

"""ST-only MCP tools used by WebUI conformance suites."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from cloud_dog_api_kit import ToolContract


_ENABLED_TEST_TIERS = {"ST", "SYSTEM", "E2E"}


def _tier_from_env_file(env_file: str) -> str:
    try:
        lines = Path(env_file).read_text(encoding="utf-8").splitlines()
    except OSError:
        return ""
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        if key.strip() == "TEST_ENV_TIER":
            return value.strip().strip("\"'")
    return ""


def e2e_tools_enabled(env_files: list[str] | None = None) -> bool:
    """Return true only for explicit local/system test tiers."""
    process_tier = os.getenv("TEST_ENV_TIER", "").strip().upper()
    if process_tier in _ENABLED_TEST_TIERS:
        return True
    for env_file in env_files or []:
        if _tier_from_env_file(env_file).upper() in _ENABLED_TEST_TIERS:
            return True
    return False


def build_e2e_tool_registry(runtime) -> dict[str, ToolContract]:
    """Build MCP tools that are available only in ST/E2E environments."""

    async def w28a_691_lifecycle_job(payload: dict[str, Any], request) -> dict[str, Any]:
        principal = runtime.access_control.principal_from_request(request)
        return runtime.search.create_lifecycle_evidence_job(
            outcome=str(payload.get("outcome", "")).strip(),
            job_type=str(payload.get("job_type", "")).strip(),
            label=str(payload.get("label", "")).strip(),
            principal=principal,
        )

    return {
        "w28a_691_lifecycle_job": ToolContract(
            name="w28a_691_lifecycle_job",
            handler=w28a_691_lifecycle_job,
            description="Create source-backed lifecycle job evidence for W28A-691 ST WebUI tests.",
            input_schema={
                "type": "object",
                "properties": {
                    "outcome": {"type": "string"},
                    "job_type": {"type": "string"},
                    "label": {"type": "string"},
                },
                "required": ["outcome", "job_type", "label"],
            },
        ),
    }
