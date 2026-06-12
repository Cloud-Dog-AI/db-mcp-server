CREATE TABLE IF NOT EXISTS source_connections (
    name VARCHAR(100) PRIMARY KEY,
    source_type VARCHAR(50) NOT NULL,
    uri_template VARCHAR(1024) NOT NULL,
    credentials_ref VARCHAR(512),
    description TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'not_tested',
    last_tested_at TIMESTAMP NULL,
    last_test_result JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_source_connections_name
        CHECK (name REGEXP '^[a-z0-9_-]{1,100}$'),
    CONSTRAINT chk_source_connections_source_type
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
    CONSTRAINT chk_source_connections_status
        CHECK (status IN ('healthy', 'degraded', 'failing', 'not_tested', 'disabled'))
);

CREATE INDEX idx_source_connections_source_type
    ON source_connections(source_type);

CREATE INDEX idx_source_connections_status
    ON source_connections(status);
