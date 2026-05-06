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
# Description: Comprehensive Playwright E2E tests for db-mcp-server WebUI
#   covering login, dashboard, profile CRUD, catalogue browse, data browser,
#   schema planner, user/group/API key CRUD, RBAC, search, relationships,
#   entity detail, audit log, settings, and system health.
# Related requirements: FR-01, FR-02, FR-03, AC-01, AC-02, CO-01
# Related tests: AT_WEBUI_E2E
# Recent changes:
#   W28A-443 — Comprehensive E2E suite (replaces W28A-411 initial 13 tests)
#   W28A-411 — Initial implementation

"""
Application Test: AT_WEBUI_E2E / W28A-443 — DB-MCP WebUI E2E Full Suite

Real browser validation of the DB-MCP WebUI contract against a live local
stack.  Uses Playwright with real HTTP setup/cleanup.  Screenshots captured
for every test (pass and fail).  Browser error tracking active.
"""

from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

import httpx
import pytest

from tests.helpers.server_runtime import load_test_runtime_config, service_base_url

pytestmark = [pytest.mark.application, pytest.mark.timeout(300)]

# ---------------------------------------------------------------------------
# Configuration from env vars — ZERO hardcoded values
# ---------------------------------------------------------------------------

TEST_CONFIG = load_test_runtime_config(default_tier="AT")
WEB_URL = service_base_url("web", default_tier="AT")
API_URL = service_base_url("api", default_tier="AT")
API_KEY = str(TEST_CONFIG.get("auth.api_key"))
WEB_LOGIN_USERNAME = str(TEST_CONFIG.get("web_login.username"))
WEB_LOGIN_PASSWORD = str(TEST_CONFIG.get("web_login.password"))

SCREENSHOT_DIR = Path("working/W28A-443-screenshots")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _api(method: str, path: str, **kwargs) -> httpx.Response:
    """Send an authenticated API request.

    Args:
        method: HTTP method.
        path: API path (relative to API_URL/v1).
        **kwargs: Extra httpx request kwargs.

    Returns:
        httpx.Response
    """
    headers = kwargs.pop("headers", {})
    headers["X-API-Key"] = API_KEY
    return httpx.request(
        method, f"{API_URL}/v1{path}",
        headers=headers, timeout=15, **kwargs,
    )


def _ensure_servers() -> None:
    """Verify API and Web servers are healthy — fail (not skip) on error."""
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


def _screenshot(page, name: str) -> None:
    """Capture a full-page screenshot for the given test step."""
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(SCREENSHOT_DIR / f"{name}.png"), full_page=True)


def _pagination_summary(total: int) -> str:
    """Return the summary text used by the paginated admin tables."""
    upper = min(10, max(0, int(total)))
    return f"Showing 1–{upper} of {total}"


def _goto_route(page, path: str, ready_text: str, timeout: int = 15000) -> None:
    """Navigate to a SPA route and wait for expected content to render.

    Args:
        page: Playwright page instance.
        path: SPA route path (e.g. "/admin/users").
        ready_text: Text expected on the page once the view has loaded.
        timeout: Maximum wait time in ms.
    """
    page.goto(f"{WEB_URL}{path}", wait_until="domcontentloaded")
    page.wait_for_function(
        "(expected) => document.body.innerText.includes(expected)",
        arg=ready_text,
        timeout=timeout,
    )


def _is_benign_request_failure(url: str, failure_text: str) -> bool:
    """Filter out expected network errors (pre-auth 401 aborts)."""
    text = str(failure_text or "")
    return "ERR_ABORTED" in text and "/api/" in str(url or "")


def _is_benign_console_error(message: str) -> bool:
    """Filter expected auth-related console errors during login flow."""
    text = str(message or "")
    return "401" in text or "Unauthorized" in text or "Failed to fetch" in text


# ---------------------------------------------------------------------------
# Resource tracker — automatic cleanup for test-created resources
# ---------------------------------------------------------------------------


