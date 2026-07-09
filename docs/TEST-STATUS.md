---
template-id: T-TSS
template-version: 1.0
project: db-mcp-server
doc-last-updated: 2026-07-09T06:46:32+00:00
doc-git-commit: 5b7b58c8a0c55018cd0527e0bfb0b5709af7de79
doc-git-branch: main
doc-age-policy: 30d
doc-conformance-stamp: 2026-07-09T06:46:32+00:00
---

# db-mcp-server — TEST-STATUS

> **Template version:** T-TSS v1.0. Per-node evidence generated from real pytest JUnit XML on CPython 3.12.13
> (W28E-1863 WS-A-EVIDENCE re-verify — replaces prior hand-set/fabricated rows). Node-ids are slash-form
> `tests/<path>.py::[Class::]<test>` so the on-origin/main `generate-req-coverage.py` REQ→test join resolves.

## 1. Latest run

- **Run timestamp:** 2026-07-09T06:46:32+00:00
- **Commit:** `5b7b58c8a0c55018cd0527e0bfb0b5709af7de79` (`main` working tree)
- **Totals:** 144 tests | 144 passed | 0 failed | 0 skipped
- **Evidence basis:** 2026-07-08 W28E-1863 WS-A-EVIDENCE per-node JUnit plus focused
  W28E-1863 db-mcp tail reverify JUnit in `working/W28E-1863/db-mcp-tail/`.

## 2. Per-test status

