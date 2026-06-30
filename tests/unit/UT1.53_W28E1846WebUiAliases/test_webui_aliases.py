from __future__ import annotations

import ast
from pathlib import Path

import pytest

from src.servers.web.ui_spa import is_spa_entry_path, spa_entry_routes

pytestmark = [pytest.mark.unit, pytest.mark.fast]


def _legacy_redirects() -> dict[str, str]:
    source = Path("src/servers/web/app.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "_WEBUI_LEGACY_REDIRECTS":
                    return ast.literal_eval(node.value)
    raise AssertionError("_WEBUI_LEGACY_REDIRECTS literal not found")


@pytest.mark.UT
@pytest.mark.webui
@pytest.mark.req("FR-022")
def test_profile_connection_aliases_redirect_to_canonical_admin_routes() -> None:
    redirects = _legacy_redirects()

    assert redirects["/source-connections"] == "/admin/source-connections"
    assert redirects["/profiles"] == "/admin/profiles"
    assert "/admin/source-connections" in spa_entry_routes()
    assert "/admin/profiles" in spa_entry_routes()
    assert is_spa_entry_path("/admin/source-connections")
    assert is_spa_entry_path("/admin/profiles")
