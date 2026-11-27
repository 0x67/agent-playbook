#!/bin/sh
set -e
cat > api.py <<'X'
import hashlib
import pickle
import subprocess

import requests


def get_order(db, request):
    order_id = request.args["id"]
    return db.execute(f"select * from orders where id = {order_id}").fetchone()


def update_profile(db, request):
    user = db.get_user(request.json["user_id"])
    for field, value in request.json.items():
        setattr(user, field, value)
    db.save(user)


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def export_dir(request):
    subprocess.run(f"tar czf /tmp/export.tgz {request.args['dir']}", shell=True)


def fetch_avatar(request):
    return requests.get(request.json["avatar_url"], timeout=5).content


def load_session(cookie):
    return pickle.loads(bytes.fromhex(cookie))
X
