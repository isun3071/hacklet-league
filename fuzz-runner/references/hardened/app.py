"""Hardened reference app (stdlib only). The clean anchor / false-positive guard.

Identical surface to references/vulnerable, defended correctly: parameterized SQL, escaped search
reflection, security headers set, generic errors (no stack traces), fast endpoints. Every probe
must read clean here.
"""
import html
import http.server
import os
import sqlite3
import urllib.parse

PORT = int(os.environ.get("PORT", "8080"))

_db = sqlite3.connect(":memory:", check_same_thread=False)
_db.execute("CREATE TABLE users (name TEXT, pw TEXT)")
_db.execute("INSERT INTO users VALUES ('alice', 's3cret')")
_db.commit()

HOME = b"""<!doctype html><html><body>
<h1>demo app</h1>
<a href="/login">login</a> | <a href="/search">search</a> | <a href="/crash">crash</a> | <a href="/heavy">heavy</a>
<form action="/login" method="post">
  <input name="username" placeholder="user">
  <input name="password" type="password" placeholder="pw">
  <button type="submit">log in</button>
</form>
</body></html>"""


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _send(self, code, body, ctype="text/html; charset=utf-8"):
        if isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")  # security header set
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/":
            return self._send(200, HOME)
        if self.path.startswith("/search"):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get("q", [""])[0]
            return self._send(200, "<p>results for: " + html.escape(q) + "</p>")  # escaped
        if self.path == "/crash":
            return self._send(500, "Internal Server Error")  # generic, no stack trace
        if self.path.startswith("/heavy"):
            return self._send(200, "done")  # fast
        return self._send(404, "not found")

    def do_POST(self):
        if self.path == "/login":
            length = int(self.headers.get("Content-Length", "0"))
            form = urllib.parse.parse_qs(self.rfile.read(length).decode())
            user = form.get("username", [""])[0]
            pw = form.get("password", [""])[0]
            row = _db.execute(
                "SELECT name FROM users WHERE name=? AND pw=?", (user, pw)  # parameterized
            ).fetchone()
            if row:
                return self._send(200, "welcome " + row[0])
            return self._send(401, "invalid credentials")
        if self.path == "/profile":
            length = int(self.headers.get("Content-Length", "0"))
            form = urllib.parse.parse_qs(self.rfile.read(length).decode())
            raw = form.get("age", [""])[0]
            if not raw.isdigit():
                return self._send(400, "invalid age")  # graceful, no crash
            return self._send(200, "age is " + raw)
        return self._send(404, "not found")


if __name__ == "__main__":
    # Bind 0.0.0.0: reachable as a dev/CI subprocess AND via the published port inside the
    # DockerDeployer container (a 127.0.0.1 binding is unreachable through Docker's port forward).
    http.server.HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
