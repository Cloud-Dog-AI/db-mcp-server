# W28A-274-G — Cassandra Connector Report

## Prime Directive Readback

> **I will ONLY do as I am told. I will ONLY implement in 100% compliance to my rules.**
> **I will NOT hack, fudge, workaround, avoid, or lie. If I do, it is 100% FAILURE.**
> **I will WARRANT that ALL my activities are 100% within these instructions and 100% to my rules.**

## Implementation Summary

### Adapter: `src/core/connectors/cassandra/adapter.py`

Full connector contract implementation using `cassandra-driver` 3.29.3. Cassandra is fundamentally different from the search engine connectors — it's a wide-column store with CQL and strongly typed schemas.

All contract methods implemented:

1. `capability_report()` — reports `source_type: "cassandra"`, `content_search: False`, documents CQL filtering limitations
2. `validate_profile()` — queries `system.local` for cluster name
3. `list_namespaces()` — lists non-system keyspaces from `system_schema.keyspaces`
4. `list_entities(namespace)` — lists tables from `system_schema.tables`
5. `describe_entity(namespace, entity)` — table metadata with column schema and row count
6. `describe_fields(namespace, entity)` — CQL column metadata including type, kind (partition_key/clustering/regular/static), and position
7. `read(namespace, entity, filter, projection, sort, limit)` — CQL SELECT with ALLOW FILTERING when needed
8. `create(namespace, entity, document)` — CQL INSERT
9. `update(namespace, entity, filter, update)` — CQL UPDATE with SET/null for $set/$unset
10. `delete(namespace, entity, filter)` — CQL DELETE
11. `count(namespace, entity, filter)` — SELECT COUNT(*)
12. `sample_shapes(namespace, entity, n)` — SELECT LIMIT n
13. `list_indexes(namespace, entity)` — queries `system_schema.indexes`
14. `schema_change_plan/apply(operation)` — CREATE/DROP TABLE and CREATE/DROP INDEX with dry-run
15. `extract_relationships(namespace, entity)` — `*_id` column name inference

### Cassandra-Specific Design Decisions

| Decision | Rationale |
|----------|-----------|
| `content_search: False` | Cassandra has no full-text search capability |
| `ALLOW FILTERING` on non-PK reads | Required for ad-hoc queries; documented in capability notes |
| `_build_where` uses flat equality only | CQL WHERE is restricted to partition/clustering keys for efficient queries |
| Schema from `system_schema.columns` | Authoritative source for CQL types (text, int, double, etc.) |
| `id` instead of `_id` for PK | CQL rejects unquoted identifiers starting with `_` |
| `from_uri()` class method | Allows `cassandra://host:port` URIs like other connectors |

### Files Created/Modified

| File | Action | Description |
|------|--------|-------------|
| `src/core/connectors/cassandra/adapter.py` | Created | Full adapter implementation |
| `src/core/connectors/cassandra/__init__.py` | Updated | Export `CassandraConnector` |
| `src/core/connectors/service.py` | Updated | Cassandra dispatch, builder, error handling |
| `src/core/filters/translator.py` | Updated | Added `CassandraFilterTranslator` (equality-only) |
| `src/core/filters/__init__.py` | Updated | Export new translator |
| `pyproject.toml` | Updated | Added `cassandra-driver>=3.28` to main dependencies |
| `defaults.yaml` | Updated | Added `connectors.cassandra` config section |
| `tests/fixtures/cassandra_seed.py` | Updated | Fixed `_id` → `id`, `USE` → `set_keyspace`, optional auth, `;` splitting |
| `tests/unit/UT1.17_CassandraConnector/test_cassandra_connector.py` | Created | Unit tests with mocked Cluster/Session |
| `tests/system/ST1.13_CassandraConnector/test_cassandra_connector_real.py` | Created | System test against real Cassandra |

### Dependencies Added

- `cassandra-driver>=3.28` (installed: 3.29.3)

## Test Results

### UT — Unit Tests

```
tests/unit/UT1.17_CassandraConnector/test_cassandra_connector.py
  test_adapter_capabilities_and_catalogue_calls  PASSED
  test_adapter_data_and_schema_operations        PASSED
```

**2 passed, 0 failed, 0 skipped.**

### Full UT Regression

```
34 passed in 3.18s
```

**34 passed, 0 failed, 0 skipped.** No regressions.

### ST — System Tests

```
tests/system/ST1.13_CassandraConnector/test_cassandra_connector_real.py
  test_cassandra_adapter_against_real_runtime  PASSED
```

**1 passed, 0 failed, 0 skipped.** Tested against real Cassandra at `cassandra0.app.vpc0.cloud-dog.net:9042`.

Verified operations:
- Namespace listing (found `dbmcp_ecommerce` keyspace)
- Entity listing (found `customers`, `orders`, etc.)
- Field description with CQL types and partition key metadata
- Count, sample, read with partition key filter
- Full CRUD cycle (create → read → update → verify → delete)
- Relationship inference (`customer_id`, `product_id`, `supplier_id`)
- Schema change (CREATE TABLE, CREATE INDEX, DROP TABLE)

### IT — Integration Tests

Not created in this iteration — requires MCP server running with Cassandra profile support integrated. The IT test structure will mirror `tests/integration/IT1.9_OpenSearchMcpTools/`.

## Vault Verification (§11)

Vault path verified:
```json
{
  "host": "cassandra0.app.vpc0.cloud-dog.net",
  "port": "9042",
  "type": "cassandra"
}
```

Path: `dev.databases.providers.cassandra` — confirmed present. No auth credentials stored (unauthenticated access).

## RULES.md COMPLIANCE WARRANTY

I warrant that:
1. I have read RULES.md IN FULL before starting work
2. ALL code I produced is 100% compliant with EVERY section of RULES.md
3. ALL tests I produced or modified are 100% compliant with RULES.md § 5
4. ALL ST/IT/AT tests use REAL systems — ZERO stubs, mocks, or fake data (§ 5.5)
5. ZERO hardcoded values exist in my code, tests, or scripts (§ 2.4)
6. ALL credentials come from Vault or git-ignored private/ env files — ZERO stored credentials (§ 2.3, § 9.2)
7. I have NOT modified any file outside my project folder (§ 9.1)
8. I have NOT accessed any server not explicitly provided (§ 9.3)
9. I have NOT stored, copied, or exposed any credentials (§ 9.2)
10. ALL test results reported are REAL — exact pass/fail/skip counts from actual runs
11. I have NOT modified any infrastructure file without explicit instruction (§ 10)
12. ALL Vault paths I referenced were verified against live Vault before use (§ 11)
13. ALL requirements I claimed as "implemented" have working code and passing tests — no stubs, no placeholders (§ 12)

**Exceptions and honest disclosures:**
- IT test NOT CREATED — requires MCP server integration with Cassandra profile support
- The Cassandra seed uses `id` instead of `_id` because CQL rejects unquoted identifiers starting with `_`

If ANY of the above cannot be truthfully stated, this warranty is VOID,
the completion claim is REJECTED, and ALL work must be reviewed.
