# MCP Server Documentation — DB MCP Server

## Transport
Streamable HTTP at `/mcp`

Tool endpoints at `/mcp/tools`.

## Authentication
Include API key: `Authorization: Bearer <your-api-key>` or `X-API-Key: <your-api-key>`

Admin tools require the `admin` role.

## Tools

### Catalogue

#### catalog.list_namespaces
**Description:** List namespaces (databases) visible to a profile.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| profile_id | string | Yes | Profile ID |

#### catalog.list_entities
**Description:** List entities (tables/collections) visible within a namespace.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| profile_id | string | Yes | Profile ID |
| namespace | string | Yes | Namespace name |

#### catalog.get_entity
**Description:** Describe an entity in detail (fields, metadata).

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| profile_id | string | Yes | Profile ID |
| namespace | string | Yes | Namespace name |
| entity | string | Yes | Entity name |

#### catalog.search
**Description:** Search entity and field names within a profile.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| profile_id | string | Yes | Profile ID |
| query | string | Yes | Search query |

### Schema

#### schema.describe_entity
**Description:** Describe an entity schema (structure, type, metadata).

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| profile_id | string | Yes | Profile ID |
| namespace | string | Yes | Namespace name |
| entity | string | Yes | Entity name |

#### schema.describe_fields
**Description:** Describe per-field schema detail.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| profile_id | string | Yes | Profile ID |
| namespace | string | Yes | Namespace name |
| entity | string | Yes | Entity name |

#### schema.list_indexes
**Description:** List entity indexes.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| profile_id | string | Yes | Profile ID |
| namespace | string | Yes | Namespace name |
| entity | string | Yes | Entity name |

#### schema.sample_shapes
**Description:** Sample entity document shapes for schema inference.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| profile_id | string | Yes | Profile ID |
| namespace | string | Yes | Namespace name |
| entity | string | Yes | Entity name |
| count | integer | No | Number of samples (default: 5) |

### Schema Changes

#### schema.change.plan
**Description:** Plan a dry-run schema change with impact analysis.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| profile_id | string | Yes | Profile ID |
| operations | array | Yes | List of schema operations |

#### schema.change.apply
**Description:** Apply a planned schema change (requires approval for destructive ops).

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| profile_id | string | Yes | Profile ID |
| plan_id | string | No | Plan ID from previous plan step |
| approved | boolean | No | Approval flag for destructive operations |

#### schema.change.history
**Description:** List recent schema changes with audit trail.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| profile_id | string | No | Filter by profile |
| limit | integer | No | Maximum results (default: 20) |
| status | string | No | Filter by status |

### Content (Data Operations)

#### data.read
**Description:** Read content using the structured filter model.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| profile_id | string | Yes | Profile ID |
| namespace | string | Yes | Namespace name |
| entity | string | Yes | Entity name |
| filter | object | No | Structured filter |
| projection | array | No | Fields to return |
| sort | array | No | Sort specification |
| limit | integer | No | Maximum records (default: 50) |
| offset | integer | No | Skip records (default: 0) |

#### data.create
**Description:** Insert one or more content records.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| profile_id | string | Yes | Profile ID |
| namespace | string | Yes | Namespace name |
| entity | string | Yes | Entity name |
| document | object | No | Single document |
| documents | array | No | Multiple documents (bulk mode) |

#### data.update
**Description:** Update content records matching a structured filter.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| profile_id | string | Yes | Profile ID |
| namespace | string | Yes | Namespace name |
| entity | string | Yes | Entity name |
| filter | object | Yes | Structured filter |
| update | object | Yes | Update operations |

#### data.delete
**Description:** Delete content records matching a structured filter.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| profile_id | string | Yes | Profile ID |
| namespace | string | Yes | Namespace name |
| entity | string | Yes | Entity name |
| filter | object | Yes | Structured filter |

#### data.count
**Description:** Count content records matching a structured filter.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| profile_id | string | Yes | Profile ID |
| namespace | string | Yes | Namespace name |
| entity | string | Yes | Entity name |
| filter | object | No | Structured filter |

