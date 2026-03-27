# W28A-409 — db-mcp-server Preprod Deployment Report

## Prime Directive Readback

> **I will ONLY do as I am told. I will ONLY implement in 100% compliance to my rules.**
> **I will NOT hack, fudge, workaround, avoid, or lie. If I do, it is 100% FAILURE.**
> **I will WARRANT that ALL my activities are 100% within these instructions and 100% to my rules.**

## Terraform Configuration

All Terraform files were already in place:
- `dbmcpserver_containers.tf.json` — complete with all env vars, Traefik labels, health check, firewall rules
- `terraform.tfvars` — ports 8080-8083, API keys
- `variables.tf` — all 6 variables declared
- `docker_images.tf.json` — image reference to `registry.cloud-dog.net:443/cloud-dog/db-mcp-server:latest`

## Docker Image Fix

The container was running but **unhealthy** — `curl: not found` in the health check. Fixed:
- Added `curl` to Dockerfile via `apt-get install -y --no-install-recommends curl`
- Rebuilt and pushed: `sha256:bcf1bfe989c4f088a0e592ea6663581df0a0538fe7b64f33b170a982395e8f04`
- Committed as `f696ed9`

## Deployment

```
terraform apply -auto-approve -target=docker_image.dbmcpserver -target=docker_container.dbmcpserver0
Apply complete! Resources: 2 added, 0 changed, 2 destroyed.
```

Container status after deploy: **Up (healthy)**

## Endpoint Verification (via Traefik, --resolve to proxy1)

| Endpoint | Expected | Actual | Status |
|----------|----------|--------|--------|
| `/health` | 200 | 200 | PASS |
| `/login` | 200 | 200 | PASS |
| `/mcp/health` | 200 | 200 | PASS |
| `/api/profiles` (no auth) | 401 | 401 | PASS |
| `/runtime-config.js` | serves config | serves config | PASS |

## runtime-config.js Issue

The runtime-config.js uses `http://dbmcpserver0.cloud-dog.net` (plaintext HTTP). It should use `window.location.origin` or `https://`. This matches the pattern seen in notification-agent/expert-agent/chat-client (W28A-400 scope).

## DNS — REQUIRES MANUAL ACTION

`dbmcpserver0.cloud-dog.net` does **not** resolve via DNS. Other services use CNAMEs:
```
notificationagent0.cloud-dog.net → proxy1.dmz.vpc0.cloud-dog.net (10.26.10.10)
```

**Required:** Create CNAME `dbmcpserver0.cloud-dog.net → proxy1.dmz.vpc0.cloud-dog.net`

DNS is managed outside the Terraform workspace — no DNS provider configured.

## Test Database Seeding

| Backend | Database/Index | Documents | Status |
|---------|---------------|-----------|--------|
| MongoDB | `cloud_dog_test_db.test_items` | 3 | SEEDED |
| CouchDB | `cloud_dog_test_db` | 2 | SEEDED |
| OpenSearch | `cloud_dog_test_db` index | 1 | SEEDED |
| Cassandra | `cloud_dog_test_db.test_items` | 3 | SEEDED |
| Elasticsearch | (skipped) | — | BLOCKED — disk at 94.5% |

## Profile Creation

Profiles not yet created via API — DNS must resolve first for the public URL, or profiles can be created via the internal API port. This is deferred pending DNS creation.

## RULES.md COMPLIANCE WARRANTY

I warrant that:
1. I have read RULES.md IN FULL before starting work
2. ALL code I produced is 100% compliant with EVERY section of RULES.md
3. ALL tests I produced or modified are 100% compliant with RULES.md § 5
4. ALL ST/IT/AT tests use REAL systems — ZERO stubs, mocks, or fake data (§ 5.5)
5. ZERO hardcoded values exist in my code, tests, or scripts (§ 2.4)
6. ALL credentials come from Vault or git-ignored private/ env files — ZERO stored credentials (§ 2.3, § 9.2)
7. I have NOT modified any file outside my project folder without authorisation (§ 9.1) — Terraform modification was explicitly authorised
8. I have NOT accessed any server not explicitly provided (§ 9.3)
9. I have NOT stored, copied, or exposed any credentials (§ 9.2)
10. ALL test results reported are REAL — exact pass/fail/skip counts from actual runs
11. I have NOT modified any infrastructure file without explicit instruction (§ 10) — Terraform and Dockerfile modifications were explicitly instructed
12. ALL Vault paths I referenced were verified against live Vault before use (§ 11)
13. ALL requirements I claimed as "implemented" have working code and passing tests — no stubs, no placeholders (§ 12)

If ANY of the above cannot be truthfully stated, this warranty is VOID,
the completion claim is REJECTED, and ALL work must be reviewed.
