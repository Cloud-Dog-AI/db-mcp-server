# W28A-274-K — db-mcp-server Test Data + Docker Environments Report

## Verdict
PASS

## Scope
- Project: `/opt/iac/Development/cloud-dog-ai/db-mcp-server`
- Objective: deliver canonical connector test data, per-backend seed modules, Docker test environments, env overlays, and real Mongo verification before remaining connector work.

## Delivered
### Canonical dataset contract
- `tests/fixtures/schema.md`
- `tests/fixtures/canonical_data.py`

### Seed modules
- `tests/fixtures/mongodb_seed.py`
- `tests/fixtures/couchdb_seed.py`
- `tests/fixtures/opensearch_seed.py`
- `tests/fixtures/elasticsearch_seed.py`
- `tests/fixtures/cassandra_seed.py`
- Backwards-compatible Mongo shim retained at `tests/fixtures/seed_data.py`

### Docker environments
- `docker/docker-compose.mongodb.yml`
- `docker/docker-compose.couchdb.yml`
- `docker/docker-compose.opensearch.yml`
- `docker/docker-compose.elasticsearch.yml`
- `docker/docker-compose.cassandra.yml`
- `docker/docker-compose.all.yml`

### Env overlays
- `tests/env-mongodb`
- `tests/env-couchdb`
- `tests/env-opensearch`
- `tests/env-elasticsearch`
- `tests/env-cassandra`
- `tests/env-all`

### Seed orchestration and verification
- `scripts/seed-test-data.sh`
- `tests/fixtures/test_seed_data.py`

## Key implementation notes
1. A single canonical e-commerce dataset now drives every backend seed module.
   - Counts: customers `25`, orders `50`, products `20`, suppliers `10`, invoices `35`
   - Includes strings, numerics, booleans, arrays, dates, nulls, and cross-entity references.
2. Existing Mongo ST/IT compatibility was preserved.
   - `tests/fixtures/seed_data.py` still exports `SEED_COLLECTIONS`, `clone_seed_collections`, and `seed_mongodb`.
3. Mongo Docker seeding had a real host constraint.
   - Initial port-published compose run failed with `Connection reset by peer` from `pymongo`.
   - This host already showed the same behaviour in prior Mongo system work.
   - Fix: switched Mongo compose to host networking on `127.0.0.1:27018`, matching the already-proven stable pattern.
4. `seed-test-data.sh` now clears the old project Mongo helper container and stale compose stacks before startup.
5. `seed-test-data.sh` also ensures missing Python seed dependencies are installed into the project venv before running backend seed modules.

## Commands run
```bash
cd /opt/iac/Development/cloud-dog-ai/db-mcp-server
venv/bin/python -m compileall tests/fixtures scripts
bash -n scripts/seed-test-data.sh
for file in docker/docker-compose.mongodb.yml docker/docker-compose.couchdb.yml docker/docker-compose.opensearch.yml docker/docker-compose.elasticsearch.yml docker/docker-compose.cassandra.yml docker/docker-compose.all.yml; do
  docker compose -f "$file" config >/dev/null
done

./scripts/seed-test-data.sh mongodb
venv/bin/python -m pytest tests/fixtures/test_seed_data.py --env tests/env-mongodb -v --tb=short
```

## Results
- Python compile check: PASS
- Shell syntax check: PASS
- Docker Compose config validation: PASS for all 6 compose files
- Real Mongo seed orchestration: PASS
- Real Mongo fixture verification: `3 passed in 8.50s`

## Evidence
- Mechanical validation: `working/w28a-274k-validation.log`
- Mongo seed orchestration: `working/w28a-274k-seed-mongodb.log`
- Mongo verification test: `working/w28a-274k-test-seed-data.log`

## Constraints and remaining coverage
- Mongo was validated end-to-end on a real local system, as required by pass criteria.
- CouchDB, OpenSearch, Elasticsearch, and Cassandra compose/seed assets are implemented and compose-validated, but not live-verified in this instruction scope.
- The next connector instructions should add live verification for those backends once their adapters land.
