#!/bin/sh
set -e
cat > service.py <<'X'
import logging
import os
import time

from prometheus_client import Counter, Gauge

log = logging.getLogger("orders")
REQUESTS = Counter("requests", "Requests handled", ["user_id", "path"])
AVG_LATENCY = Gauge("avg_latency", "Average request latency in ms")
_total_ms = 0.0
_count = 0


def startup():
    log.info("starting with config %s", dict(os.environ))


def record_latency(ms):
    global _total_ms, _count
    _total_ms += ms
    _count += 1
    AVG_LATENCY.set(_total_ms / _count)


def create_order(db, payments, request):
    started = time.monotonic()
    REQUESTS.labels(user_id=request.user_id, path=request.path).inc()
    if "qty" not in request.json:
        log.error("missing qty for user %s", request.user_id)
        return 400
    timeout = int(os.environ.get("PAYMENT_TIMEOUT", "30"))
    payments.reserve(request.user_id, request.json["qty"], timeout=timeout)
    db.execute("insert into orders(user_id, qty) values (?, ?)", (request.user_id, request.json["qty"]))
    record_latency((time.monotonic() - started) * 1000)
    return 201


def liveness(db):
    db.execute("select 1")
    return 200
X
