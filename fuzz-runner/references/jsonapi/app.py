"""JSON-API reference (stdlib only): a form-less API that publishes an OpenAPI spec. Exercises the
spec-driven discovery + error-based SQLi path that references/vulnerable (HTML-form only) can't.

- GET /openapi.json      the spec -> the discoverable API surface (no HTML to crawl)
- GET /api/items/{id}    INJECTABLE: id is concatenated into SQL; a lone quote -> a leaked DB error
- GET /api/notes?q=      SAFE: q is parameterized; a quote is inert data, never an error

api_sqli must fire on /api/items/{id} and stay clean on /api/notes (the differential's precision).
"""
import http.server
import json
import os
from urllib.parse import parse_qs, unquote, urlparse

PORT = int(os.environ.get("PORT", "8080"))

SPEC = {
    "openapi": "3.0.0",
    "info": {"title": "jsonapi-ref", "version": "1.0"},
    "paths": {
        "/api/items/{id}": {
            "get": {"parameters": [
                {"in": "path", "name": "id", "required": True, "schema": {"type": "string"}}]}
        },
        "/api/notes": {
            "get": {"parameters": [
                {"in": "query", "name": "q", "schema": {"type": "string"}}]}
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
        else:
            _send(self, 404, "application/json", b'{"error":"not found"}')


if __name__ == "__main__":
    http.server.HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
