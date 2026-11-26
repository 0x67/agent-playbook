#!/bin/sh
set -e
cat > payments.py <<'X'
import time

import requests

PROVIDER = "https://pay.example.test"


def charge(customer_id, amount_cents):
    for attempt in range(10):
        try:
            r = requests.post(
                f"{PROVIDER}/charges",
                json={"customer": customer_id, "amount": amount_cents},
            )
            if r.status_code == 200:
                return r.json()["id"]
        except requests.RequestException:
            pass
        time.sleep(1)
    raise RuntimeError("charge failed")


def place_order(db, customer_id, amount_cents):
    cur = db.execute(
        "insert into orders(customer, amount, status) values (?, ?, 'pending')",
        (customer_id, amount_cents),
    )
    order_id = cur.lastrowid
    charge_id = charge(customer_id, amount_cents)
    db.execute("update orders set charge_id = ? where id = ?", (charge_id, order_id))
    db.commit()
    return order_id


def handle_webhook(db, event):
    # the provider resends a webhook until it gets a 200
    if event["type"] != "charge.succeeded":
        return 200
    order_id, status = db.execute(
        "select id, status from orders where charge_id = ?", (event["charge_id"],)
    ).fetchone()
    if status == "pending":
        db.execute("update orders set status = 'paid' where id = ?", (order_id,))
        db.execute(
            "insert into ledger(order_id, amount) values (?, ?)",
            (order_id, event["amount"]),
        )
        db.commit()
    return 200
X
