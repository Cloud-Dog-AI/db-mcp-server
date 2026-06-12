CREATE TABLE IF NOT EXISTS profile_source_connections (
    profile_id VARCHAR(64) PRIMARY KEY,
    source_connection_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (profile_id) REFERENCES profiles(profile_id) ON DELETE CASCADE,
    FOREIGN KEY (source_connection_name) REFERENCES source_connections(name)
);

CREATE INDEX IF NOT EXISTS idx_profile_source_connections_source
    ON profile_source_connections(source_connection_name);
