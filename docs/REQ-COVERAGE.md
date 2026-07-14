---
template-id: T-RCM
template-version: 1.0
applies-to: docs/REQ-COVERAGE.md
project: db-mcp-server
doc-last-updated: 2026-07-14T16:08:12.686674+00:00
doc-git-commit: e308bec871dbef170ecfbf73c7eb725b1845e05b
doc-git-branch: HEAD
doc-age-policy: 30d
doc-conformance-stamp: 2026-07-14T16:08:12.686674+00:00
generated-by: scripts/generate-req-coverage.py
---

# db-mcp-server — REQ-COVERAGE

> **Template version:** T-RCM v1.0 — script-generated, do not hand-edit.
> Re-generate via: `scripts/generate-req-coverage.py db-mcp-server`

## 1. Latest generation

- **Generated at:** 2026-07-14T16:08:12.686674+00:00
- **Source REQ commit:** d101e34
- **Source TEST commit:** a9a6ee4

## 2. Coverage summary

| Total REQs | Covered (passing) | Covered (failing) | Covered (stale >90d) | Covered (bound/no run) | NO-TEST |
|---|---|---|---|---|---|
| 44 | 0 | 0 | 0 | 44 | 0 |

- **Passing coverage %** (passing / total) = **0.0%**
- **Bound coverage %** (any bound test, i.e. not NO-TEST) = **100.0%**

## 3. Per-REQ matrix

