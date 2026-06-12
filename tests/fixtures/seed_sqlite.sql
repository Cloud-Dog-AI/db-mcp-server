PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
  id INTEGER PRIMARY KEY,
  email TEXT NOT NULL UNIQUE,
  display_name TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_users_email ON users(email);

CREATE TABLE orders (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id),
  amount NUMERIC NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_status ON orders(status);

INSERT INTO users (id, email, display_name) VALUES
  (1, 'alice@example.test', 'Alice'),
  (2, 'bob@example.test',   'Bob'),
  (3, 'carol@example.test', 'Carol'),
  (4, 'dave@example.test',  'Dave'),
  (5, 'eve@example.test',   'Eve');

INSERT INTO orders (id, user_id, amount, status) VALUES
  (1, 1, 12.50, 'paid'),
  (2, 1, 99.00, 'paid'),
  (3, 2, 5.00,  'refunded'),
  (4, 3, 250.00,'paid'),
  (5, 4, 7.25,  'pending'),
  (6, 4, 18.50, 'failed'),
  (7, 5, 20.00, 'paid');
