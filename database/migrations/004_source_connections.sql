CREATE TABLE IF NOT EXISTS source_connections (
    name VARCHAR(100) PRIMARY KEY,
    source_type VARCHAR(50) NOT NULL,
    uri_template VARCHAR(1024) NOT NULL,
    credentials_ref VARCHAR(512),
    description TEXT NOT NULL DEFAULT '',
    status VARCHAR(20) NOT NULL DEFAULT 'not_tested',
    last_tested_at TIMESTAMP,
    last_test_result TEXT NOT NULL DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (length(name) BETWEEN 1 AND 100),
    CHECK (name NOT GLOB '*[^a-z0-9_-]*'),
    CHECK (source_type IN (
        'postgres',
        'postgresql',
        'mysql',
        'mariadb',
        'sqlite',
        'mongodb',
        'elasticsearch',
        'opensearch',
        'couchdb',
        'cassandra'
    )),
    CHECK (status IN ('healthy', 'degraded', 'failing', 'not_tested', 'disabled'))
);

CREATE INDEX IF NOT EXISTS idx_source_connections_source_type
    ON source_connections(source_type);

CREATE INDEX IF NOT EXISTS idx_source_connections_status
    ON source_connections(status);