class ResourceTracker:
    """Track resources created during tests for guaranteed cleanup."""

    def __init__(self) -> None:
        self.user_ids: list[str] = []
        self.group_ids: list[str] = []
        self.profile_ids: list[str] = []
        self.api_key_ids: list[str] = []

    def cleanup(self) -> None:
        """Remove created resources in reverse dependency order."""
        for key_id in reversed(self.api_key_ids):
            try:
                _api("POST", f"/api-keys/{key_id}/revoke",
                     json={"reason": "e2e cleanup"})
            except Exception:
                pass
        for profile_id in reversed(self.profile_ids):
            try:
                _api("DELETE", f"/profiles/{profile_id}")
            except Exception:
                pass
        for group_id in reversed(self.group_ids):
            try:
                _api("DELETE", f"/groups/{group_id}")
            except Exception:
                pass
        for user_id in reversed(self.user_ids):
            try:
                _api("DELETE", f"/users/{user_id}")
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def tracker():
    """Module-scoped resource tracker with final cleanup."""
    t = ResourceTracker()
    yield t
    t.cleanup()


@pytest.fixture(scope="module")
def browser():
    """Provide a Playwright Chromium browser for the test module."""
    _ensure_servers()
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        pytest.fail(f"Playwright is not installed: {exc}")
    pw = sync_playwright().start()
    b = pw.chromium.launch(
        headless=True,
        args=["--no-sandbox", "--disable-dev-shm-usage"],
    )
    yield b
    b.close()
    pw.stop()


@pytest.fixture
def page(browser):
    """Provide a fresh browser page with console/error tracking per test."""
    ctx = browser.new_context(ignore_https_errors=True)
    p = ctx.new_page()

    page_errors: list[str] = []
    request_failures: list[str] = []
    console_errors: list[str] = []

    p.on("pageerror", lambda exc: page_errors.append(str(exc)))
    p.on(
        "requestfailed",
        lambda req: (
            None
            if _is_benign_request_failure(str(req.url), str(req.failure))
            else request_failures.append(f"{req.method} {req.url} -> {req.failure}")
        ),
    )
    p.on(
        "console",
        lambda msg: (
            None
            if msg.type != "error" or _is_benign_console_error(msg.text)
            else console_errors.append(msg.text)
        ),
    )
    p.on("dialog", lambda dialog: dialog.accept())

    # Attach error lists for optional assertion in tests
    p._e2e_page_errors = page_errors          # type: ignore[attr-defined]
    p._e2e_request_failures = request_failures  # type: ignore[attr-defined]
    p._e2e_console_errors = console_errors      # type: ignore[attr-defined]

    yield p
    p.close()
    ctx.close()


@pytest.fixture
def authenticated_page(page):
    """Provide a page logged in via the cookie-backed username/password form."""
    page.goto(f"{WEB_URL}/login", wait_until="domcontentloaded")
    page.wait_for_timeout(3000)

    inputs = page.locator("input")
    assert inputs.count() >= 2, "Login page should expose username and password inputs"

    username_input = page.locator("input[type='text'], input:not([type]), input[type='email']").first
    password_input = page.locator("input[type='password']").first

    if username_input.count() == 0:
        username_input = inputs.nth(0)
    if password_input.count() == 0:
        password_input = inputs.nth(1)

    username_input.fill(WEB_LOGIN_USERNAME)
    password_input.fill(WEB_LOGIN_PASSWORD)

    sign_in_button = page.locator("button:has-text('Sign in')").first
    assert sign_in_button.count() > 0, "Login page should have a Sign in button"
    sign_in_button.click()

    page.wait_for_function(
        "() => window.location.pathname !== '/login'",
        timeout=15000,
    )
    page.wait_for_function(
        "() => document.body.innerText.includes('Dashboard')",
        timeout=15000,
    )

    return page


# ===========================================================================
# T1: Admin Login
# ===========================================================================


def test_t1_login_page_renders(page):
    """T1a: Login page renders with username/password inputs and Sign in button."""
    page.goto(f"{WEB_URL}/login", wait_until="domcontentloaded")
    page.wait_for_timeout(3000)

    assert page.title(), "Page should have a title"
    assert page.locator("input").count() >= 2, \
        "Login page should have username and password inputs"
    assert page.locator("input[type='password']").count() >= 1, \
        "Login page should expose a password input"
    assert page.locator("button:has-text('Sign in')").count() >= 1, \
        "Login page should have a Sign in button"

    _screenshot(page, "t1a_login_page")


