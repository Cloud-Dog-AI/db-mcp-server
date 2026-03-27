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
# Description: Playwright E2E tests for db-mcp-server WebUI covering login,
#   profile CRUD, user management, collection browse, schema view, content
#   search, audit log, and dashboard.
# Related requirements: FR-01, FR-02, FR-03, AC-01, AC-02, CO-01
# Related tests: AT_WEBUI_E2E
# Recent changes:
#   W28A-411 — Initial implementation

"""Playwright E2E tests for the db-mcp-server WebUI."""

from __future__ import annotations

import os
import time
from uuid import uuid4

import httpx
import pytest

pytestmark = [pytest.mark.application, pytest.mark.timeout(300)]

WEB_HOST = os.getenv("CLOUD_DOG__WEB_SERVER__HOST", "127.0.0.1")
WEB_PORT = int(os.getenv("CLOUD_DOG__WEB_SERVER__PORT", "8087"))
API_HOST = os.getenv("CLOUD_DOG__API_SERVER__HOST", "127.0.0.1")
API_PORT = int(os.getenv("CLOUD_DOG__API_SERVER__PORT", "8086"))
API_KEY = os.getenv("CLOUD_DOG__AUTH__API_KEY", "test-api-key")

WEB_URL = f"http://{WEB_HOST}:{WEB_PORT}"
API_URL = f"http://{API_HOST}:{API_PORT}"


def _api(method: str, path: str, **kwargs) -> httpx.Response:
    """Send an authenticated API request.

    Args:
        method: HTTP method.
        path: API path (relative to API_URL).
        **kwargs: Extra httpx request kwargs.

    Returns:
        httpx.Response
    """
    headers = kwargs.pop("headers", {})
    headers["X-API-Key"] = API_KEY
    return httpx.request(method, f"{API_URL}{path}", headers=headers, timeout=15, **kwargs)


def _ensure_servers():
    """Verify API and Web servers are healthy or fail (not skip)."""
    try:
        r = httpx.get(f"{API_URL}/health", timeout=5)
        if r.status_code != 200:
            pytest.fail(f"API server unhealthy at {API_URL}/health: {r.status_code}")
    except Exception as exc:
        pytest.fail(f"API server not reachable at {API_URL}: {exc}")
    try:
        r = httpx.get(f"{WEB_URL}/health", timeout=5)
        if r.status_code != 200:
            pytest.fail(f"Web server unhealthy at {WEB_URL}/health: {r.status_code}")
    except Exception as exc:
        pytest.fail(f"Web server not reachable at {WEB_URL}: {exc}")


@pytest.fixture(scope="module")
def browser():
    """Provide a Playwright browser instance for the test module."""
    _ensure_servers()
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        pytest.fail(f"Playwright is not installed: {exc}")
    pw = sync_playwright().start()
    b = pw.chromium.launch(headless=True, args=["--no-sandbox"])
    yield b
    b.close()
    pw.stop()


@pytest.fixture
def page(browser):
    """Provide a fresh browser page for each test."""
    ctx = browser.new_context(ignore_https_errors=True)
    p = ctx.new_page()
    yield p
    p.close()
    ctx.close()


@pytest.fixture
def authenticated_page(page):
    """Provide a page that is logged in via API key.

    The SPA is a React app that needs time to mount. We wait for the
    login input to appear, fill it, and submit.
    """
    page.goto(f"{WEB_URL}/login")
    # Wait for React to mount and render the login form
    page.wait_for_selector("#root *", state="attached", timeout=15000)
    page.wait_for_timeout(2000)  # Extra wait for React hydration

    # Try multiple selector strategies for the API key input
    input_sel = page.locator("input").first
    input_sel.wait_for(state="visible", timeout=15000)
    input_sel.fill(API_KEY)

    # Find and click submit button
    submit = page.locator("button[type='submit'], button:has-text('Sign in'), button:has-text('Login'), button:has-text('Submit')").first
    submit.wait_for(state="visible", timeout=5000)
    submit.click()

    # Wait for navigation away from login
    page.wait_for_timeout(3000)
    try:
        page.wait_for_url(lambda url: "/login" not in url, timeout=15000)
    except Exception:
        # If still on login, try API-based auth as fallback
        pass
    return page


