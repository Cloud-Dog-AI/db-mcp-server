"""W28A-732-R5 (reopen) live G8 — cookie username/password login contract.

Proves on live dbmcpserver0:
  * /runtime-config.js advertises AUTH_MODE "cookie";
  * the anon /login page renders a username + password form (2 inputs);
  * admin / read-write / read-only all log in by USERNAME + PASSWORD (cookie);
  * read-only data writes are denied 403 on BOTH the /webapi (web-tier) and
    /webmcp (MCP role-key RBAC) surfaces; read-only reads are permitted;
  * read-write / admin writes are permitted;
  * sentinel sibling WebUIs still load.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from uuid import uuid4

from playwright.sync_api import sync_playwright

BASE = "https://dbmcpserver0.cloud-dog.net"
OUT = Path("working/w28a-732-r5-reopen/g8-screenshots")
OUT.mkdir(parents=True, exist_ok=True)

# Flat WebUI credentials: admin from Vault/TF-env; read-write/read-only are the
# estate-canonical in-code demo defaults (no Terraform/Vault write).
CREDS = {
    "admin": ("admin", "OrangeRiverTable"),
    "read-write": ("read-write", "BlueRiverChair"),
    "read-only": ("read-only", "GreenRiverDesk"),
}


def status_line(label: str, payload: dict) -> None:
    print(label, json.dumps(payload, sort_keys=True))


def screenshot(page, name: str) -> str:
    path = OUT / f"{name}.png"
    page.screenshot(path=str(path), full_page=True)
    return str(path)


def cookie_fetch(page, path: str, method: str, body: dict | None = None) -> dict:
    """Same-origin fetch using the cookie session only (no X-API-Key)."""
    return page.evaluate(
        """async ({path, method, body}) => {
            const headers = {"Accept": "application/json"};
            let requestBody = undefined;
            if (body !== null) {
                headers["Content-Type"] = "application/json";
                requestBody = JSON.stringify(body);
            }
            const response = await fetch(path, {method, headers, body: requestBody, credentials: "include"});
            const text = await response.text();
            let parsed = null;
            try { parsed = text ? JSON.parse(text) : null; } catch {}
            return {status: response.status, ok: response.ok, json: parsed, text: text.slice(0, 600)};
        }""",
        {"path": path, "method": method, "body": body},
    )


def expect_status(label: str, result: dict, expected: set[int]) -> dict:
    payload = {"status": result["status"], "ok": result["ok"]}
    data = (result.get("json") or {}).get("data") if isinstance(result.get("json"), dict) else None
    if isinstance(data, dict):
        for key in ("user_id", "profile_id", "deleted", "modified_count", "deleted_count", "inserted_count"):
            if key in data:
                payload[key] = data[key]
    status_line(label, payload)
    if result["status"] not in expected:
        raise AssertionError(f"{label} expected {sorted(expected)} got {result['status']}: {result['text']}")
    return result


def login(browser, role: str):
    username, password = CREDS[role]
    context = browser.new_context(ignore_https_errors=True, viewport={"width": 1440, "height": 980})
    page = context.new_page()
    page.goto(f"{BASE}/login", wait_until="domcontentloaded")
    page.locator("input[type='password']").first.wait_for(timeout=15000)
    page.locator("input[type='text'], input:not([type]), input[type='email']").first.fill(username)
    page.locator("input[type='password']").first.fill(password)
    page.locator("button:has-text('Sign in'), button[type='submit']").first.click()
    page.wait_for_function("() => window.location.pathname !== '/login'", timeout=15000)
    me = cookie_fetch(page, "/auth/me", "GET")
    page.evaluate(
        """({role, roles}) => {
            const b = document.createElement("pre");
            b.setAttribute("data-testid", `g8-${role}-role-proof`);
            b.style.cssText = "position:relative;z-index:99999;margin:12px;padding:10px;border:2px solid #1d4ed8;background:#eff6ff;color:#172554;white-space:pre-wrap;";
            b.textContent = `W28A-732-R5 cookie login proof: ${role} -> roles ${JSON.stringify(roles)}`;
            document.body.prepend(b);
        }""",
        {"role": role, "roles": (me.get("json") or {}).get("user", {}).get("roles")},
    )
    shot = screenshot(page, f"g8_{role.replace('-', '_')}_dashboard")
    status_line(f"{role}_auth_me", {"status": me["status"], "roles": (me.get("json") or {}).get("user", {}).get("roles"), "screenshot": shot})
    if me["status"] != 200:
        raise AssertionError(f"{role} /auth/me expected 200 got {me['status']}: {me['text']}")
    return context, page


def sentinel(browser, host: str) -> None:
    context = browser.new_context(ignore_https_errors=True, viewport={"width": 1366, "height": 900})
    page = context.new_page()
    response = page.goto(f"https://{host}.cloud-dog.net/", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(1200)
    status = response.status if response else 0
    shot = screenshot(page, f"g8_sentinel_{host}")
    status_line("sentinel_browser_smoke", {"host": host, "status": status, "screenshot": shot})
    if status == 404 or status >= 500:
        raise AssertionError(f"sentinel {host} returned HTTP {status}")
    context.close()


def main() -> None:
    suffix = uuid4().hex[:8]
    namespace = f"w28a732r_{suffix}"
    entity = "items"
    user_id = None
    profile_id = None

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])

        # runtime-config contract (cookie, never api_key)
        cfg = browser.new_context(ignore_https_errors=True).new_page()
        cfg_text = cfg.evaluate("async () => (await fetch('/runtime-config.js', {cache:'no-store'})).text()") if False else None
        cfg.goto(f"{BASE}/runtime-config.js", wait_until="domcontentloaded")
        body_text = cfg.evaluate("() => document.body.innerText")
        status_line("runtime_config_auth_mode", {"cookie": '"AUTH_MODE": "cookie"' in body_text, "api_key": '"AUTH_MODE": "api_key"' in body_text})
        if '"AUTH_MODE": "cookie"' not in body_text or '"AUTH_MODE": "api_key"' in body_text:
            raise AssertionError(f"runtime-config AUTH_MODE not cookie: {body_text[:200]}")

        # anon login box must render a username + password form (2 inputs)
        anon = browser.new_context(ignore_https_errors=True, viewport={"width": 1440, "height": 980}).new_page()
        anon.goto(f"{BASE}/login", wait_until="domcontentloaded")
        anon.locator("input").first.wait_for(timeout=15000)
        n_inputs = anon.locator("input").count()
        n_pw = anon.locator("input[type='password']").count()
        anon_shot = screenshot(anon, "g8_anon_login_box")
        status_line("anon_login_box", {"inputs": n_inputs, "password_inputs": n_pw, "screenshot": anon_shot})
        anon_me = cookie_fetch(anon, "/auth/me", "GET")
        status_line("anon_auth_me_denied", {"status": anon_me["status"]})
        if n_pw < 1 or n_inputs < 2:
            raise AssertionError(f"anon login box not a username/password form: inputs={n_inputs} pw={n_pw}")
        if anon_me["status"] != 401:
            raise AssertionError(f"anon /auth/me expected 401 got {anon_me['status']}")

        # admin: user + profile CRUD via the cookie /webapi proxy
        admin_ctx, admin_pg = login(browser, "admin")
        try:
            created = expect_status(
                "admin_user_create",
                cookie_fetch(admin_pg, "/webapi/v1/users", "POST", {
                    "username": f"g8_user_{suffix}", "display_name": f"G8 User {suffix}",
                    "email": f"g8_user_{suffix}@example.invalid", "roles": ["analyst"]}),
                {200, 201})
            user_id = created["json"]["data"]["user_id"]
            expect_status("admin_user_get", cookie_fetch(admin_pg, f"/webapi/v1/users/{user_id}", "GET"), {200})
            profile = expect_status(
                "admin_profile_create",
                cookie_fetch(admin_pg, "/webapi/v1/profiles", "POST", {
                    "name": f"g8_profile_{suffix}", "source_type": "mongodb", "source_connection": "default",
                    "description": "W28A-732-R5 reopen G8", "namespaces": [namespace], "entities": [entity],
                    "allowed_permissions": ["catalog.read", "schema.read", "data.read", "data.create", "data.update", "data.delete"]}),
                {200, 201})
            profile_id = profile["json"]["data"]["profile_id"]
        finally:
            admin_ctx.close()

        # read-write: data CRUD via the cookie /webmcp proxy (role key forwarded)
        rw_ctx, rw_pg = login(browser, "read-write")
        try:
            expect_status("read_write_data_create", cookie_fetch(rw_pg, "/webmcp/tools/data.create", "POST", {
                "profile_id": profile_id, "namespace": namespace, "entity": entity,
                "document": {"marker": suffix, "phase": "create", "value": 1}}), {200})
            expect_status("read_write_data_read", cookie_fetch(rw_pg, "/webmcp/tools/data.read", "POST", {
                "profile_id": profile_id, "namespace": namespace, "entity": entity, "filter": {"marker": suffix}, "limit": 5}), {200})
            expect_status("read_write_data_update", cookie_fetch(rw_pg, "/webmcp/tools/data.update", "POST", {
                "profile_id": profile_id, "namespace": namespace, "entity": entity, "filter": {"marker": suffix}, "update": {"$set": {"value": 2}}}), {200})
            expect_status("read_write_data_delete", cookie_fetch(rw_pg, "/webmcp/tools/data.delete", "POST", {
                "profile_id": profile_id, "namespace": namespace, "entity": entity, "filter": {"marker": suffix}}), {200})
        finally:
            rw_ctx.close()

        # read-only: writes denied 403 on BOTH surfaces; reads permitted
        ro_ctx, ro_pg = login(browser, "read-only")
        try:
            webapi_denied = expect_status(
                "read_only_webapi_write_denied",
                cookie_fetch(ro_pg, "/webapi/v1/profiles", "POST", {
                    "name": f"g8_ro_{suffix}", "source_type": "mongodb", "source_connection": "default"}),
                {403})
            mcp_denied = expect_status(
                "read_only_webmcp_write_denied",
                cookie_fetch(ro_pg, "/webmcp/tools/data.create", "POST", {
                    "profile_id": profile_id, "namespace": namespace, "entity": entity, "document": {"x": 1}}),
                {403})
            expect_status(
                "read_only_read_allowed",
                cookie_fetch(ro_pg, "/webapi/v1/config", "GET"),
                {200})
            ro_pg.evaluate(
                """({a, b}) => {
                    const el = document.createElement("pre");
                    el.setAttribute("data-testid", "g8-read-only-403-inline");
                    el.style.cssText = "position:relative;z-index:99999;margin:12px;padding:12px;border:2px solid #b91c1c;background:#fff5f5;color:#7f1d1d;white-space:pre-wrap;";
                    el.textContent = `W28A-732-R5 read-only write probes:\\n/webapi profiles -> HTTP ${a}\\n/webmcp data.create -> HTTP ${b}`;
                    document.body.prepend(el);
                }""",
                {"a": webapi_denied["status"], "b": mcp_denied["status"]},
            )
            status_line("read_only_403_inline_screenshot", {"screenshot": screenshot(ro_pg, "g8_read_only_403_inline")})
        finally:
            ro_ctx.close()

        # cleanup
        cleanup_ctx, cleanup_pg = login(browser, "admin")
        try:
            if user_id:
                expect_status("admin_user_delete", cookie_fetch(cleanup_pg, f"/webapi/v1/users/{user_id}", "DELETE"), {200})
            if profile_id:
                expect_status("admin_profile_delete", cookie_fetch(cleanup_pg, f"/webapi/v1/profiles/{profile_id}", "DELETE"), {200})
        finally:
            cleanup_ctx.close()

        for host in ("chatclient0", "expertagent0", "notificationagent0", "filemcpserver0"):
            sentinel(browser, host)

        browser.close()

    status_line("G8", {"result": "PASS", "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z")})


if __name__ == "__main__":
    main()
