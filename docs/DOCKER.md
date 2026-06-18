---
template-id: T-DOK
template-version: 1.0
applies-to: docs/DOCKER.md
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

# Docker Guide

## Build
```bash
docker build -t db-mcp:latest .
```

## Run
```bash
docker run --rm -it --env-file .env -p 8080:8080 -p 8081:8081 -p 8082:8082 -p 8083:8083 db-mcp:latest
```

## Push
```bash
docker tag db-mcp:latest registry.example.com/your-team/db-mcp:latest
docker push registry.example.com/your-team/db-mcp:latest
```

## Compose Files
- `docker/docker-compose.all.yml`
- `docker/docker-compose.cassandra.yml`
- `docker/docker-compose.couchdb.yml`
- `docker/docker-compose.elasticsearch.yml`
- `docker/docker-compose.mongodb.yml`
- `docker/docker-compose.opensearch.yml`
- `docker-compose.yml`

## Notes
- Keep secrets out of committed compose files and environment examples.
- Use `docs/DEPLOY.md` for Vault-backed runs and custom CA certificate instructions.
