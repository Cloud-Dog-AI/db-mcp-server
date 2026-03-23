# PREPROD Deployment — db-mcp-server

## 1. Overview
- Service URL: `https://dbmcp0.cloud-dog.net` (planned)
- Ports: API `8086`, Web `8087`, MCP `8088`, A2A `8089`
- Image: `registry.cloud-dog.net:443/cloud-dog/db-mcp-server:latest` (planned)
- Terraform location: to be allocated in `/opt/iac/cloud-dog-repo/terraform/server0.viewdeck.com/`

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
set -a; source /opt/iac/Development/cloud-dog-ai/env-vault; set +a
vault kv get -mount=cloud_dog_ai config
```

## 5. Deployment Steps
1. Build image with `bash docker-build.sh latest`
2. Tag and push to `registry.cloud-dog.net:443/cloud-dog/db-mcp-server:latest`
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
