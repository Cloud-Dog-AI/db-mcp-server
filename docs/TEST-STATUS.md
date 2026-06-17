---
template-id: T-TSS
template-version: 1.0
project: db-mcp-server
doc-last-updated: 2026-06-17T12:28:14.133567+00:00
doc-git-commit: 9c5b12de8af6c1142c4401994aa3148adf2d1a6e
doc-git-branch: W28C-1714-100pct-fix
doc-age-policy: 30d
doc-conformance-stamp: 2026-06-17T12:28:14.133567+00:00
---

# db-mcp-server — TEST-STATUS

> **Template version:** T-TSS v1.0 — overwritten by `scripts/update-test-state.py`. Do not hand-edit.

## 1. Latest run

- **Run timestamp:** 2026-06-17T12:28:14.133567+00:00
- **Commit:** `9c5b12de8af6c1142c4401994aa3148adf2d1a6e` (`W28C-1714-100pct-fix`)
- **Totals:** 107 tests | 107 passed | 0 failed | 0 skipped

## 2. Per-test status

| Test ID | Tier | Status | Last run | Commit | Known issue |
|---|---|---|---|---|---|
| `tests.fixtures.test_seed_data::test_cross_collection_references_resolve` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.fixtures.test_seed_data::test_field_types_and_nullability_are_preserved` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.fixtures.test_seed_data::test_seed_counts_match_canonical_dataset` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.integration.IT1.10_BackendConnectorMatrix.test_backend_connector_matrix::test_real_backend_connector_operations[mongodb]` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.integration.IT1.12_SavedQueries.test_saved_queries_api::test_saved_queries_crud_conflict_and_delete` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.quality.QT1.1_ProjectStructure.test_project_structure::test_active_source_uses_platform_logging_only` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.quality.QT1.1_ProjectStructure.test_project_structure::test_required_platform_package_declarations_are_present` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.quality.QT1.1_ProjectStructure.test_project_structure::test_required_runtime_files_exist` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.quality.QT1.1_ProjectStructure.test_project_structure::test_w28a_118c_docs_map_packages_to_ui_and_tests` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.smoke.test_w28a746_b_method_idam::test_t1_flat_roles_and_secret_masking` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.smoke.test_w28a746_b_method_idam::test_t2_role_rbac_and_t3_group_membership_cascade` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.system.ST1.1_ServerStartup.test_server_startup::test_all_servers_start_and_report_health` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.system.ST1.2_AccessControlApi.test_access_control_api::test_access_control_api_crud_and_audit` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.10_SearchService.test_search_service::test_v1_10_1_repository_search_and_explain_match` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.10_SearchService.test_search_service::test_v1_10_2_index_status_includes_queue_and_entity_status` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.11_WebUiServing.test_web_ui_serving::test_cookie_authenticated_browser_proxies_inject_role_key` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.11_WebUiServing.test_web_ui_serving::test_dist_assets_are_served_from_ui_dist` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.11_WebUiServing.test_web_ui_serving::test_history_routes_resolve_to_index_html` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.11_WebUiServing.test_web_ui_serving::test_runtime_config_is_served_for_spa_bootstrap` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.11_WebUiServing.test_web_ui_serving::test_web_surface_raises_request_timeout_budget` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.12_SchemaChangeService.test_schema_change_service::test_schema_change_service_applies_plan_and_refreshes_index` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.12_SchemaChangeService.test_schema_change_service::test_schema_change_service_requires_approval_and_tracks_history` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.13_CouchDBConnector.test_couchdb_connector::test_adapter_capabilities_and_catalogue_calls` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.13_CouchDBConnector.test_couchdb_connector::test_adapter_data_and_schema_operations` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.14_OpenSearchConnector.test_opensearch_connector::test_adapter_capabilities_and_catalogue_calls` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.14_OpenSearchConnector.test_opensearch_connector::test_adapter_data_and_schema_operations` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.15_A2AServer.test_a2a_server::test_a2a_read_only_key_is_forbidden_on_write_task` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.15_A2AServer.test_a2a_server::test_a2a_root_reports_websocket_path` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.15_A2AServer.test_a2a_server::test_a2a_task_rejects_missing_api_key` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.15_A2AServer.test_a2a_server::test_a2a_websocket_accepts_valid_api_key_and_replies_to_health` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.15_A2AServer.test_a2a_server::test_a2a_websocket_proxy_alias_accepts_valid_api_key` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.15_A2AServer.test_a2a_server::test_a2a_websocket_rejects_missing_api_key` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.15_MongoConfig.test_mongo_config_resolution::test_resolve_mongodb_uri_builds_uri_from_structured_defaults` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.15_MongoConfig.test_mongo_config_resolution::test_resolve_mongodb_uri_prefers_profile_uri` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.15_MongoConfig.test_mongo_config_resolution::test_resolve_mongodb_uri_rejects_missing_settings` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.15_MongoConfig.test_mongo_config_resolution::test_resolve_mongodb_uri_uses_configured_default_uri` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.16_ElasticsearchConnector.test_elasticsearch_connector::test_adapter_capabilities_and_catalogue_calls` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.16_ElasticsearchConnector.test_elasticsearch_connector::test_adapter_data_and_schema_operations` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.17_CassandraConnector.test_cassandra_connector::test_adapter_capabilities_and_catalogue_calls` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.17_CassandraConnector.test_cassandra_connector::test_adapter_data_and_schema_operations` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.18_RelationalConnectorDispatch.test_relational_connector_dispatch::test_connector_manager_supports_mariadb_source_type` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.18_RelationalConnectorDispatch.test_relational_connector_dispatch::test_connector_manager_supports_postgresql_source_type` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.19_JobLifecycle.test_job_lifecycle::test_lifecycle_queue_cancel` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.19_JobLifecycle.test_job_lifecycle::test_lifecycle_queue_run_fail_retry` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.19_JobLifecycle.test_job_lifecycle::test_lifecycle_queue_run_succeed` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.19_JobLifecycle.test_job_lifecycle::test_lifecycle_queue_run_timeout` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.1_ConfigLoading.test_config_loading::test_load_runtime_config_reads_ports_and_auth_key` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.1_ConfigLoading.test_config_loading::test_runtime_config_js_exposes_web_settings` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.20_DiscoveryApi.test_discovery_api::test_discovery_routes_cache_profile_results_and_discover_connection_namespaces` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.20_McpServer.test_mcp_server::test_mcp_surface_raises_request_timeout_budget` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.21_ProfileScopeAndSchemaApproval.test_profile_scope_schema_approval::test_connector_manager_resolves_named_source_connection` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.21_ProfileScopeAndSchemaApproval.test_profile_scope_schema_approval::test_profile_scope_route_dry_runs_filtered_profile_without_persisting` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.21_ProfileScopeAndSchemaApproval.test_profile_scope_schema_approval::test_schema_change_approve_route_marks_plan_approved` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.22_TestDataSeed.test_test_data_seed_api::test_test_data_seed_is_forbidden_outside_allowed_runtime_profiles` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.22_TestDataSeed.test_test_data_seed_api::test_test_data_seed_rejects_unknown_connection` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.22_TestDataSeed.test_test_data_seed_api::test_test_data_seed_rejects_unknown_dataset` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.22_TestDataSeed.test_test_data_seed_api::test_test_data_seed_runs_sqlite_fixture_when_runtime_profile_is_allowed` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.2_AuthMiddleware.test_auth_middleware::test_api_base_path_override_exposes_prefixed_health_and_ping` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.2_AuthMiddleware.test_auth_middleware::test_auth_me_returns_api_key_principal` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.2_AuthMiddleware.test_auth_middleware::test_health_route_is_public` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.2_AuthMiddleware.test_auth_middleware::test_protected_route_accepts_valid_api_key` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.2_AuthMiddleware.test_auth_middleware::test_protected_route_rejects_missing_api_key` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.2_AuthMiddleware.test_auth_middleware::test_read_only_key_is_forbidden_on_api_write` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.3_AccessControlService.test_access_control_service::test_flat_demo_keys_resolve_to_three_flat_roles` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.3_AccessControlService.test_access_control_service::test_group_role_assignments_contribute_to_effective_permissions` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.3_AccessControlService.test_access_control_service::test_internal_profile_lookup_preserves_connection_secret` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.3_AccessControlService.test_access_control_service::test_profile_masking_enforces_exclusions_and_masks` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.3_AccessControlService.test_access_control_service::test_verify_api_key_applies_role_permissions_and_key_scopes` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.4_MongoDBConnector.test_mongodb_connector::test_adapter_caches_namespace_listing_per_uri` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.4_MongoDBConnector.test_mongodb_connector::test_adapter_capabilities_and_catalogue_calls` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.4_MongoDBConnector.test_mongodb_connector::test_adapter_data_and_schema_operations` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.4_MongoDBConnector.test_mongodb_connector::test_adapter_normalises_binary_fields_and_preserves_binary_schema_type` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.4_MongoDBConnector.test_mongodb_connector::test_adapter_plans_and_applies_entity_lifecycle` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.50_UnauthAuthGate.test_unauth_auth_gate::test_anon_proxy_request_is_keyless` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.50_UnauthAuthGate.test_unauth_auth_gate::test_auth_me_resolves_managed_api_key` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.50_UnauthAuthGate.test_unauth_auth_gate::test_forged_session_cookie_does_not_bypass` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.50_UnauthAuthGate.test_unauth_auth_gate::test_unauth_principal_denied` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.51_AuthedNonAdminGate.test_authed_non_admin_gate::test_mask_connection_secret_forms` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.51_AuthedNonAdminGate.test_authed_non_admin_gate::test_nonadmin_key_cannot_escalate_via_webui_header` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.51_AuthedNonAdminGate.test_authed_non_admin_gate::test_principal_for_admin_has_wildcard` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.51_AuthedNonAdminGate.test_authed_non_admin_gate::test_principal_for_nonadmin_is_denied_profile_manage` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.51_AuthedNonAdminGate.test_authed_non_admin_gate::test_principal_for_unknown_user_is_none` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.51_AuthedNonAdminGate.test_authed_non_admin_gate::test_profile_view_masks_connection_password` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.51_AuthedNonAdminGate.test_authed_non_admin_gate::test_service_key_only_is_admin_unchanged` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.51_AuthedNonAdminGate.test_authed_non_admin_gate::test_webui_forwarded_nonadmin_is_reresolved_not_admin` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.51_AuthedNonAdminGate.test_authed_non_admin_gate::test_webui_forwarded_unknown_user_denied` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.52_FlatLoginContract.test_flat_login_contract::test_anon_write_is_unauthorized` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.52_FlatLoginContract.test_flat_login_contract::test_bad_password_is_unauthorized` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.52_FlatLoginContract.test_flat_login_contract::test_mcp_proxy_forwards_session_role_key[creds0-admin]` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.52_FlatLoginContract.test_flat_login_contract::test_mcp_proxy_forwards_session_role_key[creds1-read-write]` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.52_FlatLoginContract.test_flat_login_contract::test_mcp_proxy_forwards_session_role_key[creds2-read-only]` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.52_FlatLoginContract.test_flat_login_contract::test_missing_credentials_is_bad_request` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.52_FlatLoginContract.test_flat_login_contract::test_read_only_can_read` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.52_FlatLoginContract.test_flat_login_contract::test_read_only_write_is_forbidden` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.52_FlatLoginContract.test_flat_login_contract::test_read_write_can_write_and_forwards_role_principal` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.52_FlatLoginContract.test_flat_login_contract::test_runtime_config_advertises_cookie_not_api_key` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.52_FlatLoginContract.test_flat_login_contract::test_three_flat_roles_login_by_username_password[creds0-admin]` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.52_FlatLoginContract.test_flat_login_contract::test_three_flat_roles_login_by_username_password[creds1-read-write]` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.52_FlatLoginContract.test_flat_login_contract::test_three_flat_roles_login_by_username_password[creds2-read-only]` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.5_FilterModel.test_filter_model::test_filter_parser_rejects_invalid_input` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.5_FilterModel.test_filter_model::test_parse_filter_accepts_legacy_mapping_and_nested_groups` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.5_FilterModel.test_filter_model::test_translate_filter_to_mongodb_query` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.6_CatalogTools.test_catalog_tools::test_catalog_tools_list_and_search` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.7_ContentTools.test_content_tools::test_content_tools_translate_filters_and_mask_results` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.8_RelationshipTools.test_relationship_tools::test_relationship_tools_cover_crud_and_inference` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.9_SearchIndexer.test_search_indexer::test_v1_9_1_query_normalisation_and_fts_building` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |
| `tests.unit.UT1.9_SearchIndexer.test_search_indexer::test_v1_9_2_sync_profile_builds_metadata_relationship_and_content_documents` | UT/ST/IT | pass | 2026-06-17 | `9c5b12de` | |

## 3. Failures (detail)

_None._
