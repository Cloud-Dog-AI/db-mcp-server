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
# Description: Quality checks for db-mcp-server runtime skeleton assets.
# Related requirements: W28A-274-A deliverables 1, 3, 4, 5
# Related tests: QT1.1

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

pytestmark = pytest.mark.quality


REQUIRED_FILES = [
    "start_api_server.py",
    "start_web_server.py",
    "start_mcp_server.py",
    "start_a2a_server.py",
    "server_control.sh",
    "Dockerfile",
    "docker-build.sh",
    "docker-compose.yml",
    "src/common/runtime.py",
    "src/servers/api/app.py",
    "src/servers/web/app.py",
    "src/servers/mcp/app.py",
    "src/servers/a2a/app.py",
]


def test_required_runtime_files_exist() -> None:
    """Ensure the runtime skeleton assets exist in the repository."""
    root = Path(__file__).resolve().parents[3]
    missing = [path for path in REQUIRED_FILES if not (root / path).exists()]
    assert not missing, f"Missing required files: {missing}"


def test_required_platform_package_declarations_are_present() -> None:
    """Lock the non-LLM platform package declarations required by W28A-118C."""
    root = Path(__file__).resolve().parents[3]
    pyproject = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    dependencies = pyproject["project"]["dependencies"]
    dependency_names = {dependency.split("=", 1)[0].split("<", 1)[0].split(">", 1)[0].strip() for dependency in dependencies}

    expected = {
        "cloud_dog_config",
        "cloud_dog_logging",
        "cloud_dog_api_kit",
        "cloud_dog_idam",
        "cloud_dog_jobs",
        "cloud_dog_db",
        "cloud-dog-storage",
    }

    assert expected <= dependency_names


def test_w28a_118c_docs_map_packages_to_ui_and_tests() -> None:
    """Ensure package posture is traceable to requirements, UI surfaces, and tests."""
    root = Path(__file__).resolve().parents[3]
    requirements = (root / "docs" / "REQUIREMENTS.md").read_text(encoding="utf-8")
    architecture = (root / "docs" / "ARCHITECTURE.md").read_text(encoding="utf-8")
    tests = (root / "docs" / "TESTS.md").read_text(encoding="utf-8")
    combined = "\n".join([requirements, architecture, tests])

    for package in [
        "cloud_dog_config",
        "cloud_dog_logging",
        "cloud_dog_api_kit",
        "cloud_dog_idam",
        "cloud_dog_jobs",
        "cloud_dog_db",
        "cloud_dog_storage",
    ]:
        assert package in combined

    for surface in [
        "Catalogue",
        "Entity Detail",
        "Data Browser",
        "Search",
        "Jobs",
        "Settings",
        "MCP Console",
        "A2A Console",
        "API Docs",
    ]:
        assert surface in tests

    for evidence in [
        "UT1.1_ConfigLoading",
        "UT1.3_AccessControlService",
        "UT1.11_WebUiServing",
        "UT1.19_JobLifecycle",
        "ST1.5_ContentApi",
        "ST1.7_SearchApi",
        "IT1.6_SearchIndexingLifecycle",
        "AT_WEBUI_E2E",
    ]:
        assert evidence in tests
