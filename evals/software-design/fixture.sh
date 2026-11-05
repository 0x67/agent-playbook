#!/bin/sh
set -e
cat > orders.py <<'X'
import json, sqlite3, smtplib

class OrderManager:
    def process(self, data, flag):
        db = sqlite3.connect("shop.db")
        d = json.loads(data)
        total = 0
        for i in d["items"]:
            if i["qty"] <= 0:
                raise ValueError("bad qty")
            total += i["price"] * i["qty"]
        if flag:
            total = total * 0.9
        db.execute("insert into orders(customer, total) values (?, ?)", (d["customer"], total))
        db.commit()
        s = smtplib.SMTP("localhost")
        s.sendmail("shop@example.com", d["email"], f"Order total: {total}")
        return {"ok": True, "total": total}
X
