#!/bin/sh
set -e
cat > server.py <<'X'
from http.server import BaseHTTPRequestHandler, HTTPServer
import json

USERS = {"alice": "s3cret"}

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/login":
            self.send_response(404); self.end_headers(); return
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        ok = USERS.get(body.get("user")) == body.get("password")
        self.send_response(200 if ok else 401); self.end_headers()

if __name__ == "__main__":
    HTTPServer(("", 8080), Handler).serve_forever()
X
