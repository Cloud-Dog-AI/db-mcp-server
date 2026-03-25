# W28A-274-I — Search & Indexing Report

## Verdict
PASS

## Scope
Implemented Phase 1 discovery search and indexing in `/opt/iac/Development/cloud-dog-ai/db-mcp-server`, building on the existing W28A-274-A, W28A-274-B, W28A-274-C, and W28A-274-H-R2 runtime, access-control, connector, and core MCP tool surfaces.

## Delivered
- SQLite FTS5-backed discovery index under `src/core/search/`
- Discovery indexing pipeline that builds profile, namespace, entity, field, relationship-hint, and content-excerpt documents
- Index coverage and freshness metadata per profile and per entity
- Search MCP tools:
  - `search.metadata`
  - `search.content`
  - `search.related`
  - `search.explain_match`
- Index management MCP tools:
  - `index.status`
  - `index.sync_profile`
  - `index.sync_entity`
  - `index.rebuild`
- Managed indexing jobs via `cloud_dog_jobs` using the runtime queue/backend
- Search/indexing test coverage across UT, ST, and IT
- Updated project test inventory and context summary

## Key implementation files
- `src/core/search/models.py`
- `src/core/search/repository.py`
- `src/core/search/indexer.py`
- `src/core/search/service.py`
- `src/core/search/__init__.py`
- `src/servers/mcp/search_tools.py`
- `src/common/runtime.py`
- `src/servers/mcp/app.py`
- `src/core/access_control/models.py`
- `src/core/access_control/schemas.py`
- `defaults.yaml`
- `tests/helpers/core_tools_runtime.py`
- `tests/fixtures/seed_data.py`
- `tests/unit/UT1.9_SearchIndexer/test_search_indexer.py`
- `tests/unit/UT1.10_SearchService/test_search_service.py`
- `tests/system/ST1.7_SearchApi/test_search_api.py`
- `tests/integration/IT1.6_SearchIndexingLifecycle/test_search_indexing_lifecycle.py`
- `docs/TESTS.md`
- `CONTEXT-SUMMARY.md`

## Design summary
- Discovery indexing is kept local and dependency-light with SQLite FTS5 for Phase 1.
- Indexed document kinds are:
  - `profile`
  - `namespace`
  - `entity`
  - `field`
  - `relationship_hint`
  - `content_excerpt`
- Indexing respects profile visibility and profile index policy.
- Search/index management is exposed through MCP tools and uses the same access-control model as the rest of the service.
- Indexing requests are submitted through `cloud_dog_jobs` and then executed inline against the current memory queue backend so the runtime stays honest about job creation and status without inventing an out-of-scope worker subsystem.

## Backwards compatibility
- Added `index_policy` to profile models/schemas with a default empty dictionary. Existing profiles continue to load without migration because repository payload deserialisation now falls back to the dataclass default for the new field.
- Existing API, MCP, runtime, and connector surfaces remained intact.
- The prior QT/UT/ST/IT coverage was rerun after the search/indexing changes and remained green.

## Real issues hit during verification
1. Initial ST1.7 failure
   - Cause: the live test profile did not include `data.create`, so the seeded corpus could not be inserted via `data.create`.
   - Evidence: `working/w28a-274i-st17.log`
   - Fix: added `data.create` to the live search test profile permissions.

2. Initial IT1.6 failure
   - Cause: the live search profile had unrestricted namespace visibility on the shared Mongo host, so `search.related` returned entities from older test databases that were also visible to the connector.
   - Evidence: `working/w28a-274i-it16.log`
   - Fix: constrained the live search tests to a generated namespace via profile `namespaces=[namespace]`.

No application logic was hidden or skipped to get green results. Both failures were surfaced, fixed, and rerun.

