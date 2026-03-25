# W28A-274-L — Schema Change Tools Report

## Verdict
- PASS

## Scope
- Project: `/opt/iac/Development/cloud-dog-ai/db-mcp-server`
- Objective: implement schema change planning, approval-gated apply, persisted history, audit trail, and discovery index refresh, with MongoDB as the required working connector.

## Delivered
- Added schema-change core package:
  - `src/core/schema/models.py`
  - `src/core/schema/repository.py`
  - `src/core/schema/service.py`
  - `src/core/schema/__init__.py`
- Wired runtime registration in `src/common/runtime.py`
- Replaced thin connector passthrough MCP handlers in `src/servers/mcp/schema_tools.py`
  - `schema.change.plan`
  - `schema.change.apply`
  - `schema.change.history`
- Expanded MongoDB schema support in `src/core/connectors/mongodb/adapter.py`
  - `create_entity`
  - `drop_entity`
  - `create_index`
  - `drop_index`
  - richer dry-run `before_state` and `after_state`
- Added test coverage:
  - `tests/unit/UT1.12_SchemaChangeService/test_schema_change_service.py`
  - updated `tests/unit/UT1.4_MongoDBConnector/test_mongodb_connector.py`
  - updated `tests/system/ST1.6_SchemaApi/test_schema_api.py`
  - `tests/integration/IT1.7_SchemaChangeLifecycle/test_schema_change_lifecycle.py`
- Updated inventory/docs:
  - `docs/TESTS.md`
  - `CONTEXT-SUMMARY.md`

## Design Summary
- Schema changes now persist in a metadata-backed `schema_change_history` table.
- Plan and apply are no longer raw connector calls from the MCP tool layer.
- Each plan gets a stable `plan_id` and explicit audit IDs:
  - `<plan_id>:plan`
  - `<plan_id>:apply`
  - `<plan_id>:apply-state`
- Apply is approval-gated.
- Successful apply triggers discovery refresh:
  - `index.sync_entity` for entity/index changes
  - `index.sync_profile` for entity drops
- History exposes the persisted plan, result, and audit-trail references.

## Backwards Compatibility
- Preserved existing top-level plan keys used by prior tests and clients:
  - `operation`
  - `namespace`
  - `entity`
  - `parameters`
  - `dry_run`
- Preserved `applied` in apply responses.
- Extended the response shape additively with:
  - `plan_id`
  - `requires_approval`
  - `audit_event_id`
  - `index_refresh_triggered`
  - `audit_trail`
  - `result`

## Commands Run
```bash
cd /opt/iac/Development/cloud-dog-ai/db-mcp-server
venv/bin/python -m compileall src tests
venv/bin/python -m pytest tests/unit/UT1.4_MongoDBConnector/test_mongodb_connector.py tests/unit/UT1.12_SchemaChangeService/test_schema_change_service.py --env tests/env-UT -q
timeout 600 venv/bin/python -m pytest tests/system/ST1.6_SchemaApi/test_schema_api.py --env tests/env-ST -v --tb=short
timeout 600 venv/bin/python -m pytest tests/integration/IT1.7_SchemaChangeLifecycle/test_schema_change_lifecycle.py --env tests/env-IT -v --tb=short
venv/bin/python -m compileall src tests 2>&1 | tee working/w28a-274l-compileall.log
venv/bin/python -m pytest tests/quality tests/unit --env tests/env-UT -v --tb=short 2>&1 | tee working/w28a-274l-qt-ut.log
timeout 1200 venv/bin/python -m pytest tests/system --env tests/env-ST -v --tb=short 2>&1 | tee working/w28a-274l-st.log
timeout 1200 venv/bin/python -m pytest tests/integration --env tests/env-IT -v --tb=short 2>&1 | tee working/w28a-274l-it.log
```

## Validation Results
- Compile: PASS
  - Evidence: `working/w28a-274l-compileall.log`
- QT + UT: `27 passed in 3.30s`
  - Evidence: `working/w28a-274l-qt-ut.log`
- ST full: `8 passed in 501.45s`
  - Evidence: `working/w28a-274l-st.log`
- IT full: `7 passed in 506.19s`
  - Evidence: `working/w28a-274l-it.log`

## MongoDB Capability Status
- Required pass criteria met for MongoDB.
- Verified live operations:
  - plan `create_index`
  - apply `create_index`
  - history retrieval with persisted audit identifiers
  - discovery refresh after apply
- Connector also now supports entity create/drop for future tests.

## Audit Trail Evidence
- Apply returns a real `audit_event_id` ending in `:apply-state`.
- IT1.7 verifies the corresponding JSONL audit event exists and contains:
  - `event_type == admin.schema.change`
  - `approval_status == approved`
  - populated `new_value` after-state payload

## Notes
- One initial IT attempt failed because ST and IT were started in parallel and both tried to claim the same fixed Docker container name `db-mcp-server-test-mongo6` used by the shared Mongo test helper.
- This was an execution collision, not a product defect. All final validation was rerun serially and passed.

## Pass Criteria Check
- Schema change plan/apply works for at least MongoDB: PASS
- Audit trail written for every change: PASS
- Index refresh triggered after changes: PASS
- All tests green: PASS
- Report written to `working/W28A-274-L-SCHEMA-CHANGE-REPORT.md`: PASS
