CREATE TABLE IF NOT EXISTS saved_queries (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    page_key VARCHAR(64) NOT NULL,
    name VARCHAR(120) NOT NULL,
    description TEXT,
    payload JSONB NOT NULL,
    shared BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, page_key, name)
);

CREATE INDEX IF NOT EXISTS idx_saved_queries_user_page
    ON saved_queries(user_id, page_key);