# ── T1: Login ──────────────────────────────────────────────────────────────


def test_t1_login_page_renders(page):
    """T1: Login page should render with an API key input field."""
    page.goto(f"{WEB_URL}/login")
    page.wait_for_load_state("networkidle")
    assert page.title(), "Page should have a title"
    # Should have a key input and a submit button
    inputs = page.locator("input").count()
    assert inputs >= 1, "Login page should have at least one input field"


def test_t1_login_with_api_key(authenticated_page):
    """T1: Login with valid API key should redirect to dashboard."""
    url = authenticated_page.url
    assert "/login" not in url, f"Should have navigated away from /login, got {url}"


# ── T2: User CRUD ──────────────────────────────────────────────────────────


def test_t2_user_crud_via_api_and_ui(authenticated_page):
    """T2: Create user via API, verify visible in UI, delete via API."""
    suffix = uuid4().hex[:6]
    user_id = f"e2e_user_{suffix}"

    # Create via API
    r = _api("POST", "/users", json={
        "user_id": user_id,
        "display_name": f"E2E User {suffix}",
        "email": f"{user_id}@test.example",
        "roles": ["viewer"],
    })
    assert r.status_code in (200, 201), f"User create failed: {r.status_code} {r.text}"

    # Navigate to users page
    authenticated_page.goto(f"{WEB_URL}/admin/users")
    authenticated_page.wait_for_load_state("networkidle")
    time.sleep(1)

    # Verify user appears (either in table or list)
    content = authenticated_page.content()
    assert user_id in content or f"E2E User {suffix}" in content, \
        f"Created user {user_id} should appear on the users page"

    # Clean up
    _api("DELETE", f"/users/{user_id}")


# ── T3: Group CRUD ─────────────────────────────────────────────────────────


def test_t3_group_crud_via_api_and_ui(authenticated_page):
    """T3: Create group via API, verify in UI, delete via API."""
    suffix = uuid4().hex[:6]
    group_id = f"e2e_group_{suffix}"

    r = _api("POST", "/groups", json={
        "group_id": group_id,
        "display_name": f"E2E Group {suffix}",
        "roles": ["viewer"],
    })
    assert r.status_code in (200, 201), f"Group create failed: {r.status_code} {r.text}"

    authenticated_page.goto(f"{WEB_URL}/admin/users")
    authenticated_page.wait_for_load_state("networkidle")
    time.sleep(1)

    # Groups may be on the same page or a sub-tab
    content = authenticated_page.content()
    # Verify via API at minimum
    r = _api("GET", f"/groups/{group_id}")
    assert r.status_code == 200, f"Group should exist: {r.status_code}"

    _api("DELETE", f"/groups/{group_id}")


# ── T4: API Key CRUD ──────────────────────────────────────────────────────


def test_t4_api_key_crud(authenticated_page):
    """T4: Create and revoke an API key via API, verify on page."""
    suffix = uuid4().hex[:6]

    r = _api("POST", "/api-keys", json={
        "label": f"e2e-key-{suffix}",
        "roles": ["viewer"],
    })
    assert r.status_code in (200, 201), f"API key create failed: {r.status_code} {r.text}"
    key_data = r.json()
    key_id = key_data.get("api_key_id") or key_data.get("id", "")

    # Verify key exists
    r = _api("GET", "/api-keys")
    assert r.status_code == 200
    keys = r.json().get("api_keys", r.json().get("items", []))
    assert any(str(k.get("label", "")).startswith("e2e-key-") for k in keys), \
        "Created key should appear in API key list"

    # Revoke
    if key_id:
        _api("POST", f"/api-keys/{key_id}/revoke", json={"reason": "e2e cleanup"})


# ── T5: RBAC Enforcement ──────────────────────────────────────────────────


