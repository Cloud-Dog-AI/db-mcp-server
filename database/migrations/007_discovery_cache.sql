CREATE TABLE IF NOT EXISTS discovery_cache (
    profile_id VARCHAR(64) NOT NULL,
    cache_key VARCHAR(120) NOT NULL,
    payload TEXT NOT NULL,
    refreshed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ttl_seconds INTEGER DEFAULT 600,
    PRIMARY KEY (profile_id, cache_key)
);