def test_t1_login_with_credentials(authenticated_page):
    """T1b: After credential login, user lands on the dashboard."""
    page = authenticated_page

    # Should not be on login page
    assert "/login" not in page.url, \
        f"Should have navigated away from login, still at: {page.url}"

    # Dashboard heading must be visible
    root_html = page.locator("#root").inner_html()
    assert len(root_html) > 100, \
        "App should have rendered meaningful content in #root"
    assert page.locator("h1:has-text('Dashboard')").count() > 0, \
        "Dashboard heading should be visible after login"

    _screenshot(page, "t1b_login_authenticated")


# ===========================================================================
# T2: Dashboard — widgets, status cards, health indicators
# ===========================================================================


def test_t2_dashboard_widgets(authenticated_page):
    """T2: Dashboard shows status cards, profile selector, and recent activity."""
    page = authenticated_page

    page.locator("h1:has-text('Dashboard')").first.wait_for(timeout=15000)
    page.wait_for_timeout(2000)

    body = page.locator("body").inner_text()

    assert "Browse Databases" in body, \
        "Dashboard should show the Browse Databases action"
    assert "Run Query" in body, \
        "Dashboard should show the Run Query action"
    assert "View Connections" in body, \
        "Dashboard should show the View Connections action"
    assert "View Jobs" in body, \
        "Dashboard should show the View Jobs action"

    assert "Timestamp" in body and "Event" in body and "Outcome" in body and "Actor" in body, \
        "Dashboard should show the recent audit activity table"
    assert page.locator("button:has-text('Refresh')").count() > 0, \
        "Dashboard should have Refresh button"

    assert "PROFILES" in body, "Dashboard should render the Profiles status card"
    assert "NAMESPACES" in body, "Dashboard should render the Namespaces status card"
    assert "ENTITIES" in body, "Dashboard should render the Entities status card"
    assert "QUEUE HEALTH" in body, "Dashboard should render the Queue Health status card"
    assert "DATABASE TYPE" in body, "Dashboard should render the Database Type status card"

    _screenshot(page, "t2_dashboard_widgets")


# ===========================================================================
# T3: Database Connections — Profile CRUD
# ===========================================================================


def test_t3_profile_crud(authenticated_page, tracker):
    """T3: Create profile via API, verify on profiles admin page, delete."""
    page = authenticated_page
    suffix = uuid4().hex[:6]
    profile_name = f"e2e_prof_{suffix}"
    profiles_before = _api("GET", "/profiles")
    assert profiles_before.status_code == 200, \
        f"Profile list failed: {profiles_before.status_code} {profiles_before.text}"
    before_items = profiles_before.json().get("data", profiles_before.json())
    expected_total = len(before_items) + 1

    # Create via API
    r = _api("POST", "/profiles", json={
        "name": profile_name,
        "source_type": "mongodb",
        "source_connection": "mongodb://localhost:27017/e2e_test",
        "description": f"E2E Profile {suffix}",
        "enabled_tools": ["catalog.list_namespaces"],
    })
    assert r.status_code in (200, 201), \
        f"Profile create failed: {r.status_code} {r.text}"
    created = r.json().get("data", r.json())
    created_id = created.get("profile_id", profile_name)
    tracker.profile_ids.append(created_id)

    # Navigate to profiles admin page
    _goto_route(page, "/admin/profiles", "Profiles")

    page.wait_for_timeout(2000)
    if _pagination_summary(expected_total) not in page.locator("body").inner_text():
        page.locator("button:has-text('Refresh')").first.click()
        page.wait_for_timeout(2000)

    body = page.locator("body").inner_text()

    # Structural checks
    assert page.locator("h1:has-text('Profiles')").count() > 0, \
        "Profiles page should show the Profiles heading"
    assert page.locator("button:has-text('Add Connection')").count() > 0, \
        "Profiles page should show the Add Connection action"
    assert page.locator("button:has-text('Refresh')").count() > 0, \
        "Profiles page should show the Refresh action"

    assert _pagination_summary(expected_total) in body, \
        "Profiles page should refresh the total profile count after creation"

    _screenshot(page, "t3_profile_crud")

    # Cleanup
    _api("DELETE", f"/profiles/{created_id}")
    tracker.profile_ids.remove(created_id)


# ===========================================================================
# T4: Query Execution — Data Browser
# ===========================================================================


