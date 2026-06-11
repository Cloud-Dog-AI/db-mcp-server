# W28A-732-R5 (reopen) — FINAL REPORT

Lane: W28A-732-R5 db-mcp WebUI login-contract reopen
Service: db-mcp-server  Host: dbmcpserver0.cloud-dog.net
Date: 2026-06-11

## Outcome
The failed API-key-only WebUI login contract is replaced with the platform flat
username/password (cookie) login. Proven LIVE on dbmcpserver0.

- origin/main = 8455944 (login fix 6b41809 + MCP role-key fix 8455944)
- Deployed registry digest = sha256:8d06acbcc4fd5b18f8f4f5560747ae0108cd1a60e47ed5018d8661a0445065b6
- Two-anchor tags: W28A-732-R5-reopen-evidence, W28A-732-R5-reopen-final-proof (both -> 8455944 == origin/main)

## Live G8 (browser, Playwright) — PASS
- runtime-config AUTH_MODE = cookie (api_key absent)
- anon /login renders Username + Password Sign-in form (inputs=2, password=1)
- anon /auth/me = 401
- admin / read-write / read-only username+password login = 200 with correct roles
- read-write data create/read/update/delete = 200 (via cookie /webmcp, role key forwarded)
- read-only write = 403 on BOTH /webapi (web-tier block) and /webmcp (MCP role RBAC)
- read-only read = 200
- admin user + profile CRUD = 200; cleanup deletes = 200
- 4 sentinel sibling WebUIs = 200
- 9 screenshots captured, non-blank, all-unique MD5

## Tests
UT 86 (incl. new UT1.52 flat-login contract), QT 4, ST login/auth green, IT1.1 1, AT login 2. Zero failures.

## Deploy
Targeted terraform apply (operator-authorised "FIX IT"): docker_image.dbmcpserver +
docker_container.dbmcpserver0 via the sanctioned tcp://server0.viewdeck.com:2375 docker
provider; consul backend. No Vault writes; no tfvars change (read-write/read-only use
in-code demo passwords).

HAVE_ALL_REQUIREMENTS_BEEN_MET: YES
WAIVER_COUNT=0