| Test ID | Tier | Status | Last run | Commit | Known issue |
|---|---|---|---|---|---|
| `tests/application/AT_WEBUI_E2E/test_webui_e2e.py::test_t10_settings` | UT/IT/ST/AT/QT | pass | 2026-07-09 | `5b7b58c` | focused reverify: `working/W28E-1863/db-mcp-tail/at_webui_tail.xml` |
| `tests/application/AT_WEBUI_E2E/test_webui_e2e.py::test_t11_audit_log` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/application/AT_WEBUI_E2E/test_webui_e2e.py::test_t12_system_health` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/application/AT_WEBUI_E2E/test_webui_e2e.py::test_t13_catalogue_browse` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/application/AT_WEBUI_E2E/test_webui_e2e.py::test_t14_search` | UT/IT/ST/AT/QT | pass | 2026-07-09 | `5b7b58c` | focused reverify: `working/W28E-1863/db-mcp-tail/at_webui_tail.xml` |
| `tests/application/AT_WEBUI_E2E/test_webui_e2e.py::test_t15_relationships` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/application/AT_WEBUI_E2E/test_webui_e2e.py::test_t16_entity_detail` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/application/AT_WEBUI_E2E/test_webui_e2e.py::test_t17_console_gate_and_cw_testids` | UT/IT/ST/AT/QT | pass | 2026-07-09 | `5b7b58c` | focused reverify: `working/W28E-1863/db-mcp-tail/at_webui_tail.xml` |
| `tests/application/AT_WEBUI_E2E/test_webui_e2e.py::test_t1_login_page_renders` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/application/AT_WEBUI_E2E/test_webui_e2e.py::test_t1_login_with_credentials` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/application/AT_WEBUI_E2E/test_webui_e2e.py::test_t2_dashboard_widgets` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/application/AT_WEBUI_E2E/test_webui_e2e.py::test_t3_profile_crud` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/application/AT_WEBUI_E2E/test_webui_e2e.py::test_t4_data_browser` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/application/AT_WEBUI_E2E/test_webui_e2e.py::test_t5_schema_browser` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/application/AT_WEBUI_E2E/test_webui_e2e.py::test_t6_user_crud` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/application/AT_WEBUI_E2E/test_webui_e2e.py::test_t7_group_crud` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/application/AT_WEBUI_E2E/test_webui_e2e.py::test_t8_api_key_crud` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/application/AT_WEBUI_E2E/test_webui_e2e.py::test_t9_rbac_unauthenticated` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/quality/QT1.1_ProjectStructure/test_project_structure.py::test_active_source_uses_platform_logging_only` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/quality/QT1.1_ProjectStructure/test_project_structure.py::test_required_platform_package_declarations_are_present` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/quality/QT1.1_ProjectStructure/test_project_structure.py::test_required_runtime_files_exist` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/quality/QT1.1_ProjectStructure/test_project_structure.py::test_w28a_118c_docs_map_packages_to_ui_and_tests` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/smoke/test_w28a746_b_method_idam.py::test_t1_flat_roles_and_secret_masking` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/smoke/test_w28a746_b_method_idam.py::test_t2_role_rbac_and_t3_group_membership_cascade` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/system/ST1.10_OpenSearchConnector/test_opensearch_connector_real.py::test_opensearch_adapter_against_real_local_runtime` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/system/ST1.12_ElasticsearchConnector/test_elasticsearch_connector_real.py::test_elasticsearch_adapter_against_real_runtime` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/system/ST1.13_CassandraConnector/test_cassandra_connector_real.py::test_cassandra_adapter_against_real_runtime` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/system/ST1.14_PostgreSQLConnector/test_postgresql_connector_real.py::test_postgresql_connector_against_real_runtime` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/system/ST1.15_MariaDBConnector/test_mariadb_connector_real.py::test_mariadb_connector_against_real_runtime` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/system/ST1.1_ServerStartup/test_server_startup.py::test_all_servers_start_and_report_health` | UT/IT/ST/AT/QT | pass | 2026-07-09 | `5b7b58c` | focused reverify: `working/W28E-1863/db-mcp-tail/st1_1_server_startup.xml` |
| `tests/system/ST1.2_AccessControlApi/test_access_control_api.py::test_access_control_api_crud_and_audit` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/system/ST1.3_MongoDBConnector/test_mongodb_connector_real.py::test_mongodb_adapter_against_real_local_mongo` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/system/ST1.4_CatalogApi/test_catalog_api.py::test_catalogue_tools_against_real_mongodb` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/system/ST1.5_ContentApi/test_content_api.py::test_content_tools_apply_structured_filters_and_masks` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/system/ST1.5_ContentApi/test_content_api.py::test_content_tools_round_trip_binary_fields` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/system/ST1.5_ContentApi/test_content_api.py::test_content_tools_support_all_documented_filter_operators` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/system/ST1.6_SchemaApi/test_schema_api.py::test_schema_tools_plan_apply_history_and_refresh` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/system/ST1.7_SearchApi/test_search_api.py::test_v1_7_search_metadata_finds_customer_email_field` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/system/ST1.8_WebUiServing/test_web_ui_system_serving.py::test_web_server_serves_spa_runtime_config_and_api_proxy` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/system/ST1.9_CouchDBConnector/test_couchdb_connector_real.py::test_couchdb_adapter_against_real_local_couchdb` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.10_SearchService/test_search_service.py::test_v1_10_1_repository_search_and_explain_match` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.10_SearchService/test_search_service.py::test_v1_10_2_index_status_includes_queue_and_entity_status` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.11_WebUiServing/test_web_ui_serving.py::test_cookie_authenticated_browser_proxies_inject_role_key` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.11_WebUiServing/test_web_ui_serving.py::test_dist_assets_are_served_from_ui_dist` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.11_WebUiServing/test_web_ui_serving.py::test_history_routes_resolve_to_index_html` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.11_WebUiServing/test_web_ui_serving.py::test_idam_webui_compatibility_reads_are_session_protected` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.11_WebUiServing/test_web_ui_serving.py::test_legacy_webui_routes_redirect_to_canonical_urls` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.11_WebUiServing/test_web_ui_serving.py::test_runtime_config_is_served_for_spa_bootstrap` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.11_WebUiServing/test_web_ui_serving.py::test_unknown_extensionless_webui_route_is_not_spa_entry` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.11_WebUiServing/test_web_ui_serving.py::test_web_surface_raises_request_timeout_budget` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.12_SchemaChangeService/test_schema_change_service.py::test_schema_change_service_applies_plan_and_refreshes_index` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.12_SchemaChangeService/test_schema_change_service.py::test_schema_change_service_requires_approval_and_tracks_history` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.13_CouchDBConnector/test_couchdb_connector.py::test_adapter_capabilities_and_catalogue_calls` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.13_CouchDBConnector/test_couchdb_connector.py::test_adapter_data_and_schema_operations` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.14_OpenSearchConnector/test_opensearch_connector.py::test_adapter_capabilities_and_catalogue_calls` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.14_OpenSearchConnector/test_opensearch_connector.py::test_adapter_data_and_schema_operations` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.15_A2AServer/test_a2a_server.py::test_a2a_read_only_key_is_forbidden_on_write_task` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.15_A2AServer/test_a2a_server.py::test_a2a_root_reports_websocket_path` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.15_A2AServer/test_a2a_server.py::test_a2a_task_rejects_missing_api_key` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.15_A2AServer/test_a2a_server.py::test_a2a_websocket_accepts_valid_api_key_and_replies_to_health` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.15_A2AServer/test_a2a_server.py::test_a2a_websocket_proxy_alias_accepts_valid_api_key` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.15_A2AServer/test_a2a_server.py::test_a2a_websocket_rejects_missing_api_key` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.15_MongoConfig/test_mongo_config_resolution.py::test_resolve_mongodb_uri_builds_uri_from_structured_defaults` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.15_MongoConfig/test_mongo_config_resolution.py::test_resolve_mongodb_uri_prefers_profile_uri` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.15_MongoConfig/test_mongo_config_resolution.py::test_resolve_mongodb_uri_rejects_missing_settings` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.15_MongoConfig/test_mongo_config_resolution.py::test_resolve_mongodb_uri_uses_configured_default_uri` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.16_ElasticsearchConnector/test_elasticsearch_connector.py::test_adapter_capabilities_and_catalogue_calls` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.16_ElasticsearchConnector/test_elasticsearch_connector.py::test_adapter_data_and_schema_operations` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.17_CassandraConnector/test_cassandra_connector.py::test_adapter_capabilities_and_catalogue_calls` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.17_CassandraConnector/test_cassandra_connector.py::test_adapter_data_and_schema_operations` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.18_RelationalConnectorDispatch/test_relational_connector_dispatch.py::test_connector_manager_supports_mariadb_source_type` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.18_RelationalConnectorDispatch/test_relational_connector_dispatch.py::test_connector_manager_supports_postgresql_source_type` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.19_JobLifecycle/test_job_lifecycle.py::test_lifecycle_queue_cancel` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.19_JobLifecycle/test_job_lifecycle.py::test_lifecycle_queue_run_fail_retry` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.19_JobLifecycle/test_job_lifecycle.py::test_lifecycle_queue_run_succeed` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.19_JobLifecycle/test_job_lifecycle.py::test_lifecycle_queue_run_timeout` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.1_ConfigLoading/test_config_loading.py::test_load_runtime_config_reads_ports_and_auth_key` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.1_ConfigLoading/test_config_loading.py::test_runtime_config_js_exposes_web_settings` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.20_DiscoveryApi/test_discovery_api.py::test_discovery_routes_cache_profile_results_and_discover_connection_namespaces` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.20_McpServer/test_mcp_server.py::test_mcp_surface_raises_request_timeout_budget` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.21_ProfileScopeAndSchemaApproval/test_profile_scope_schema_approval.py::test_connector_manager_resolves_named_source_connection` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.21_ProfileScopeAndSchemaApproval/test_profile_scope_schema_approval.py::test_profile_scope_route_dry_runs_filtered_profile_without_persisting` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.21_ProfileScopeAndSchemaApproval/test_profile_scope_schema_approval.py::test_schema_change_approve_route_marks_plan_approved` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.22_TestDataSeed/test_test_data_seed_api.py::test_test_data_seed_is_forbidden_outside_allowed_runtime_profiles` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.22_TestDataSeed/test_test_data_seed_api.py::test_test_data_seed_rejects_unknown_connection` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.22_TestDataSeed/test_test_data_seed_api.py::test_test_data_seed_rejects_unknown_dataset` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.22_TestDataSeed/test_test_data_seed_api.py::test_test_data_seed_runs_sqlite_fixture_when_runtime_profile_is_allowed` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.23_JobsApi/test_jobs_api.py::test_jobs_api_non_admin_is_limited_to_own_jobs` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.23_JobsApi/test_jobs_api.py::test_jobs_api_retries_and_deletes_job_records` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.2_AuthMiddleware/test_auth_middleware.py::test_api_base_path_override_exposes_prefixed_health_and_ping` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.2_AuthMiddleware/test_auth_middleware.py::test_auth_me_returns_api_key_principal` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.2_AuthMiddleware/test_auth_middleware.py::test_health_route_is_public` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.2_AuthMiddleware/test_auth_middleware.py::test_protected_route_accepts_valid_api_key` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.2_AuthMiddleware/test_auth_middleware.py::test_protected_route_rejects_missing_api_key` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.2_AuthMiddleware/test_auth_middleware.py::test_read_only_key_is_forbidden_on_api_write` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.3_AccessControlService/test_access_control_service.py::test_flat_demo_keys_resolve_to_three_flat_roles` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.3_AccessControlService/test_access_control_service.py::test_group_role_assignments_contribute_to_effective_permissions` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.3_AccessControlService/test_access_control_service.py::test_internal_profile_lookup_preserves_connection_secret` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.3_AccessControlService/test_access_control_service.py::test_profile_masking_enforces_exclusions_and_masks` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.3_AccessControlService/test_access_control_service.py::test_profile_update_preserves_masked_connection_secret` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.3_AccessControlService/test_access_control_service.py::test_rotate_api_key_revokes_old_key_and_preserves_scope` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.3_AccessControlService/test_access_control_service.py::test_verify_api_key_applies_role_permissions_and_key_scopes` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.4_MongoDBConnector/test_mongodb_connector.py::test_adapter_caches_namespace_listing_per_uri` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.4_MongoDBConnector/test_mongodb_connector.py::test_adapter_capabilities_and_catalogue_calls` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.4_MongoDBConnector/test_mongodb_connector.py::test_adapter_data_and_schema_operations` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.4_MongoDBConnector/test_mongodb_connector.py::test_adapter_normalises_binary_fields_and_preserves_binary_schema_type` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.4_MongoDBConnector/test_mongodb_connector.py::test_adapter_plans_and_applies_entity_lifecycle` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.50_UnauthAuthGate/test_unauth_auth_gate.py::test_anon_proxy_request_is_keyless` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.50_UnauthAuthGate/test_unauth_auth_gate.py::test_auth_me_resolves_managed_api_key` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.50_UnauthAuthGate/test_unauth_auth_gate.py::test_forged_session_cookie_does_not_bypass` | UT/IT/ST/AT/QT | pass | 2026-07-09 | `5b7b58c` | focused reverify: `working/W28E-1863/db-mcp-tail/ut1_50_unauth_auth_gate.xml` |
| `tests/unit/UT1.50_UnauthAuthGate/test_unauth_auth_gate.py::test_unauth_principal_denied` | UT/IT/ST/AT/QT | pass | 2026-07-09 | `5b7b58c` | focused reverify: `working/W28E-1863/db-mcp-tail/ut1_50_unauth_auth_gate.xml` |
| `tests/unit/UT1.51_AuthedNonAdminGate/test_authed_non_admin_gate.py::test_mask_connection_secret_forms` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.51_AuthedNonAdminGate/test_authed_non_admin_gate.py::test_nonadmin_key_cannot_escalate_via_webui_header` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.51_AuthedNonAdminGate/test_authed_non_admin_gate.py::test_principal_for_admin_has_wildcard` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.51_AuthedNonAdminGate/test_authed_non_admin_gate.py::test_principal_for_nonadmin_is_denied_profile_manage` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.51_AuthedNonAdminGate/test_authed_non_admin_gate.py::test_principal_for_unknown_user_is_none` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.51_AuthedNonAdminGate/test_authed_non_admin_gate.py::test_profile_view_masks_connection_password` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.51_AuthedNonAdminGate/test_authed_non_admin_gate.py::test_service_key_only_is_admin_unchanged` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.51_AuthedNonAdminGate/test_authed_non_admin_gate.py::test_webui_forwarded_nonadmin_is_reresolved_not_admin` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.51_AuthedNonAdminGate/test_authed_non_admin_gate.py::test_webui_forwarded_unknown_user_denied` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.52_FlatLoginContract/test_flat_login_contract.py::test_admin_user_proxy_auth_precedes_malformed_json` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.52_FlatLoginContract/test_flat_login_contract.py::test_anon_write_is_unauthorized` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.52_FlatLoginContract/test_flat_login_contract.py::test_bad_password_is_unauthorized` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.52_FlatLoginContract/test_flat_login_contract.py::test_mcp_proxy_forwards_session_role_key[creds0-admin]` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.52_FlatLoginContract/test_flat_login_contract.py::test_mcp_proxy_forwards_session_role_key[creds1-read-write]` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.52_FlatLoginContract/test_flat_login_contract.py::test_mcp_proxy_forwards_session_role_key[creds2-read-only]` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.52_FlatLoginContract/test_flat_login_contract.py::test_missing_credentials_is_bad_request` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.52_FlatLoginContract/test_flat_login_contract.py::test_read_only_can_read` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.52_FlatLoginContract/test_flat_login_contract.py::test_read_only_write_is_forbidden` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.52_FlatLoginContract/test_flat_login_contract.py::test_read_write_can_write_and_forwards_role_principal` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.52_FlatLoginContract/test_flat_login_contract.py::test_runtime_config_advertises_cookie_not_api_key` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.52_FlatLoginContract/test_flat_login_contract.py::test_three_flat_roles_login_by_username_password[creds0-admin]` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.52_FlatLoginContract/test_flat_login_contract.py::test_three_flat_roles_login_by_username_password[creds1-read-write]` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.52_FlatLoginContract/test_flat_login_contract.py::test_three_flat_roles_login_by_username_password[creds2-read-only]` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.53_W28E1846WebUiAliases/test_webui_aliases.py::test_profile_connection_aliases_redirect_to_canonical_admin_routes` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.54_W28E1863Wsc014BuildIdentity/test_build_identity.py::test_version_route_emits_build_identity_not_spa_shadowed` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.5_FilterModel/test_filter_model.py::test_filter_parser_rejects_invalid_input` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.5_FilterModel/test_filter_model.py::test_parse_filter_accepts_legacy_mapping_and_nested_groups` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.5_FilterModel/test_filter_model.py::test_translate_filter_to_mongodb_query` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.6_CatalogTools/test_catalog_tools.py::test_catalog_tools_list_and_search` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.7_ContentTools/test_content_tools.py::test_content_tools_translate_filters_and_mask_results` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.8_RelationshipTools/test_relationship_tools.py::test_relationship_tools_cover_crud_and_inference` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.9_SearchIndexer/test_search_indexer.py::test_v1_9_1_query_normalisation_and_fts_building` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |
| `tests/unit/UT1.9_SearchIndexer/test_search_indexer.py::test_v1_9_2_sync_profile_builds_metadata_relationship_and_content_documents` | UT/IT/ST/AT/QT | pass | 2026-07-08 | `973991f8` |  |

## 3. Failures (detail)

- No current failures in the 144-test status set. The six W28E-1863 db-mcp second-pass
  origin/main fail rows were reverified with focused JUnit evidence under
  `working/W28E-1863/db-mcp-tail/`.

## 4. Blocked / not-run tiers (honest gaps)

- **tests/integration** — BLOCKED (wall-clock timeout). The IT tier connects to the real
  remote MongoDB backend (`mongo0.app.vpc0.cloud-dog.net:27017`) configured in `tests/env-IT`.
  Each connector round-trip over the VPC link takes ~25-60s, so the tier (and even a reduced
  subset with `--ignore` of the mongodb matrix/tools/schema suites) exceeds the 600s foreground
  budget before emitting a JUnit summary. Partial observed on 2026-07-08 CPython 3.12.13:
  ~19 passed / 3 failed before the cutoff (indicative only — not recorded as per-node evidence).
  Consequence: REQs whose ONLY binding is an integration test remain COVERED-BOUND (no run status):
  FR-011 (also bound elsewhere), FR-012, FR-019. Re-run against a local/low-latency Mongo to close.