def test_t4_data_browser(authenticated_page):
    """T4: Data browser page renders with filter builder and results table."""
    page = authenticated_page

    # Navigate to data browser with test parameters
    page.goto(
        f"{WEB_URL}/data/test_ns/test_entity",
        wait_until="domcontentloaded",
    )
    page.wait_for_function(
        "(t) => document.body.innerText.includes(t)",
        arg="Data Browser",
        timeout=15000,
    )

    body = page.locator("body").inner_text()

    # Page heading and entity path
    assert "Data Browser" in body, "Page should show Data Browser heading"
    assert "test_ns" in body, "Page should display the namespace"
    assert "test_entity" in body, "Page should display the entity name"

    # Filter builder
    assert "Structured filter builder" in body, \
        "Data browser should show the structured filter builder"
    assert page.locator("[data-testid='data-run-query']").count() > 0, \
        "Data browser should have the Execute query button"
    assert page.locator("[data-testid='filter-add-condition']").count() > 0, \
        "Filter builder should have an Add condition button"

    # Results section
    assert "Results" in body, "Data browser should show Results section"
    assert page.locator("table").count() > 0 or "No rows returned" in body or "Matched records" in body, \
        "Data browser should have the results table or empty-state message"

    _screenshot(page, "t4_data_browser")


# ===========================================================================
# T5: Schema Browser — Schema Change Planner
# ===========================================================================


def test_t5_schema_browser(authenticated_page):
    """T5: Schema planner page renders with plan/apply controls."""
    page = authenticated_page

    _goto_route(page, "/schema", "Schema Change Planner")

    body = page.locator("body").inner_text()

    assert "Create index" in body, \
        "Schema page should show Create index section"
    assert "Plan preview" in body, \
        "Schema page should show Plan preview panel"
    assert "Apply result" in body, \
        "Schema page should show Apply result panel"

    assert page.locator("button:has-text('Plan')").count() > 0, \
        "Schema page should have Plan button"
    assert page.locator("button:has-text('Apply')").count() > 0, \
        "Schema page should have Apply button"

    # Verify input fields for index creation
    assert page.locator("[aria-label='Schema namespace']").count() > 0, \
        "Schema page should have namespace input"
    assert page.locator("[aria-label='Schema entity']").count() > 0, \
        "Schema page should have entity input"
    assert page.locator("[aria-label='Schema index name']").count() > 0, \
        "Schema page should have index name input"

    _screenshot(page, "t5_schema_browser")


# ===========================================================================
# T6: User CRUD
# ===========================================================================


def test_t6_user_crud(authenticated_page, tracker):
    """T6: Create user via API, verify on admin users page, delete via API."""
    page = authenticated_page
    suffix = uuid4().hex[:6]
    username = f"e2e_user_{suffix}"
    users_before = _api("GET", "/users")
    assert users_before.status_code == 200, \
        f"User list failed: {users_before.status_code} {users_before.text}"
    before_items = users_before.json().get("data", users_before.json())
    expected_total = len(before_items) + 1

    # Create via API
    r = _api("POST", "/users", json={
        "username": username,
        "display_name": f"E2E User {suffix}",
        "email": f"{username}@test.example",
        "roles": ["analyst"],
    })
    assert r.status_code in (200, 201), \
        f"User create failed: {r.status_code} {r.text}"
    user_data = r.json().get("data", r.json())
    user_id = user_data.get("user_id", username)
    tracker.user_ids.append(user_id)

    # Verify via API
    r2 = _api("GET", f"/users/{user_id}")
    assert r2.status_code == 200, \
        f"User should be retrievable via API: {r2.status_code}"

    _goto_route(page, "/admin/users", "Users")
    page.wait_for_timeout(2000)
    if _pagination_summary(expected_total) not in page.locator("body").inner_text():
        page.locator("button:has-text('Refresh')").first.click()
        page.wait_for_timeout(2000)

    body = page.locator("body").inner_text()

    # Structural checks
    assert page.locator("h1:has-text('Users')").count() > 0, \
        "Users page should have the Users heading"
    assert page.locator("button:has-text('Add User')").count() > 0, \
        "Users page should show the Add User action"
    assert page.locator("button:has-text('Refresh')").count() > 0, \
        "Users page should show the Refresh action"

    assert _pagination_summary(expected_total) in body, \
        "Users page should refresh the total user count after creation"

    # Verify Delete button exists for CRUD
    assert page.locator("button:has-text('Delete')").count() > 0, \
        "Users page should have Delete buttons for user management"

    _screenshot(page, "t6_user_crud")

    # Cleanup
    _api("DELETE", f"/users/{user_id}")
    tracker.user_ids.remove(user_id)


