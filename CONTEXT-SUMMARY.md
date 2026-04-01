# db-mcp-server — Context Summary

## Current baseline

- Repo: `/opt/iac/Development/cloud-dog-ai/db-mcp-server`
- Workspace HEAD used for the latest completed work: `dcdbff637ebee7751b15b93f6ec9fc8228445540`
- Latest completed instruction: `W28A-512`
- Latest W28A-512 report: `/opt/iac/Development/cloud-dog-ai/db-mcp-server/working/W28A-512-FIX-E2E-GAPS-REPORT.md`

## What W28A-512 changed

- Added requirement documentation in `/opt/iac/Development/cloud-dog-ai/db-mcp-server/docs/REQUIREMENTS.md`:
  - `CO-05` for the 16 documented filter operators plus `and`/`or`/`not`
  - `CO-06` for MongoDB binary/blob handling
  - `AC-04` for the 5 built-in RBAC roles
  - `AC-05` and `AC-06` for admin-only user/group/API-key CRUD
- Added real ST coverage in `/opt/iac/Development/cloud-dog-ai/db-mcp-server/tests/system/ST1.5_ContentApi/test_content_api.py`:
  - `test_content_tools_support_all_documented_filter_operators`
  - `test_content_tools_round_trip_binary_fields`
- Fixed a real binary-path defect that was discovered during W28A-512 verification:
  - `/opt/iac/Development/cloud-dog-ai/db-mcp-server/src/servers/mcp/content_tools.py`
  - `/opt/iac/Development/cloud-dog-ai/db-mcp-server/src/core/connectors/mongodb/adapter.py`
  - Binary envelopes now coerce on create/update, binary fields normalise safely on read, and schema describe reports `binary`
- Updated stale Playwright expectations in `/opt/iac/Development/cloud-dog-ai/db-mcp-server/tests/application/AT_WEBUI_E2E/test_webui_e2e.py` to match the current SPA

## Latest verified results

- Targeted ST:
  - `tests/system/ST1.5_ContentApi/test_content_api.py`
  - Result: `3 passed in 261.64s`
- Targeted AT:
  - `tests/application/AT_WEBUI_E2E/test_webui_e2e.py`
  - Result: `17 passed in 223.58s`
- Full regression:
  - Command: `venv/bin/python -m pytest tests/ -v --env tests/env-AT --tb=short`
  - Result: `87 passed in 1736.66s (0:28:56)`

## Latest deploy state

- Docker build completed via `bash docker-build.sh`
- Local image ID:
  - `sha256:c0cad54fbec5da75a425737f015bf2c67d95f2597cd4de51cc177ac9509fce1b`
- Pushed registry image:
  - `registry.cloud-dog.net:443/cloud-dog/db-mcp-server:latest`
- Latest pushed digest:
  - `sha256:9783fc2dc65c018167fed8fc1d5540817263da8e0aeab4305cf9460256cd9f01`
- Terraform working dir:
  - `/opt/iac/cloud-dog-repo/terraform/server0.viewdeck.com/27 MLAgents`
- Latest deploy used scoped Terraform only:
  - `terraform plan -target=docker_image.dbmcpserver -target=docker_container.dbmcpserver0 -out=w28a-512.tfplan`
  - `terraform apply -auto-approve w28a-512.tfplan`
- Apply result:
  - `Apply complete! Resources: 2 added, 0 changed, 2 destroyed.`

## Current preprod state

- Health endpoint:
  - `https://dbmcpserver0.cloud-dog.net/health`
  - Last result: `200`
- W28A-512 preprod verification passed against the deployed service:
  - temporary profile on live default Mongo connector
  - `catalog.list_namespaces`
  - `catalog.list_entities`
  - all 16 documented filter operators
  - binary 50 KiB create/read
  - binary 500 KiB update/read
  - `schema.describe_fields` => `payload.types == ["binary"]`
  - `index.sync_profile` + `search.metadata`
  - cleanup verified; no leftover `w28a-512-preprod-*` profiles

## Important route quirks on preprod

- Public API routing is not uniform:
  - `https://dbmcpserver0.cloud-dog.net/api/v1/...` returned `404` in the latest verification
  - `https://dbmcpserver0.cloud-dog.net/webapi/v1/...` worked for authenticated CRUD/list calls
  - `https://dbmcpserver0.cloud-dog.net/v1/ping` and `https://dbmcpserver0.cloud-dog.net/api/api/v1/ping` also returned `200`
- MCP verification was run against:
  - `https://dbmcpserver0.cloud-dog.net/mcp/tools/...`
- A2A health previously worked at:
  - `https://dbmcpserver0.cloud-dog.net/weba2a/health`

If another agent needs to do live verification, reuse the exact working public paths above instead of assuming `/api/v1` works externally.

## Files currently modified by the latest completed instruction

- `/opt/iac/Development/cloud-dog-ai/db-mcp-server/docs/REQUIREMENTS.md`
- `/opt/iac/Development/cloud-dog-ai/db-mcp-server/src/servers/mcp/content_tools.py`
- `/opt/iac/Development/cloud-dog-ai/db-mcp-server/src/core/connectors/mongodb/adapter.py`
- `/opt/iac/Development/cloud-dog-ai/db-mcp-server/tests/system/ST1.5_ContentApi/test_content_api.py`
- `/opt/iac/Development/cloud-dog-ai/db-mcp-server/tests/application/AT_WEBUI_E2E/test_webui_e2e.py`
- `/opt/iac/Development/cloud-dog-ai/db-mcp-server/working/W28A-512-FIX-E2E-GAPS-REPORT.md`

## Important constraints to preserve

- Do not use SSH
- Do not touch firewall, iptables, Shorewall, Docker networking, or firewall Terraform
- Use `server_control.sh` for local server lifecycle
- Use `--env tests/env-<TIER>` for tests
- Do not bypass `cloud_dog_config`
- For deploys, use Docker build/push plus scoped Terraform only unless the user explicitly broadens scope

## Recommended next-agent starting point

1. Read `/opt/iac/Development/cloud-dog-ai/db-mcp-server/working/W28A-512-FIX-E2E-GAPS-REPORT.md`
2. Read the modified files listed above
3. If live verification is needed, reuse:
   - API: `https://dbmcpserver0.cloud-dog.net/webapi/v1/...`
   - MCP: `https://dbmcpserver0.cloud-dog.net/mcp/tools/...`
4. If local confidence is needed, rerun:
   - `venv/bin/python -m pytest tests/system/ST1.5_ContentApi/test_content_api.py -v --env tests/env-ST --tb=short`
   - `venv/bin/python -m pytest tests/application/AT_WEBUI_E2E/test_webui_e2e.py -v --env tests/env-AT --tb=short`
   - `venv/bin/python -m pytest tests/ -v --env tests/env-AT --tb=short`
