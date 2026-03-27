# db-mcp-server — Architecture

## W28A-421 Review Status
- Reviewed for external/shareable publication during W28A-421.
- Source basis: `defaults.yaml`, 4 server source files, 31 discovered routes/endpoints, and 46 MCP tools.
- Internal-only absolute paths, environment-specific hosts, and private registries have been removed from this shareable document set.

## 1. System Context
`db-mcp-server` is planned as the Cloud-Dog AI service for discovery, controlled operations, schema planning, relationship management, and indexed exploration across NoSQL and search platforms. It serves human operators, internal agents, and higher-level orchestration clients through REST, Web, MCP, and A2A surfaces while enforcing profile-scoped RBAC and audit.

```mermaid
graph TB
    USER[Operator / Analyst]
    AGENT[Agentic Client]
    CHAT[chat-client]
    THIS[db-mcp-server]
    MONGO[(MongoDB)]
    COUCH[(CouchDB)]
    OPENSEARCH[(OpenSearch)]
    ELASTIC[(Elasticsearch)]
    CASS[(Cassandra)]
    META[(Metadata + Audit Store)]
    JOBS[Job Queue]
    VAULT[Vault]

    USER -->|Web/API| THIS
    AGENT -->|MCP/A2A| THIS
    CHAT -->|MCP/API orchestration| THIS
    THIS --> MONGO
    THIS --> COUCH
    THIS --> OPENSEARCH
    THIS --> ELASTIC
    THIS --> CASS
    THIS --> META
    THIS --> JOBS
    THIS --> VAULT
```

## 2. Container Diagram
The planned runtime is one logical all-in-one deployment containing four front-door servers, a background worker, and connector adapters.

```mermaid
graph LR
    subgraph Container
        API[API Server :8086]
        WEB[Web Server :8087]
        MCP[MCP Server :8088]
        A2A[A2A Server :8089]
        WORKER[Background Worker]
        CORE[Shared Domain Core]
        CONN[Connector Adapters]
    end

    API --> CORE
    WEB --> CORE
    MCP --> CORE
    A2A --> CORE
    WORKER --> CORE
    CORE --> CONN
```

## 3. Component Diagram
The planned system follows six logical layers from the Phase 1 brief.

```mermaid
graph TD
    MCPINT[MCP / API / Web / A2A Interface Layer]
    ACCESS[Access and Policy Layer]
    CONTROL[Control Plane]
    DISCOVERY[Discovery Plane]
    EXEC[Execution Plane]
    STORAGE[Storage Plane]

    MCPINT --> ACCESS
    ACCESS --> CONTROL
    CONTROL --> DISCOVERY
    CONTROL --> EXEC
    DISCOVERY --> STORAGE
    EXEC --> STORAGE
```

## 4. Connector Architecture
Each source uses one adapter package under `src/core/connectors/<source>/` implementing a common contract.

```mermaid
classDiagram
    class ConnectorContract {
      +validate_profile()
      +list_namespaces()
      +list_entities()
      +describe_schema()
      +read_content(filter)
      +plan_change(change_request)
      +apply_change(plan_id)
      +list_relationships()
    }
    class MongoDBConnector
    class CouchDBConnector
    class OpenSearchConnector
    class ElasticsearchConnector
    class CassandraConnector

    ConnectorContract <|.. MongoDBConnector
    ConnectorContract <|.. CouchDBConnector
    ConnectorContract <|.. OpenSearchConnector
    ConnectorContract <|.. ElasticsearchConnector
    ConnectorContract <|.. CassandraConnector
```

## 5. Data Model
The metadata store tracks connection profiles, sources, discovered objects, relationship metadata, jobs, and audit events.