# ===========================================================================
# T7: Group CRUD
# ===========================================================================


def test_t7_group_crud(authenticated_page, tracker):
    """T7: Create group via API, verify on admin page, delete via API."""
    page = authenticated_page
    suffix = uuid4().hex[:6]
    group_name = f"e2e_grp_{suffix}"
    groups_before = _api("GET", "/groups")
    assert groups_before.status_code == 200, \
        f"Group list failed: {groups_before.status_code} {groups_before.text}"
    before_items = groups_before.json().get("data", groups_before.json())
    expected_total = len(before_items) + 1

    # Create via API
    r = _api("POST", "/groups", json={
        "name": group_name,
        "description": f"E2E Group {suffix}",
        "roles": ["analyst"],
    })
    assert r.status_code in (200, 201), \
        f"Group create failed: {r.status_code} {r.text}"
    group_data = r.json().get("data", r.json())
    group_id = group_data.get("group_id", group_name)
    tracker.group_ids.append(group_id)

    # Verify via API
    r2 = _api("GET", "/groups")
    assert r2.status_code == 200
    groups_list = r2.json().get("data", r2.json().get("groups", []))
    if isinstance(groups_list, dict):
        groups_list = groups_list.get("groups", [])
    assert any(g.get("name") == group_name for g in groups_list), \
        f"Created group '{group_name}' should appear in API groups list"

    _goto_route(page, "/admin/groups", "Groups")
    page.wait_for_timeout(2000)
    if _pagination_summary(expected_total) not in page.locator("body").inner_text():
        page.locator("button:has-text('Refresh')").first.click()
        page.wait_for_timeout(2000)

    body = page.locator("body").inner_text()

    assert page.locator("h1:has-text('Groups')").count() > 0, \
        "Groups page should have the Groups heading"
    assert page.locator("button:has-text('Add Group')").count() > 0, \
        "Groups page should show the Add Group action"
    assert _pagination_summary(expected_total) in body, \
        "Groups page should refresh the total group count after creation"

    _screenshot(page, "t7_group_crud")

    # Cleanup
    _api("DELETE", f"/groups/{group_id}")
    tracker.group_ids.remove(group_id)


# ===========================================================================
# T8: API Key CRUD
# ===========================================================================


def test_t8_api_key_crud(authenticated_page, tracker):
    """T8: Create API key via API, verify on admin page, revoke via API."""
    page = authenticated_page
    suffix = uuid4().hex[:6]
    key_name = f"e2e-key-{suffix}"

    keys_before = _api("GET", "/api-keys")
    assert keys_before.status_code == 200, \
        f"API key list failed: {keys_before.status_code} {keys_before.text}"
    before_body = keys_before.json()
    before_items = before_body.get("data", before_body.get("api_keys", before_body.get("items", [])))
    if isinstance(before_items, dict):
        before_items = before_items.get("api_keys", before_items.get("items", []))
    expected_total = len(before_items) + 1

    users = _api("GET", "/users")
    assert users.status_code == 200, f"User list failed: {users.status_code} {users.text}"
    user_items = users.json().get("data", users.json())
    assert user_items, "API key test requires at least one existing user"
    owner_user_id = user_items[0]["user_id"]

    # Create via API
    r = _api("POST", "/api-keys", json={
        "owner_user_id": owner_user_id,
        "name": key_name,
        "scopes": ["data.read"],
    })
    assert r.status_code in (200, 201), \
        f"API key create failed: {r.status_code} {r.text}"
    key_data = r.json().get("data", r.json())
    key_id = key_data.get("api_key_id") or key_data.get("id", "")
    if key_id:
        tracker.api_key_ids.append(key_id)

    # Verify via API
    r2 = _api("GET", "/api-keys")
    assert r2.status_code == 200
    body_json = r2.json()
    keys_list = body_json.get("data", body_json.get("api_keys",
                              body_json.get("items", [])))
    if isinstance(keys_list, dict):
        keys_list = keys_list.get("api_keys", keys_list.get("items", []))
    assert any(str(k.get("name", "")).startswith("e2e-key-") for k in keys_list), \
        f"Created key should appear in API key list"

    _goto_route(page, "/admin/api-keys", "API Keys")
    page.wait_for_timeout(2000)
    if _pagination_summary(expected_total) not in page.locator("body").inner_text():
        page.locator("button:has-text('Refresh')").first.click()
        page.wait_for_timeout(2000)

    body = page.locator("body").inner_text()

    assert page.locator("h1:has-text('API Keys')").count() > 0, \
        "API keys page should have the API Keys heading"
    assert page.locator("button:has-text('Add API Key')").count() > 0, \
        "API keys page should show the Add API Key action"
    assert _pagination_summary(expected_total) in body, \
        "API keys page should refresh the total API key count after creation"

    # Verify Revoke button exists
    assert page.locator("button:has-text('Revoke')").count() > 0, \
        "API Keys section should have Revoke buttons"

    _screenshot(page, "t8_api_key_crud")

    # Cleanup
    if key_id:
        _api("POST", f"/api-keys/{key_id}/revoke",
             json={"reason": "e2e cleanup"})
        tracker.api_key_ids.remove(key_id)


