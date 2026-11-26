#!/bin/sh
set -e
mkdir -p migrations api
cat > NOTES.md <<'X'
orders has about 80 million rows. Deploys replace instances one at a time, so old and new code run together for
about ten minutes. GET /orders/{id} is called by partner integrations outside the company.
X
cat > migrations/0042_orders.sql <<'X'
ALTER TABLE orders RENAME COLUMN total TO total_cents;
ALTER TABLE orders ADD COLUMN currency text;
UPDATE orders SET currency = 'USD';
ALTER TABLE orders ALTER COLUMN currency SET NOT NULL;
CREATE INDEX orders_customer_idx ON orders (customer_id);
X
cat > api/orders.py <<'X'
def order_response(order):
    # was {"id", "total", "status"} before this change
    return {
        "id": order.id,
        "total_cents": order.total_cents,
        "currency": order.currency,
        "status": order.status,
    }
X
