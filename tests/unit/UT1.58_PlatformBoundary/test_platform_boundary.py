"""Mandatory source-control coverage for RULES sections 1.4 and 1.4.1."""

import pytest

from scripts.check_platform_boundaries import scan_service_source



@pytest.mark.UT
@pytest.mark.internal
@pytest.mark.req("FR-027")
def test_service_source_has_no_platform_boundary_bypasses() -> None:
    assert scan_service_source() == []
