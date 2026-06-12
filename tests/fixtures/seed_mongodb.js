db.users.drop();
db.orders.drop();

db.users.insertMany([
  {_id: 1, id: 1, email: "alice@example.test", display_name: "Alice"},
  {_id: 2, id: 2, email: "bob@example.test", display_name: "Bob"},
  {_id: 3, id: 3, email: "carol@example.test", display_name: "Carol"},
  {_id: 4, id: 4, email: "dave@example.test", display_name: "Dave"},
  {_id: 5, id: 5, email: "eve@example.test", display_name: "Eve"}
]);

db.orders.insertMany([
  {_id: 1, id: 1, user_id: 1, amount: 12.50, status: "paid"},
  {_id: 2, id: 2, user_id: 1, amount: 99.00, status: "paid"},
  {_id: 3, id: 3, user_id: 2, amount: 5.00, status: "refunded"},
  {_id: 4, id: 4, user_id: 3, amount: 250.00, status: "paid"},
  {_id: 5, id: 5, user_id: 4, amount: 7.25, status: "pending"},
  {_id: 6, id: 6, user_id: 4, amount: 18.50, status: "failed"},
  {_id: 7, id: 7, user_id: 5, amount: 20.00, status: "paid"}
]);

db.users.createIndex({email: 1}, {name: "idx_users_email", unique: true});
db.orders.createIndex({user_id: 1}, {name: "idx_orders_user_id"});
db.orders.createIndex({status: 1}, {name: "idx_orders_status"});