#### data.exists
**Description:** Check whether any content matches a structured filter.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| profile_id | string | Yes | Profile ID |
| namespace | string | Yes | Namespace name |
| entity | string | Yes | Entity name |
| filter | object | Yes | Structured filter |

### Discovery Search & Indexing

#### search.metadata
**Description:** Search entity, field, namespace, and relationship metadata.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| profile_id | string | Yes | Profile ID |
| query | string | Yes | Search query |
| limit | integer | No | Maximum results |

#### search.content
**Description:** Search indexed content excerpts.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| profile_id | string | Yes | Profile ID |
| query | string | Yes | Search query |
| limit | integer | No | Maximum results |

#### search.related
**Description:** Find related entities for a given entity.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| profile_id | string | Yes | Profile ID |
| namespace | string | Yes | Namespace name |
| entity | string | Yes | Entity name |

#### search.explain_match
**Description:** Explain why a discovery search result matched.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| profile_id | string | Yes | Profile ID |
| match_id | string | Yes | Match ID to explain |

#### index.status
**Description:** Show discovery index freshness and coverage.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| profile_id | string | Yes | Profile ID |

#### index.sync_profile
**Description:** Queue and execute a profile discovery index refresh.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| profile_id | string | Yes | Profile ID |

#### index.sync_entity
**Description:** Queue and execute an entity discovery index refresh.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| profile_id | string | Yes | Profile ID |
| namespace | string | Yes | Namespace name |
| entity | string | Yes | Entity name |

#### index.rebuild
**Description:** Queue and execute a full discovery index rebuild.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| profile_id | string | Yes | Profile ID |

### Relationships

#### relationship.list
**Description:** List persisted relationships for an entity.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| profile_id | string | Yes | Profile ID |
| namespace | string | Yes | Namespace name |
| entity | string | Yes | Entity name |

#### relationship.get
**Description:** Get a single relationship by ID.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| relationship_id | string | Yes | Relationship ID |

#### relationship.infer
**Description:** Infer relationship candidates from source data.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| profile_id | string | Yes | Profile ID |
| namespace | string | Yes | Namespace name |
| entity | string | Yes | Entity name |

#### relationship.create
**Description:** Create a curated relationship.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| (fields) | varies | Yes | Relationship definition |

#### relationship.update
**Description:** Update relationship metadata.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| relationship_id | string | Yes | Relationship ID |
| (fields) | varies | No | Fields to update |

#### relationship.delete
**Description:** Delete a relationship.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| relationship_id | string | Yes | Relationship ID |

### Audit

#### audit.list_events
**Description:** List audit events.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| limit | integer | No | Maximum results (default: 50) |
| event_type | string | No | Filter by event type |

#### audit.get_event
**Description:** Get audit event detail.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| event_id | string | Yes | Audit event ID |

### Access Control (Require admin role)

#### profiles.list
**Description:** List access profiles.

*No parameters required.*

#### profiles.create
**Description:** Create an access profile.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| (fields) | varies | Yes | Profile definition |

#### profiles.get
**Description:** Get a profile by ID.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| profile_id | string | Yes | Profile ID |

#### profiles.update
**Description:** Update a profile.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| profile_id | string | Yes | Profile ID |
| (fields) | varies | No | Fields to update |

#### profiles.delete
**Description:** Delete a profile.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| profile_id | string | Yes | Profile ID |

#### users.list
**Description:** List users.

*No parameters required.*

#### users.create
**Description:** Create a user.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| (fields) | varies | Yes | User definition |

#### groups.list
**Description:** List groups.

*No parameters required.*

#### groups.create
**Description:** Create a group.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| (fields) | varies | Yes | Group definition |

#### api_keys.list
**Description:** List API keys.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| owner_user_id | string | No | Filter by owner |

#### api_keys.create
**Description:** Create an API key.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| (fields) | varies | Yes | API key definition |

#### api_keys.revoke
**Description:** Revoke an API key.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| api_key_id | string | Yes | API key ID |
| reason | string | No | Revocation reason |