# ===========================================================================
# T9: RBAC — unauthenticated access denied
# ===========================================================================


def test_t9_rbac_unauthenticated(page):
    """T9: Unauthenticated API calls should be rejected with 401/403."""
    for endpoint in ["/profiles", "/users", "/groups", "/api-keys"]:
        r = httpx.get(f"{API_URL}/v1{endpoint}", timeout=10)
        assert r.status_code in (401, 403), (
            f"Unauthenticated {endpoint} should return 401/403, "
            f"got {r.status_code}"
        )

    _screenshot(page, "t9_rbac_unauthenticated")


# ===========================================================================
# T10: Settings / Config
# ===========================================================================


def test_t10_settings(authenticated_page):
    """T10: Settings page shows runtime config and operations controls."""
    page = authenticated_page

    _goto_route(page, "/settings", "Settings")

    body = page.locator("body").inner_text()

    # Runtime section
    assert "Runtime" in body, "Settings should show Runtime section"

    # Operations section
    assert "Service-Specific" in body, "Settings should show Service-Specific section"
    assert page.locator("button:has-text('Run ping')").count() > 0, \
        "Settings should have Run ping button"
    assert page.locator("button:has-text('Rebuild current profile index')").count() > 0, \
        "Settings should have Rebuild button"

    # Service info (displayed as JSON blocks, not form inputs)
    assert "api_base_url" in body, \
        "Settings should show api_base_url in service info"
    assert "Service Info" in body, \
        "Settings should show Service Info block"

    _screenshot(page, "t10_settings")


# ===========================================================================
# T11: Audit Log
# ===========================================================================


def test_t11_audit_log(authenticated_page):
    """T11: Audit page shows event viewer with filters and events table."""
    page = authenticated_page

    _goto_route(page, "/audit", "Audit")

    body = page.locator("body").inner_text()

    assert "Resource metrics" in body or "Uptime" in body, \
        "Audit page should show resource metrics"
    assert "Recent audit events" in body, \
        "Audit page should show recent audit events"
    assert page.locator("button:has-text('Refresh')").count() > 0, \
        "Audit page should expose audit refresh controls"

    # If audit events are present, verify table structure
    # (DataTable hides column headers when empty)
    page.wait_for_timeout(2000)
    body = page.locator("body").inner_text()
    if "No audit events found" not in body:
        assert "Timestamp" in body or "execute" in body or "success" in body, \
            "Audit events table should display event data when events exist"

    _screenshot(page, "t11_audit_log")


# ===========================================================================
# T12: System Health
# ===========================================================================


def test_t12_system_health(page):
    """T12: Health, ping, and jobs/status endpoints respond correctly."""
    # API health (no auth required)
    r_health = httpx.get(f"{API_URL}/health", timeout=10)
    assert r_health.status_code == 200, \
        f"API /health should return 200, got {r_health.status_code}"

    # Web health (no auth required)
    r_web = httpx.get(f"{WEB_URL}/health", timeout=10)
    assert r_web.status_code == 200, \
        f"Web /health should return 200, got {r_web.status_code}"

    # Authenticated ping
    r_ping = _api("GET", "/ping")
    assert r_ping.status_code == 200, \
        f"/ping should return 200, got {r_ping.status_code}"
    ping_data = r_ping.json()
    assert ping_data.get("ok") is True, f"/ping should return ok=true: {ping_data}"

    # Jobs status
    r_jobs = _api("GET", "/jobs/status")
    assert r_jobs.status_code == 200, \
        f"/jobs/status should return 200, got {r_jobs.status_code}"

    # runtime-config.js should be served
    r_config = httpx.get(f"{WEB_URL}/runtime-config.js", timeout=10)
    assert r_config.status_code == 200, \
        f"runtime-config.js should return 200, got {r_config.status_code}"
    assert "window.__RUNTIME_CONFIG__" in r_config.text, \
        "runtime-config.js should contain window.__RUNTIME_CONFIG__"

    _screenshot(page, "t12_system_health")


