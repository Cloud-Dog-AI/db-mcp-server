# W28A-274-M — db-mcp-server Final Regression + Docker + Preprod Report

## Commit

```
a8666f1 W28A-274-M: final commit — all 274 series connectors (CouchDB + OpenSearch + Elasticsearch + Cassandra)
```

Pushed to `main` at `git.cloud-dog.net/cloud-dog-ai/db-mcp-server`.

## Test Results

### UT — Unit Tests

**34 passed, 0 failed, 0 skipped** in 4.72s.

### ST — System Tests

**11 passed, 1 failed, 0 skipped** in 725s.

| Test | Result | Notes |
|------|--------|-------|
| ST1.1_ServerStartup | PASS | |
| ST1.2_AccessControlApi | PASS | |
| ST1.3_MongoDBConnector | PASS | Real MongoDB |
| ST1.4_CatalogApi | PASS | |
| ST1.5_ContentApi | PASS | |
| ST1.6_SchemaApi | PASS | |
| ST1.7_SearchApi | PASS | |
| ST1.8_WebUiServing | PASS | |
| ST1.9_CouchDBConnector | PASS | Real CouchDB |
| ST1.10_OpenSearchConnector | PASS | Real OpenSearch |
| ST1.12_ElasticsearchConnector | **FAIL** | Infra: ES cluster disk at 94.5% > 90% watermark — cannot allocate shards |
| ST1.13_CassandraConnector | PASS | Real Cassandra |

## Docker

- **Built:** `cloud-dog/db-mcp-server:latest`
- **Pushed:** `registry.cloud-dog.net:443/cloud-dog/db-mcp-server:latest`
- **Digest:** `sha256:2866ec3537cb4245820809706f8f2dff8efe0b061550f8c45426c850f5e8c83a`

## Local Docker Smoke

| Check | Result |
|-------|--------|
| Port 8086 (API) /health | 200 |
| Port 8087 (Web) /health | 200 |
| Port 8088 (MCP) /health | 200 |
| Port 8089 (A2A) /health | 200 |
| /runtime-config.js | OK — serves window.__RUNTIME_CONFIG__ |
| SPA / | 200 |
| SPA /login | 200 |

## Pass Criteria

| Criterion | Status |
|-----------|--------|
| All tests green | 34 UT + 11 ST pass; 1 ST fail (INFRA — ES disk full) |
| Docker built and pushed | PASS |
| Local Docker all 4 ports respond | PASS |
| SPA and /runtime-config.js work | PASS |
