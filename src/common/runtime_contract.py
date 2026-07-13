# Copyright 2026 Cloud-Dog, Viewdeck Engineering Limited
# Licensed under the Apache License, Version 2.0.

"""Fail-fast Python runtime contract for db-mcp-server.

The W28R-3011 supply-chain remediation moves the service and its local
developer/test contract to Python 3.13. Keeping this check in application source
prevents an older local interpreter from silently invalidating that remediation.
"""

from __future__ import annotations

import sys
from collections.abc import Sequence

MIN_PYTHON: tuple[int, int] = (3, 13)


def runtime_ok(version_info: Sequence[int] = sys.version_info) -> bool:
    """Return whether ``version_info`` satisfies the supported runtime floor."""
    return tuple(version_info[:2]) >= MIN_PYTHON


def enforce_runtime(version_info: Sequence[int] = sys.version_info) -> None:
    """Reject interpreters older than Python 3.13 with actionable guidance."""
    if runtime_ok(version_info):
        return
    running = ".".join(str(part) for part in tuple(version_info[:3]))
    raise RuntimeError(
        "db-mcp-server requires Python >= 3.13; running "
        f"{running}. Create the project environment with "
        "`python3.13 -m venv .venv` and use `.venv/bin/python` for all tests."
    )