# ===========================================================================
# T13: Catalogue Browse
# ===========================================================================


def test_t13_catalogue_browse(authenticated_page):
    """T13: Catalogue page renders with scope panel and entity listing."""
    page = authenticated_page

    _goto_route(page, "/catalogue", "Catalogue")

    body = page.locator("body").inner_text()

    assert "Profile scope" in body, "Catalogue should show Profile scope panel"
    assert "Select a namespace" in body or "Namespace" in body, "Catalogue should show namespace selector"
    assert page.locator("button:has-text('Refresh')").count() > 0, \
        "Catalogue should have a Refresh button"

    # Entities section
    assert "Entities in" in body, \
        "Catalogue should show Entities table section"

    _screenshot(page, "t13_catalogue_browse")


# ===========================================================================
# T14: Discovery Search
# ===========================================================================


def test_t14_search(authenticated_page):
    """T14: Search page renders with query input, mode selector, and results."""
    page = authenticated_page

    _goto_route(page, "/search", "Discovery Search")

    body = page.locator("body").inner_text()

    # Search query section
    assert "Search query" in body, \
        "Search page should show Search query section"
    assert page.locator("[data-testid='search-run-button']").count() > 0, \
        "Search page should have the search-run-button"

    # Mode selector
    assert page.locator("select").count() > 0, \
        "Search page should have a mode selector (Metadata/Content)"

    # Results section
    assert "Results" in body, "Search page should show Results section"

    assert "Matched components" in body, \
        "Search page should show Matched components panel"

    _screenshot(page, "t14_search")


# ===========================================================================
# T15: Relationship Explorer
# ===========================================================================


def test_t15_relationships(authenticated_page):
    """T15: Relationships page renders with entity selection and controls."""
    page = authenticated_page

    _goto_route(page, "/relationships", "Relationship Explorer")

    body = page.locator("body").inner_text()

    # Entity selection
    assert "Entity selection" in body, \
        "Relationships page should show Entity selection section"

    # Create curated relationship
    assert "Create manual relationship" in body, \
        "Relationships page should show Create manual relationship button"

    # Persisted relationships table
    assert "Persisted relationships" in body, \
        "Relationships page should show Persisted relationships section"

    # Action buttons
    assert page.locator("button:has-text('Infer')").count() > 0, \
        "Relationships page should have Infer button"
    assert page.locator("button:has-text('Load')").count() > 0, \
        "Relationships page should have Load button"
    assert page.locator("button:has-text('Create manual relationship')").count() > 0, \
        "Relationships page should have Create manual relationship button"

    _screenshot(page, "t15_relationships")


# ===========================================================================
# T16: Entity Detail
# ===========================================================================


def test_t16_entity_detail(authenticated_page):
    """T16: Entity detail page renders with schema, indexes, and relationships."""
    page = authenticated_page

    page.goto(
        f"{WEB_URL}/catalogue/test_ns/test_entity",
        wait_until="domcontentloaded",
    )
    page.wait_for_function(
        "(t) => document.body.innerText.includes(t)",
        arg="Entity Detail",
        timeout=15000,
    )

    body = page.locator("body").inner_text()

    assert "Schema" in body, "Entity detail should show Schema section"
    assert "Indexes" in body, "Entity detail should show Indexes section"
    assert "Relationships" in body, \
        "Entity detail should show Relationships section"
    assert "Entity metadata" in body, \
        "Entity detail should show Entity metadata panel"
    assert "Sample document shapes" in body, \
        "Entity detail should show Sample document shapes panel"

    # Link to data browser
    assert page.locator("a:has-text('Open data browser')").count() > 0, \
        "Entity detail should have a link to the data browser"

    _screenshot(page, "t16_entity_detail")