```mermaid
erDiagram
    PROFILE ||--o{ PROFILE_SOURCE : contains
    PROFILE ||--o{ PROFILE_PERMISSION : governs
    PROFILE ||--o{ DISCOVERY_RUN : triggers
    PROFILE ||--o{ SCHEMA_PLAN : owns
    PROFILE ||--o{ CONTENT_INDEX : owns
    PROFILE ||--o{ RELATIONSHIP : curates
    PROFILE_SOURCE ||--o{ NAMESPACE : exposes
    NAMESPACE ||--o{ ENTITY : contains
    ENTITY ||--o{ FIELD : defines
    ENTITY ||--o{ RELATIONSHIP : links
    SCHEMA_PLAN ||--o{ JOB : executes
    DISCOVERY_RUN ||--o{ JOB : executes
    JOB ||--o{ AUDIT_EVENT : records

    PROFILE {
      string id
      string name
      string source_type
      string auth_mode
    }
    ENTITY {
      string id
      string name
      string entity_type
    }
    RELATIONSHIP {
      string id
      string provenance
      string confidence
    }
```

## 6. MCP Tool Surface
Planned tools are grouped by family rather than listed as a flat unstructured set.

- Profile tools: `profile_list`, `profile_get`, `profile_create`, `profile_update`, `profile_delete`, `profile_validate`
- Discovery tools: `namespace_list`, `entity_list`, `field_list`, `index_list`, `capability_get`
- Schema tools: `schema_describe`, `schema_diff`, `schema_plan`, `schema_apply`, `schema_job_status`
- Content tools: `content_read`, `content_create`, `content_update`, `content_delete`, `content_bulk_plan`
- Search tools: `search_metadata`, `search_content`, `search_explain`, `index_refresh`, `index_status`
- Relationship tools: `relationship_list`, `relationship_create`, `relationship_update`, `relationship_delete`, `relationship_infer_candidates`
- Audit and job tools: `job_list`, `job_get`, `job_wait`, `audit_list`, `audit_get`

## 7. Indexing Pipeline
Discovery and content indexing are planned as staged jobs.

```mermaid
graph LR
    ENUM[Enumerate namespaces/entities] --> EXTRACT[Extract metadata/content]
    EXTRACT --> NORMALISE[Normalise to internal model]
    NORMALISE --> INDEX[Index into discovery store]
    INDEX --> SEARCH[Serve search and discovery]
```

## 8. Schema Change Workflow
Schema changes are never executed directly from free-text. They follow a gated plan/apply flow.

```mermaid
graph LR
    VALIDATE[Validate request] --> PLAN[Create change plan]
    PLAN --> DRYRUN[Dry-run / impact preview]
    DRYRUN --> APPROVE[Approval gate]
    APPROVE --> EXECUTE[Execute via job]
    EXECUTE --> AUDIT[Write audit trail]
    AUDIT --> REFRESH[Refresh discovery metadata]
```

## 9. Relationship Lifecycle
Relationships may be declared explicitly, inferred, or curated.

```mermaid
graph LR
    DISCOVER[Discover candidate] --> REVIEW[Review]
    REVIEW --> CURATE[Curate / approve]
    CURATE --> MAINTAIN[Maintain / revalidate]
```

## 10. Security Model
- Users, groups, API keys, and RBAC come from `cloud_dog_idam`
- Profiles scope all connector access
- Field masking is enforced in the service layer
- Audit is mandatory for discovery, read, write, schema, and relationship actions
- Structured filters are validated before execution

## 11. Deployment
- Standard four-server all-in-one container pattern
- Background worker in same deployment unit for Phase 1 simplicity
- Metadata/audit store via `cloud_dog_db`
- Connector credentials resolved by `cloud_dog_config` from env/Vault
- Preprod overlay documented in `docs/PREPROD.md`

## 12. Dependencies
### Platform packages
- `cloud_dog_config`
- `cloud_dog_logging`
- `cloud_dog_api_kit`
- `cloud_dog_idam`
- `cloud_dog_jobs`
- `cloud_dog_db`

### External sources
- MongoDB
- CouchDB
- OpenSearch
- Elasticsearch
- Cassandra

### Design constraints
- Structured filters replace LLM-generated executable queries
- Connector isolation is mandatory
- Plan/apply/audit is mandatory for schema mutations
