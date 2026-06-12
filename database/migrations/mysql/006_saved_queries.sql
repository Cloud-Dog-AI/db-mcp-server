CREATE TABLE IF NOT EXISTS saved_queries (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    page_key VARCHAR(64) NOT NULL,
    name VARCHAR(120) NOT NULL,
    description TEXT,
    payload JSON NOT NULL,
    shared BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_saved_queries_user_page_name (user_id, page_key, name)
);

CREATE INDEX idx_saved_queries_user_page
    ON saved_queries(user_id, page_key);