| REQ-ID | Surface | Priority | Tests | Last-run status | Last-run commit | Age (days) | Coverage state |
|---|---|---|---|---|---|---|---|
| CS-001 | api, mcp, a2a, webui | — | tests/unit/UT1.52_FlatLoginContract/test_flat_login_contract.py, tests/unit/UT1.52_FlatLoginContract/test_flat_login_contract.py | — | — | — | COVERED-BOUND |
| CS-002 | api, mcp | — | tests/unit/UT1.22_TestDataSeed/test_test_data_seed_api.py | — | — | — | COVERED-BOUND |
| CS-003 | api | — | tests/unit/UT1.22_TestDataSeed/test_test_data_seed_api.py | — | — | — | COVERED-BOUND |
| CS-004 | mcp | — | tests/unit/UT1.22_TestDataSeed/test_test_data_seed_api.py | — | — | — | COVERED-BOUND |
| CS-005 | api | — | tests/unit/UT1.52_FlatLoginContract/test_flat_login_contract.py | — | — | — | COVERED-BOUND |
| CS-006 | mcp | — | tests/unit/UT1.52_FlatLoginContract/test_flat_login_contract.py | — | — | — | COVERED-BOUND |
| CS-007 | a2a | — | tests/unit/UT1.52_FlatLoginContract/test_flat_login_contract.py | — | — | — | COVERED-BOUND |
| CS-008 | webui | — | tests/unit/UT1.52_FlatLoginContract/test_flat_login_contract.py | — | — | — | COVERED-BOUND |
| CS-009 | api | — | tests/unit/UT1.22_TestDataSeed/test_test_data_seed_api.py | — | — | — | COVERED-BOUND |
| CS-010 | mcp | — | tests/unit/UT1.22_TestDataSeed/test_test_data_seed_api.py | — | — | — | COVERED-BOUND |
| CS-011 | a2a | — | tests/unit/UT1.22_TestDataSeed/test_test_data_seed_api.py | — | — | — | COVERED-BOUND |
| CS-012 | webui | — | tests/unit/UT1.52_FlatLoginContract/test_flat_login_contract.py | — | — | — | COVERED-BOUND |
| CS-013 | api | — | tests/unit/UT1.22_TestDataSeed/test_test_data_seed_api.py | — | — | — | COVERED-BOUND |
| CS-014 | mcp | — | tests/unit/UT1.22_TestDataSeed/test_test_data_seed_api.py | — | — | — | COVERED-BOUND |
| CS-015 | a2a | — | tests/unit/UT1.22_TestDataSeed/test_test_data_seed_api.py | — | — | — | COVERED-BOUND |
| CS-016 | webui | — | tests/unit/UT1.52_FlatLoginContract/test_flat_login_contract.py | — | — | — | COVERED-BOUND |
| FR-001 | api, webui | must | tests/unit/UT1.52_FlatLoginContract/test_flat_login_contract.py, tests/unit/UT1.52_FlatLoginContract/test_flat_login_contract.py, tests/unit/UT1.51_AuthedNonAdminGate/test_authed_non_admin_gate.py, tests/unit/UT1.51_AuthedNonAdminGate/test_authed_non_admin_gate.py, tests/unit/UT1.51_AuthedNonAdminGate/test_authed_non_admin_gate.py, tests/unit/UT1.51_AuthedNonAdminGate/test_authed_non_admin_gate.py, tests/unit/UT1.51_AuthedNonAdminGate/test_authed_non_admin_gate.py, tests/unit/UT1.51_AuthedNonAdminGate/test_authed_non_admin_gate.py, tests/unit/UT1.51_AuthedNonAdminGate/test_authed_non_admin_gate.py, tests/unit/UT1.51_AuthedNonAdminGate/test_authed_non_admin_gate.py, tests/unit/UT1.51_AuthedNonAdminGate/test_authed_non_admin_gate.py, tests/unit/UT1.50_UnauthAuthGate/test_unauth_auth_gate.py, tests/unit/UT1.50_UnauthAuthGate/test_unauth_auth_gate.py, tests/unit/UT1.50_UnauthAuthGate/test_unauth_auth_gate.py, tests/unit/UT1.50_UnauthAuthGate/test_unauth_auth_gate.py | — | — | — | COVERED-BOUND |
| FR-002 | api, a2a | must | tests/unit/UT1.2_AuthMiddleware/test_auth_middleware.py, tests/unit/UT1.2_AuthMiddleware/test_auth_middleware.py, tests/unit/UT1.2_AuthMiddleware/test_auth_middleware.py, tests/unit/UT1.2_AuthMiddleware/test_auth_middleware.py, tests/unit/UT1.2_AuthMiddleware/test_auth_middleware.py, tests/unit/UT1.2_AuthMiddleware/test_auth_middleware.py | — | — | — | COVERED-BOUND |
| FR-003 | api, mcp, webui | must | tests/unit/UT1.3_AccessControlService/test_access_control_service.py, tests/unit/UT1.3_AccessControlService/test_access_control_service.py, tests/unit/UT1.3_AccessControlService/test_access_control_service.py, tests/unit/UT1.3_AccessControlService/test_access_control_service.py, tests/unit/UT1.3_AccessControlService/test_access_control_service.py, tests/unit/UT1.3_AccessControlService/test_access_control_service.py, tests/unit/UT1.3_AccessControlService/test_access_control_service.py, tests/system/ST1.2_AccessControlApi/test_access_control_api.py, tests/integration/IT1.14_IdamCascadeNegative/test_dbmcp_idam_negative.py, tests/integration/IT1.1_AccessControlLifecycle/test_access_control_lifecycle.py | — | — | — | COVERED-BOUND |
| FR-004 | api, mcp, webui | must | tests/unit/UT1.21_ProfileScopeAndSchemaApproval/test_profile_scope_schema_approval.py, tests/unit/UT1.21_ProfileScopeAndSchemaApproval/test_profile_scope_schema_approval.py, tests/unit/UT1.21_ProfileScopeAndSchemaApproval/test_profile_scope_schema_approval.py, tests/integration/IT1.11_SourceConnections/test_source_connections_api.py | — | — | — | COVERED-BOUND |
| FR-005 | api, mcp | must | tests/unit/UT1.6_CatalogTools/test_catalog_tools.py, tests/unit/UT1.20_DiscoveryApi/test_discovery_api.py, tests/system/ST1.4_CatalogApi/test_catalog_api.py, tests/integration/IT1.15_McpJsonRpcEnvelope/test_mcp_jsonrpc_tools_call.py, tests/integration/IT1.3_FullDiscoveryFlow/test_full_discovery_flow.py | — | — | — | COVERED-BOUND |
| FR-006 | api, mcp | must | tests/unit/UT1.7_ContentTools/test_content_tools.py, tests/system/ST1.5_ContentApi/test_content_api.py, tests/system/ST1.5_ContentApi/test_content_api.py, tests/system/ST1.5_ContentApi/test_content_api.py, tests/integration/IT1.4_ContentCRUDLifecycle/test_content_crud_lifecycle.py | — | — | — | COVERED-BOUND |
| FR-007 | api, mcp | must | tests/unit/UT1.5_FilterModel/test_filter_model.py, tests/unit/UT1.5_FilterModel/test_filter_model.py, tests/unit/UT1.5_FilterModel/test_filter_model.py | — | — | — | COVERED-BOUND |
| FR-008 | api, mcp | should | tests/unit/UT1.8_RelationshipTools/test_relationship_tools.py, tests/integration/IT1.5_RelationshipLifecycle/test_relationship_lifecycle.py | — | — | — | COVERED-BOUND |
| FR-009 | api, mcp | must | tests/unit/UT1.12_SchemaChangeService/test_schema_change_service.py, tests/unit/UT1.12_SchemaChangeService/test_schema_change_service.py, tests/system/ST1.6_SchemaApi/test_schema_api.py, tests/integration/IT1.7_SchemaChangeLifecycle/test_schema_change_lifecycle.py | — | — | — | COVERED-BOUND |
| FR-010 | api, mcp | must | tests/unit/UT1.9_SearchIndexer/test_search_indexer.py, tests/unit/UT1.9_SearchIndexer/test_search_indexer.py, tests/unit/UT1.10_SearchService/test_search_service.py, tests/unit/UT1.10_SearchService/test_search_service.py, tests/system/ST1.7_SearchApi/test_search_api.py, tests/integration/IT1.6_SearchIndexingLifecycle/test_search_indexing_lifecycle.py | — | — | — | COVERED-BOUND |
| FR-011 | api, mcp | should | tests/integration/IT1.12_SavedQueries/test_saved_queries_api.py | — | — | — | COVERED-BOUND |
| FR-012 | api | should | tests/fixtures/test_seed_data.py, tests/fixtures/test_seed_data.py, tests/fixtures/test_seed_data.py | — | — | — | COVERED-BOUND |
| FR-013 | internal, mcp | must | tests/unit/UT1.4_MongoDBConnector/test_mongodb_connector.py, tests/unit/UT1.4_MongoDBConnector/test_mongodb_connector.py, tests/unit/UT1.4_MongoDBConnector/test_mongodb_connector.py, tests/unit/UT1.4_MongoDBConnector/test_mongodb_connector.py, tests/unit/UT1.4_MongoDBConnector/test_mongodb_connector.py, tests/unit/UT1.15_MongoConfig/test_mongo_config_resolution.py, tests/unit/UT1.15_MongoConfig/test_mongo_config_resolution.py, tests/unit/UT1.15_MongoConfig/test_mongo_config_resolution.py, tests/unit/UT1.15_MongoConfig/test_mongo_config_resolution.py, tests/system/ST1.3_MongoDBConnector/test_mongodb_connector_real.py, tests/integration/IT1.2_MongoDbMcpTools/test_mongodb_mcp_tools.py | — | — | — | COVERED-BOUND |
| FR-014 | internal, mcp | must | tests/unit/UT1.13_CouchDBConnector/test_couchdb_connector.py, tests/unit/UT1.13_CouchDBConnector/test_couchdb_connector.py, tests/system/ST1.9_CouchDBConnector/test_couchdb_connector_real.py, tests/integration/IT1.8_CouchDbMcpTools/test_couchdb_mcp_tools.py | — | — | — | COVERED-BOUND |
| FR-015 | internal, mcp | must | tests/unit/UT1.14_OpenSearchConnector/test_opensearch_connector.py, tests/unit/UT1.14_OpenSearchConnector/test_opensearch_connector.py, tests/system/ST1.10_OpenSearchConnector/test_opensearch_connector_real.py, tests/integration/IT1.9_OpenSearchMcpTools/test_opensearch_mcp_tools.py | — | — | — | COVERED-BOUND |
| FR-016 | internal | must | tests/unit/UT1.16_ElasticsearchConnector/test_elasticsearch_connector.py, tests/unit/UT1.16_ElasticsearchConnector/test_elasticsearch_connector.py, tests/system/ST1.12_ElasticsearchConnector/test_elasticsearch_connector_real.py | — | — | — | COVERED-BOUND |
| FR-017 | internal | must | tests/unit/UT1.17_CassandraConnector/test_cassandra_connector.py, tests/unit/UT1.17_CassandraConnector/test_cassandra_connector.py, tests/system/ST1.13_CassandraConnector/test_cassandra_connector_real.py | — | — | — | COVERED-BOUND |
| FR-018 | internal | must | tests/unit/UT1.18_RelationalConnectorDispatch/test_relational_connector_dispatch.py, tests/unit/UT1.18_RelationalConnectorDispatch/test_relational_connector_dispatch.py, tests/system/ST1.15_MariaDBConnector/test_mariadb_connector_real.py, tests/system/ST1.14_PostgreSQLConnector/test_postgresql_connector_real.py | — | — | — | COVERED-BOUND |
| FR-019 | internal, mcp | must | tests/integration/IT1.10_BackendConnectorMatrix/test_backend_connector_matrix.py | — | — | — | COVERED-BOUND |
| FR-020 | mcp | must | tests/unit/UT1.20_McpServer/test_mcp_server.py, tests/integration/IT1.15_McpJsonRpcEnvelope/test_mcp_jsonrpc_tools_call.py, tests/integration/IT1.15_McpJsonRpcEnvelope/test_mcp_jsonrpc_tools_call.py | — | — | — | COVERED-BOUND |
| FR-021 | a2a | must | tests/unit/UT1.15_A2AServer/test_a2a_server.py, tests/unit/UT1.15_A2AServer/test_a2a_server.py, tests/unit/UT1.15_A2AServer/test_a2a_server.py, tests/unit/UT1.15_A2AServer/test_a2a_server.py, tests/unit/UT1.15_A2AServer/test_a2a_server.py, tests/unit/UT1.15_A2AServer/test_a2a_server.py | — | — | — | COVERED-BOUND |
| FR-022 | webui | must | tests/unit/UT1.53_W28E1846WebUiAliases/test_webui_aliases.py, tests/unit/UT1.11_WebUiServing/test_web_ui_serving.py, tests/unit/UT1.11_WebUiServing/test_web_ui_serving.py, tests/unit/UT1.11_WebUiServing/test_web_ui_serving.py, tests/unit/UT1.11_WebUiServing/test_web_ui_serving.py, tests/unit/UT1.11_WebUiServing/test_web_ui_serving.py, tests/unit/UT1.11_WebUiServing/test_web_ui_serving.py, tests/unit/UT1.11_WebUiServing/test_web_ui_serving.py, tests/unit/UT1.11_WebUiServing/test_web_ui_serving.py, tests/application/AT_WEBUI_E2E/test_webui_e2e.py, tests/application/AT_WEBUI_E2E/test_webui_e2e.py, tests/application/AT_WEBUI_E2E/test_webui_e2e.py, tests/application/AT_WEBUI_E2E/test_webui_e2e.py, tests/application/AT_WEBUI_E2E/test_webui_e2e.py, tests/application/AT_WEBUI_E2E/test_webui_e2e.py, tests/application/AT_WEBUI_E2E/test_webui_e2e.py, tests/application/AT_WEBUI_E2E/test_webui_e2e.py, tests/application/AT_WEBUI_E2E/test_webui_e2e.py, tests/application/AT_WEBUI_E2E/test_webui_e2e.py, tests/application/AT_WEBUI_E2E/test_webui_e2e.py, tests/application/AT_WEBUI_E2E/test_webui_e2e.py, tests/application/AT_WEBUI_E2E/test_webui_e2e.py, tests/application/AT_WEBUI_E2E/test_webui_e2e.py, tests/application/AT_WEBUI_E2E/test_webui_e2e.py, tests/application/AT_WEBUI_E2E/test_webui_e2e.py, tests/application/AT_WEBUI_E2E/test_webui_e2e.py, tests/application/AT_WEBUI_E2E/test_webui_e2e.py, tests/system/ST1.8_WebUiServing/test_web_ui_system_serving.py | — | — | — | COVERED-BOUND |
| FR-023 | internal, api | must | tests/unit/UT1.1_ConfigLoading/test_config_loading.py, tests/unit/UT1.1_ConfigLoading/test_config_loading.py | — | — | — | COVERED-BOUND |
| FR-024 | api, mcp | should | tests/unit/UT1.19_JobLifecycle/test_job_lifecycle.py, tests/unit/UT1.19_JobLifecycle/test_job_lifecycle.py, tests/unit/UT1.19_JobLifecycle/test_job_lifecycle.py, tests/unit/UT1.19_JobLifecycle/test_job_lifecycle.py, tests/unit/UT1.23_JobsApi/test_jobs_api.py, tests/unit/UT1.23_JobsApi/test_jobs_api.py | — | — | — | COVERED-BOUND |
| FR-025 | api | must | tests/system/ST1.1_ServerStartup/test_server_startup.py | — | — | — | COVERED-BOUND |
| FR-026 | internal | should | tests/quality/QT1.1_ProjectStructure/test_project_structure.py, tests/quality/QT1.1_ProjectStructure/test_project_structure.py, tests/quality/QT1.1_ProjectStructure/test_project_structure.py, tests/quality/QT1.1_ProjectStructure/test_project_structure.py, tests/quality/QT1.1_ProjectStructure/test_project_structure.py | — | — | — | COVERED-BOUND |
| FR-027 | api, a2a | must | tests/e2e/test_w28a746_live_preprod_contract.py, tests/e2e/test_w28a746_live_preprod_contract.py, tests/smoke/test_w28a746_b_method_idam.py, tests/smoke/test_w28a746_b_method_idam.py | — | — | — | COVERED-BOUND |
| FR-028 | api, mcp | must | tests/unit/UT1.30_ApiA2aAuditAU3/test_au3_emitters.py, tests/unit/UT1.30_ApiA2aAuditAU3/test_au3_emitters.py, tests/unit/UT1.30_ApiA2aAuditAU3/test_au3_emitters.py, tests/unit/UT1.30_ApiA2aAuditAU3/test_au3_emitters.py, tests/unit/UT1.30_ApiA2aAuditAU3/test_au3_emitters.py, tests/unit/UT1.30_ApiA2aAuditAU3/test_au3_emitters.py, tests/system/ST1.2_AccessControlApi/test_access_control_api.py, tests/integration/IT1.14_ApiA2aAuditAU3/test_api_a2a_audit_au3.py, tests/integration/IT1.14_ApiA2aAuditAU3/test_api_a2a_audit_au3.py, tests/integration/IT1.14_ApiA2aAuditAU3/test_api_a2a_audit_au3.py, tests/integration/IT1.13_McpAuditAU3/test_mcp_audit_au3.py | — | — | — | COVERED-BOUND |
