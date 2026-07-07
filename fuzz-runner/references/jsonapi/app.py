"""JSON-API reference (stdlib only): a form-less API that publishes an OpenAPI spec. Exercises the
spec-driven discovery + error-based SQLi path that references/vulnerable (HTML-form only) can't.

- GET  /openapi.json      the spec -> the discoverable API surface (no HTML to crawl)
- GET  /api/items/{id}    INJECTABLE: id is concatenated into SQL; a lone quote -> a leaked DB error
- GET  /api/notes?q=      SAFE: q is parameterized; a quote is inert data, never an error
- GET  /api/dump          LEAKY: returns user records including plaintext "password" fields (exposure)
- POST /api/register, /api/login   self-as-oracle auth (login returns {"token": <username>})
- POST /api/orders        create an order carrying a private "secret" (auth required)
- GET  /api/orders/{id}   BOLA: returns ANY authed caller's-or-not order incl. its secret (no owner check)

api_sqli fires on /api/items/{id}, clean on /api/notes; response_leaks_credentials fires on /api/dump;
api_bola fires on /api/orders/{id} (B reads A's order + secret) — all clean on the safe endpoints.
"""
import http.server
import json
import os
from urllib.parse import parse_qs, unquote, urlparse

PORT = int(os.environ.get("PORT", "8080"))

USERS = {}          # username -> password
ORDERS = {}         # id -> {owner, item, secret}
_STATE = {"next_id": 1}

_STR = {"type": "string"}
SPEC = {
    "openapi": "3.0.0",
    "info": {"title": "jsonapi-ref", "version": "1.0"},
    "paths": {
        "/api/items/{id}": {
            "get": {"parameters": [
                {"in": "path", "name": "id", "required": True, "schema": _STR}]}
        },
        "/api/notes": {
            "get": {"parameters": [{"in": "query", "name": "q", "schema": _STR}]}
        },
        "/api/dump": {"get": {}},
        "/api/register": {"post": {"requestBody": {"content": {"application/json": {
            "schema": {"properties": {"username": _STR, "email": _STR, "password": _STR}}}}}}},
        "/api/login": {"post": {"requestBody": {"content": {"application/json": {
            "schema": {"properties": {"username": _STR, "password": _STR}}}}}}},
        "/api/orders": {"post": {"requestBody": {"content": {"application/json": {
            "schema": {"properties": {"item": _STR, "secret": _STR}}}}}}},
        "/api/orders/{id}": {
            "get": {"parameters": [{"in": "path", "name": "id", "required": True, "schema": _STR}]}
        },
    },
}


def _send(h, code, ctype, body: bytes):
    h.send_response(code)
    h.send_header("Content-Type", ctype)
    h.send_header("Content-Length", str(len(body)))
    h.end_headers()
    h.wfile.write(body)


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/openapi.json":
            _send(self, 200, "application/json", json.dumps(SPEC).encode())
        elif u.path.startswith("/api/items/"):
            item_id = unquote(u.path[len("/api/items/"):])
            sql = "SELECT * FROM items WHERE id = '%s'" % item_id  # unparameterized -> injectable
            if "'" in item_id:  # a lone quote breaks the string literal -> the framework leaks a DB error
                body = ('sqlite3.OperationalError: unrecognized token near "\'"\n[SQL: %s]' % sql).encode()
                _send(self, 500, "text/html; charset=utf-8", body)
            else:
                _send(self, 200, "application/json", json.dumps({"id": item_id, "name": "item"}).encode())
        elif u.path == "/api/notes":
            q = parse_qs(u.query).get("q", [""])[0]  # parameterized: quote is data, never grammar
            _send(self, 200, "application/json", json.dumps({"query": q, "notes": []}).encode())
        elif u.path == "/api/dump":  # excessive data exposure: returns password material to any caller
            users = [{"username": "alice", "email": "alice@x.com", "password": "hunter2"},
                     {"username": "bob", "email": "bob@x.com", "password": "s3cret!"}]
            _send(self, 200, "application/json", json.dumps({"users": users}).encode())
        elif u.path.startswith("/api/orders/"):
            if self._bearer() is None:  # auth-gated (so it's genuine BOLA, not a public endpoint)
                _send(self, 401, "application/json", b'{"error":"unauthorized"}')
                return
            order = ORDERS.get(unquote(u.path[len("/api/orders/"):]))
            if order is None:
                _send(self, 404, "application/json", b'{"error":"not found"}')
            else:  # BOLA: any authed caller reads any order incl. its secret — no owner check
                _send(self, 200, "application/json", json.dumps({"id": order["id"], **order}).encode())
        else:
            _send(self, 404, "application/json", b'{"error":"not found"}')

    def _bearer(self):
        h = self.headers.get("Authorization", "")
        return h[7:] if h.startswith("Bearer ") and h[7:] in USERS else None

    def _json_body(self):
        try:
            n = int(self.headers.get("Content-Length", 0))
            return json.loads(self.rfile.read(n) or b"{}")
        except (ValueError, json.JSONDecodeError):
            return {}

    def do_POST(self):
        u = urlparse(self.path)
        body = self._json_body()
        if u.path == "/api/register":
            USERS[body.get("username", "")] = body.get("password", "")
            _send(self, 200, "application/json", b'{"status":"registered"}')
        elif u.path == "/api/login":
            user = body.get("username", "")
            if user in USERS and USERS[user] == body.get("password"):
                _send(self, 200, "application/json", json.dumps({"token": user}).encode())
            else:
                _send(self, 401, "application/json", b'{"error":"bad credentials"}')
        elif u.path == "/api/orders":
            owner = self._bearer()
            if owner is None:
                _send(self, 401, "application/json", b'{"error":"unauthorized"}')
                return
            oid = str(_STATE["next_id"])
            _STATE["next_id"] += 1
            ORDERS[oid] = {"id": oid, "owner": owner, "item": body.get("item", ""),
                           "secret": body.get("secret", "")}
            _send(self, 201, "application/json", json.dumps({"id": oid}).encode())
        else:
            _send(self, 404, "application/json", b'{"error":"not found"}')


if __name__ == "__main__":
    http.server.HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
