# Canonical Connector Test Dataset

## Domain
E-commerce platform used to validate discovery, CRUD, search, aggregation, schema, and relationship behaviour across every db-mcp connector.

## Entities

| Entity | Fields | Records | Relationships |
|---|---|---:|---|
| customers | `_id`, `name`, `email`, `country`, `industry`, `status`, `tier`, `created_at`, `updated_at` | 25 | `orders.customer_id -> customers._id`, `invoices.customer_id -> customers._id` |
| orders | `_id`, `customer_id`, `product_id`, `quantity`, `unit_price`, `total`, `status`, `order_date`, `ship_date` | 50 | `orders.customer_id -> customers._id`, `orders.product_id -> products._id` |
| products | `_id`, `name`, `category`, `subcategory`, `price`, `stock`, `supplier_id`, `description`, `tags[]` | 20 | `products.supplier_id -> suppliers._id`, `orders.product_id -> products._id` |
| suppliers | `_id`, `name`, `country`, `rating`, `contact_email`, `active` | 10 | `products.supplier_id -> suppliers._id` |
| invoices | `_id`, `order_id`, `customer_id`, `amount`, `tax`, `total`, `status`, `issued_date`, `due_date`, `paid_date` | 35 | `invoices.order_id -> orders._id`, `invoices.customer_id -> customers._id` |

## Field Variety
- String: `name`, `email`, `country`, `status`, `description`, `tier`, `category`, `subcategory`
- Numeric: `quantity`, `unit_price`, `total`, `price`, `stock`, `rating`, `amount`, `tax`
- Date or datetime-like strings: `created_at`, `updated_at`, `order_date`, `ship_date`, `issued_date`, `due_date`, `paid_date`
- Boolean: `active`
- Array: `tags`
- References: `customer_id`, `product_id`, `supplier_id`, `order_id`

## Data Features
- Countries span `UK`, `US`, `DE`, `FR`, `JP`
- Customer statuses cover `active` and `inactive`
- Order statuses cover `open`, `processing`, `shipped`, `delivered`, `cancelled`
- Invoice statuses cover `issued`, `paid`, `overdue`, `partially_paid`, `void`
- Date ranges span `2025-01` through `2026-12`
- Optional NULL values exist in `updated_at`, `description`, `contact_email`, `ship_date`, and `paid_date`
- Cross-entity references are complete and deterministic

## Cross-Backend Expectations
Every connector seed module must preserve:
- record counts
- reference integrity
- array typing for `tags`
- booleans for `active`
- numeric precision for prices and totals
- ability to filter by country, status, date range, and numeric thresholds
