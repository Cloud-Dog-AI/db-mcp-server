from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.servers.web.app import create_web_app, _build_identity

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENV_UT = str(PROJECT_ROOT / "tests" / "env-UT")


@pytest.fixture()
def web_app(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    ui_dist = tmp_path / "ui" / "dist"
    ui_dist.mkdir(parents=True)
    (ui_dist / "index.html").write_text(
        "<html><body><div id='root'>db-mcp-webui</div></body></html>", encoding="utf-8"
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("CLOUD_DOG__BUILD__SOURCE_COMMIT", "deadbeefcafebabe0123456789abcdef01234567")
    monkeypatch.setenv("CLOUD_DOG__BUILD__SOURCE_BRANCH", "w28e-1863-wsc014-db-mcp")
    monkeypatch.setenv("CLOUD_DOG__BUILD__BUILD_DATE", "2026-07-08T10:00:00Z")
    return create_web_app([ENV_UT])


@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("UI-R7")
def test_version_route_emits_build_identity_not_spa_shadowed(web_app) -> None:
    client = TestClient(web_app, raise_server_exceptions=False)
    resp = client.get("/version")
    assert resp.status_code == 200
    # Not shadowed by the /{path:path} SPA catch-all: JSON, not the index.html shell.
    assert "application/json" in resp.headers.get("content-type", "")
    body = resp.json()
    assert body["service"] == "db-mcp-server"
    assert body["source_commit"] == "deadbeefcafebabe0123456789abcdef01234567"
    assert body["commit"] == "deadbeefcafebabe0123456789abcdef01234567"
    assert body["source_branch"] == "w28e-1863-wsc014-db-mcp"
    assert body["build_date"] == "2026-07-08T10:00:00Z"
    assert body["version"]
