# Copyright 2026 Cloud-Dog, Viewdeck Engineering Limited
# Licensed under the Apache License, Version 2.0.

"""W28R-3011 Python 3.13 project-local runtime contract regression."""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path

import pytest

from src.common.runtime_contract import MIN_PYTHON, enforce_runtime, runtime_ok


REPO_ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.UT
@pytest.mark.internal
@pytest.mark.req("FR-027")
def test_current_interpreter_satisfies_python_313_floor() -> None:
    assert MIN_PYTHON == (3, 13)
    assert sys.version_info[:2] >= MIN_PYTHON
    assert runtime_ok()


@pytest.mark.UT
@pytest.mark.internal
@pytest.mark.req("FR-027")
def test_pre_313_is_rejected_and_supported_versions_pass() -> None:
    for version in ((3, 12, 13), (3, 11, 9), (3, 10, 0)):
        assert not runtime_ok(version)
        with pytest.raises(RuntimeError, match=r"requires Python >= 3\.13"):
            enforce_runtime(version)
    for version in ((3, 13, 0), (3, 13, 14), (3, 14, 0)):
        assert runtime_ok(version)
        enforce_runtime(version)


@pytest.mark.UT
@pytest.mark.internal
@pytest.mark.req("FR-027")
def test_project_metadata_and_ruff_target_python_313() -> None:
    metadata = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert metadata["project"]["requires-python"] == ">=3.13"
    assert metadata["tool"]["ruff"]["target-version"] == "py313"
    assert "make lint" in (REPO_ROOT / "docs" / "BUILD.md").read_text(encoding="utf-8")


@pytest.mark.UT
@pytest.mark.internal
@pytest.mark.req("FR-027")
def test_python_version_file_pins_313() -> None:
    assert (REPO_ROOT / ".python-version").read_text(encoding="utf-8").strip() == "3.13"


@pytest.mark.UT
@pytest.mark.internal
@pytest.mark.req("FR-027")
def test_container_and_local_commands_use_python_313_contract() -> None:
    internal = (REPO_ROOT / "Dockerfile").read_text(encoding="utf-8")
    public = (REPO_ROOT / "Dockerfile.public").read_text(encoding="utf-8")
    assert "registry.cloud-dog.net:443/cloud-dog/python-runtime@sha256:" in internal
    assert "python:3.13-slim" in public
    assert "python:3.12" not in internal + public
    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    assert "PYTHON ?= .venv/bin/python" in makefile
    assert "lint:" in makefile
    assert "runtime-preflight:" in makefile


@pytest.mark.UT
@pytest.mark.internal
@pytest.mark.req("FR-027")
def test_docker_build_percent_encodes_private_index_credentials() -> None:
    build_script = (REPO_ROOT / "docker-build.sh").read_text(encoding="utf-8")
    assert '[[ ! "${PIP_INDEX_URL}" =~ /simple$ ]]' in build_script
    assert 'PIP_INDEX_URL="${PIP_INDEX_URL}/simple"' in build_script
    assert 'urllib.parse.quote(os.environ["PYPI_VALUE"], safe="")' in build_script
    assert "${PYPI_USERNAME_URLENCODED}:${PYPI_PASSWORD_URLENCODED}@" in build_script
    assert "${PYPI_USERNAME}:${PYPI_PASSWORD}@" not in build_script
    assert 'BUILD_IMAGE_REF="${REGISTRY}/${LOCAL_IMAGE_REF}"' in build_script
    dev_block = build_script.split('else\n  # Dev/deployment variant', 1)[1]
    assert "extra-index-url" not in dev_block
    assert "files.pythonhosted.org" not in dev_block
