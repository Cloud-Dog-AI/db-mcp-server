---
template-id: T-PRE
template-version: 1.0
applies-to: docs/PREPROD.md
registry: service
required: must-have
when-applicable: ""
template-last-updated: 2026-06-12
template-owner: platform-standards

project: db-mcp-server
doc-last-updated: 2026-06-18T00:00:00Z
doc-git-commit: 58fb399bb2ba144e262f97293103a7a0a19ba05d
doc-git-branch: main
doc-source-shas: []
doc-age-policy: 90d
doc-conformance-stamp: 2026-06-18T00:00:00Z
---

# PREPROD Deployment — db-mcp-server

## 1. Overview
- Service URL: `https://dbmcp0.your-domain.com` (planned)
- Ports: API `8086`, Web `8087`, MCP `8088`, A2A `8089`
- Image: `registry.example.com/cloud-dog/db-mcp-server:latest` (planned)
- Terraform location: to be allocated in `terraform/`

## 2. Configuration
Preprod configuration will layer:
- container env vars
- `private/env-PREPROD`
- `config.yaml`
- `defaults.yaml`
- Vault-backed expressions

Key groups:
- server settings
- metadata store
- connector credentials
- RBAC and auth
- job worker and indexing settings

## 3. Preprod-Specific Overrides
Expected preprod overrides:
- external base URLs
- metadata store URI
- connector endpoints and credentials
- API/web credentials
- job backend and indexing backend

## 4. Vault Configuration
Expected Vault paths:
- `dev.services.dbmcpserver0`
- `dev.databases.*`
- `dev.vdbs.*`
- `dev.models.*`

Populate with:
```bash
set -a; source .env.local
vault kv get -mount=cloud_dog_ai config
```

## 5. Deployment Steps
1. Build image with `bash docker-build.sh latest`
2. Tag and push to `registry.example.com/cloud-dog/db-mcp-server:latest`
3. Apply Terraform once deployment files exist
4. Verify `GET /health`

## 6. Testing Against Preprod
Planned preprod validation:
- ST health and startup checks
- limited IT profile and discovery checks
- non-destructive AT operator flows

## 7. Troubleshooting
- check Traefik routing
- check Vault resolution
- check metadata store connectivity
- check connector health per source
