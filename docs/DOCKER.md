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
