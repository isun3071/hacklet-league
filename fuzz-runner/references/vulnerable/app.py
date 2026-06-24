"""Deliberately-vulnerable reference app (stdlib only). The slop_detected anchor.

Same surface as references/hardened, but: string-formatted SQL (injectable login), reflects
search input unescaped (XSS), no security headers, leaks stack traces, and a slow endpoint.
Trusted code we wrote, safe to run as a local subprocess; real submissions are untrusted and
only ever run in the sandboxed container.
"""
import http.server
import os
import sqlite3
import time
import traceback
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
        self.end_headers()  # note: no security headers
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/":
            return self._send(200, HOME)
        if self.path.startswith("/search"):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get("q", [""])[0]
            return self._send(200, "<p>results for: " + q + "</p>")  # reflects raw -> XSS
        if self.path == "/crash":
            try:
                raise ValueError("kaboom while rendering report")
            except ValueError:
                return self._send(500, "Internal Error\n\n" + traceback.format_exc())  # leaks trace
        if self.path.startswith("/heavy"):
            time.sleep(3.5)  # slow: blows past the TTFB gate
            return self._send(200, "done")
        return self._send(404, "not found")

    def do_POST(self):
        if self.path == "/login":
            length = int(self.headers.get("Content-Length", "0"))
            form = urllib.parse.parse_qs(self.rfile.read(length).decode())
            user = form.get("username", [""])[0]
            pw = form.get("password", [""])[0]
            query = "SELECT name FROM users WHERE name='%s' AND pw='%s'" % (user, pw)  # injectable
            try:
                row = _db.execute(query).fetchone()
            except Exception:
                return self._send(500, traceback.format_exc())
            if row:
                return self._send(200, "welcome " + row[0])
            return self._send(401, "invalid credentials")
        if self.path == "/profile":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                form = urllib.parse.parse_qs(self.rfile.read(length).decode())
                age = int(form["age"][0])  # KeyError if missing, ValueError if non-numeric
                return self._send(200, "age is " + str(age))
            except Exception:
                return self._send(500, traceback.format_exc())  # unhandled -> 500 + leaks trace
        return self._send(404, "not found")


if __name__ == "__main__":
    http.server.HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
