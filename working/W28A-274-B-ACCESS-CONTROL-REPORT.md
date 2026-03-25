# W28A-274-B Access Control Report

## Verdict
PASS

## Scope
Implemented the db-mcp-server access-control layer in `/opt/iac/Development/cloud-dog-ai/db-mcp-server` on top of the W28A-274-A runtime skeleton.

## Delivered
- Profile CRUD API at `/api/v1/profiles`
- User CRUD API at `/api/v1/users`
- Group CRUD API at `/api/v1/groups`
- API-key create/list/revoke API at `/api/v1/api-keys`
- Profile-scoped permission enforcement with RBAC and API-key capability scoping
- Field masking and field exclusion rules per profile
- MCP management tool parity for profile, user, group, and API-key management
- Audit logging for create/update/delete/revoke and denied authorisation events
- UT/ST/IT coverage for the new access-control layer

## Key implementation files
- `src/core/access_control/models.py`
- `src/core/access_control/repository.py`
- `src/core/access_control/schemas.py`
- `src/core/access_control/service.py`
- `src/servers/api/access_control.py`
- `src/servers/mcp/access_control_tools.py`
- `src/common/auth.py`
- `src/common/http.py`
- `src/common/runtime.py`
- `src/servers/api/app.py`
- `src/servers/mcp/app.py`
- `defaults.yaml`
- `tests/unit/UT1.3_AccessControlService/test_access_control_service.py`
- `tests/system/ST1.2_AccessControlApi/test_access_control_api.py`
- `tests/integration/IT1.1_AccessControlLifecycle/test_access_control_lifecycle.py`
- `docs/TESTS.md`

## Design summary
- Access-control state is persisted in the metadata store through a SQLAlchemy-backed repository.
- Bootstrap admin identity and bootstrap API key are seeded from config to preserve backwards-compatible admin access.
- Effective permissions are computed from:
  - direct user roles
  - group roles
  - role-to-permission mapping
  - API-key capability scoping
  - profile permission scoping
- Request middleware resolves an authenticated principal and places the principal, roles, permissions, scopes, and profile ids on `request.state`.
- API and MCP surfaces both call the same access-control service for CRUD, permission checks, and audit emission.

## Commands run
```bash
cd /opt/iac/Development/cloud-dog-ai/db-mcp-server
. venv/bin/activate
python -m compileall src start_api_server.py start_mcp_server.py start_web_server.py start_a2a_server.py tests
python -m pytest tests/unit --env tests/env-UT -v --tb=short
python -m pytest tests/system/ST1.2_AccessControlApi --env tests/env-ST -v --tb=short
python -m pytest tests/integration/IT1.1_AccessControlLifecycle --env tests/env-IT -v --tb=short
set -a; source /opt/iac/Development/cloud-dog-ai/env-vault; set +a
python -m pytest tests/ --env tests/env-IT -q --tb=short
python -m pytest tests/ --env tests/env-IT --collect-only -q
```

## Results
- UT: `8 passed`
  - Evidence: `working/w28a-274b-ut.log`
- ST1.2: `1 passed in 77.97s`
  - Evidence: `working/w28a-274b-st12.log`
- IT1.1: `1 passed in 79.92s`
  - Evidence: `working/w28a-274b-it11.log`
- Full suite: `12 passed`
  - Evidence: `working/w28a-274b-tests.log`
- Collect-only inventory: `12 tests`
  - Evidence: `working/w28a-274b-collect.log`

## Behaviour verified
- Unauthenticated access to protected CRUD endpoints returns `401`.
- Least-privilege API keys are denied admin-only actions with `403`.
- Profile masking replaces masked fields and removes excluded fields.
- MCP `/mcp/tools` exposes the new management tool catalogue.
- MCP admin tool execution works with the bootstrap admin API key.
- MCP admin tools reject limited principals with `403`.
- Audit log contains create events and denied authorisation events for admin operations.

## Notes
- The instruction’s example verification command omitted `--env`. I used `--env tests/env-IT` on all pytest runs to comply with the platform rules that require env-file driven execution.
- No connector work, deployment changes, or infrastructure mutation was performed in this scope.