## Exact commands run
```bash
cd /opt/iac/Development/cloud-dog-ai/db-mcp-server

venv/bin/python -m compileall src tests start_api_server.py start_web_server.py start_mcp_server.py start_a2a_server.py \
  2>&1 | tee working/w28a-274i-compileall.log

venv/bin/python -m pytest tests/unit/UT1.9_SearchIndexer tests/unit/UT1.10_SearchService \
  --env tests/env-UT -v --tb=short \
  2>&1 | tee working/w28a-274i-ut.log

venv/bin/python -m pytest tests/system/ST1.7_SearchApi \
  --env tests/env-ST -v --tb=short \
  2>&1 | tee working/w28a-274i-st17.log

venv/bin/python -m pytest tests/system/ST1.7_SearchApi \
  --env tests/env-ST -v --tb=short \
  2>&1 | tee working/w28a-274i-st17-rerun.log

set -a; source /opt/iac/Development/cloud-dog-ai/env-vault; set +a
venv/bin/python -m pytest tests/integration/IT1.6_SearchIndexingLifecycle \
  --env tests/env-IT -v --tb=short \
  2>&1 | tee working/w28a-274i-it16.log

set -a; source /opt/iac/Development/cloud-dog-ai/env-vault; set +a
venv/bin/python -m pytest tests/integration/IT1.6_SearchIndexingLifecycle \
  --env tests/env-IT -v --tb=short \
  2>&1 | tee working/w28a-274i-it16-rerun.log

venv/bin/python -m pytest tests/quality --env tests/env-QT -v --tb=short \
  2>&1 | tee working/w28a-274i-qt.log

venv/bin/python -m pytest tests/unit --env tests/env-UT -v --tb=short \
  2>&1 | tee working/w28a-274i-ut-full.log

venv/bin/python -m pytest tests/system --env tests/env-ST -v --tb=short \
  2>&1 | tee working/w28a-274i-st-full.log

set -a; source /opt/iac/Development/cloud-dog-ai/env-vault; set +a
venv/bin/python -m pytest tests/integration --env tests/env-IT -v --tb=short \
  2>&1 | tee working/w28a-274i-it-full.log
```

## Results
- Compile verification: PASS
  - Evidence: `working/w28a-274i-compileall.log`
- Targeted UT: `4 passed in 1.11s`
  - Evidence: `working/w28a-274i-ut.log`
- Targeted ST rerun: `1 passed in 72.72s`
  - Evidence: `working/w28a-274i-st17-rerun.log`
- Targeted IT rerun: `1 passed in 73.97s`
  - Evidence: `working/w28a-274i-it16-rerun.log`
- QT full: `1 passed in 0.04s`
  - Evidence: `working/w28a-274i-qt.log`
- UT full: `20 passed in 3.10s`
  - Evidence: `working/w28a-274i-ut-full.log`
- ST full: `7 passed in 431.04s`
  - Evidence: `working/w28a-274i-st-full.log`
- IT full: `6 passed in 439.03s`
  - Evidence: `working/w28a-274i-it-full.log`

## Behaviour verified
- Discovery index builds from seeded real MongoDB data.
- `search.metadata` finds relevant entity/field matches for natural-language queries such as `customer email`.
- `search.content` finds indexed content excerpts such as seeded customer email values.
- `search.related` returns related entities using indexed relationship hints plus field-name overlap.
- `search.explain_match` identifies which indexed components matched the query.
- `index.status` returns freshness, coverage, entity status, queue state, and job state.
- `index.sync_profile`, `index.sync_entity`, and `index.rebuild` create real jobs through `cloud_dog_jobs` and complete successfully on the current runtime.

## Notes
- Search indexing uses per-tier discovery index files via env overlays to keep QT/UT/ST/IT state isolated.
- The shared Mongo runtime on this host contains prior test databases. The live search tests were intentionally narrowed to a generated namespace to keep assertions specific to the seeded corpus under test.
- No infrastructure, Docker, Terraform, or Vault state was modified in this scope.
- No files outside `/opt/iac/Development/cloud-dog-ai/db-mcp-server` were edited.
