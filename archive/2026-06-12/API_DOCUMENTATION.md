# API Documentation

## Base URLs
- Local development: `http://localhost:8083`
- Deployed: `https://db-mcp.your-domain.com`

## Authentication
Use `Authorization: Bearer <your-api-key>` for API, MCP, and A2A requests; web access uses the configured admin login flow.

## Verification Basis
- Source files reviewed: `start_a2a_server.py`, `start_api_server.py`, `start_mcp_server.py`, `start_web_server.py`
- Route inventory size: 31

## Route Inventory
| Method | Path | Notes |
|--------|------|-------|
| GET | `/` | Handler `root` in `src/servers/a2a/app.py`. |
| GET | `/` | Handler `root` in `src/servers/mcp/app.py`. |
| POST | `/auth/login` | Handler `auth_login` in `src/servers/web/app.py`. |
| GET | `/auth/me` | Handler `auth_me` in `src/servers/web/app.py`. |
| POST | `/auth/logout` | Handler `auth_logout` in `src/servers/web/app.py`. |
| GET | `/runtime-config.js` | Handler `runtime_config` in `src/servers/web/app.py`. |
| GET | `/` | Handler `root` in `src/servers/web/app.py`. |
| GET | `/robots.txt` | Handler `robots` in `src/servers/web/app.py`. |
| GET | `/{path:path}` | Handler `spa` in `src/servers/web/app.py`. |
| GET | `/profiles` | Handler `list_profiles` in `src/servers/api/access_control.py`. |
| POST | `/profiles` | Handler `create_profile` in `src/servers/api/access_control.py`. |
| GET | `/profiles/{profile_id}` | Handler `get_profile` in `src/servers/api/access_control.py`. |
| PUT | `/profiles/{profile_id}` | Handler `update_profile` in `src/servers/api/access_control.py`. |
| DELETE | `/profiles/{profile_id}` | Handler `delete_profile` in `src/servers/api/access_control.py`. |
| POST | `/profiles/{profile_id}/mask-preview` | Handler `mask_preview` in `src/servers/api/access_control.py`. |
| GET | `/profiles/{profile_id}/authorise/{permission}` | Handler `profile_authorise` in `src/servers/api/access_control.py`. |
| GET | `/users` | Handler `list_users` in `src/servers/api/access_control.py`. |
| POST | `/users` | Handler `create_user` in `src/servers/api/access_control.py`. |
| GET | `/users/{user_id}` | Handler `get_user` in `src/servers/api/access_control.py`. |
| PUT | `/users/{user_id}` | Handler `update_user` in `src/servers/api/access_control.py`. |
| DELETE | `/users/{user_id}` | Handler `delete_user` in `src/servers/api/access_control.py`. |
| GET | `/groups` | Handler `list_groups` in `src/servers/api/access_control.py`. |
| POST | `/groups` | Handler `create_group` in `src/servers/api/access_control.py`. |
| GET | `/groups/{group_id}` | Handler `get_group` in `src/servers/api/access_control.py`. |
| PUT | `/groups/{group_id}` | Handler `update_group` in `src/servers/api/access_control.py`. |
| DELETE | `/groups/{group_id}` | Handler `delete_group` in `src/servers/api/access_control.py`. |
| GET | `/api-keys` | Handler `list_api_keys` in `src/servers/api/access_control.py`. |
| POST | `/api-keys` | Handler `create_api_key` in `src/servers/api/access_control.py`. |
| POST | `/api-keys/{api_key_id}/revoke` | Handler `revoke_api_key` in `src/servers/api/access_control.py`. |
| GET | `/ping` | Handler `ping` in `src/servers/api/app.py`. |
| GET | `/jobs/health` | Handler `jobs_health` in `src/servers/api/app.py`. |

## Example Request
```bash
curl -H "Authorization: Bearer your-api-key" http://localhost:8083/health
```

## Example Response
```json
{
  "ok": true,
  "result": {
    "status": "healthy"
  }
}
```