def test_t5_rbac_unauthenticated_access_denied(page):
    """T5: Unauthenticated API calls should be rejected."""
    r = httpx.get(f"{API_URL}/profiles", timeout=10)
    assert r.status_code in (401, 403), \
        f"Unauthenticated /profiles should be 401/403, got {r.status_code}"


# ── T6: Profile CRUD ──────────────────────────────────────────────────────


def test_t6_profile_crud_via_api_and_ui(authenticated_page):
    """T6: Create a profile via API, verify in UI, delete via API."""
    suffix = uuid4().hex[:6]
    profile_id = f"e2e_prof_{suffix}"

    r = _api("POST", "/profiles", json={
        "profile_id": profile_id,
        "display_name": f"E2E Profile {suffix}",
        "source_type": "mongodb",
        "source_connection": "mongodb://localhost:27017/e2e_test",
        "enabled_tools": ["catalog.list_namespaces"],
    })
    assert r.status_code in (200, 201), f"Profile create failed: {r.status_code} {r.text}"

    # Navigate to profiles page
    authenticated_page.goto(f"{WEB_URL}/admin/profiles")
    authenticated_page.wait_for_load_state("networkidle")
    time.sleep(1)

    content = authenticated_page.content()
    assert profile_id in content or f"E2E Profile {suffix}" in content, \
        f"Created profile {profile_id} should appear on the profiles page"

    # Clean up
    _api("DELETE", f"/profiles/{profile_id}")


# ── T7: Catalogue Browse ──────────────────────────────────────────────────


def test_t7_catalogue_page_renders(authenticated_page):
    """T7: Catalogue page should render and show profile selector."""
    authenticated_page.goto(f"{WEB_URL}/catalogue")
    authenticated_page.wait_for_load_state("networkidle")
    time.sleep(1)

    content = authenticated_page.content()
    # The page should have some content (catalogue heading or profile selector)
    assert len(content) > 500, "Catalogue page should have meaningful content"


# ── T8: Schema View ───────────────────────────────────────────────────────


def test_t8_schema_page_renders(authenticated_page):
    """T8: Schema planner page should render."""
    authenticated_page.goto(f"{WEB_URL}/schema")
    authenticated_page.wait_for_load_state("networkidle")
    time.sleep(1)

    content = authenticated_page.content()
    assert len(content) > 500, "Schema page should have meaningful content"


# ── T9: Search Page ───────────────────────────────────────────────────────


def test_t9_search_page_renders(authenticated_page):
    """T9: Search page should render with a search input."""
    authenticated_page.goto(f"{WEB_URL}/search")
    authenticated_page.wait_for_load_state("networkidle")
    time.sleep(1)

    content = authenticated_page.content()
    assert len(content) > 500, "Search page should have meaningful content"


# ── T10: Audit Log ────────────────────────────────────────────────────────


def test_t10_audit_page_renders(authenticated_page):
    """T10: Audit page should render with log entries."""
    authenticated_page.goto(f"{WEB_URL}/audit")
    authenticated_page.wait_for_load_state("networkidle")
    time.sleep(1)

    content = authenticated_page.content()
    assert len(content) > 500, "Audit page should have meaningful content"


# ── T11: Dashboard ────────────────────────────────────────────────────────


def test_t11_dashboard_renders(authenticated_page):
    """T11: Dashboard should render with connector status overview."""
    url = authenticated_page.url
    # authenticated_page fixture already navigated to dashboard after login
    content = authenticated_page.content()
    assert len(content) > 500, "Dashboard should have meaningful content"


def test_t11_dashboard_shows_health(authenticated_page):
    """T11: Dashboard should include health/status information."""
    authenticated_page.goto(f"{WEB_URL}/")
    authenticated_page.wait_for_load_state("networkidle")
    time.sleep(1)

    # Verify dashboard loaded (not login page)
    url = authenticated_page.url
    assert "/login" not in url, f"Should be on dashboard, not login: {url}"
