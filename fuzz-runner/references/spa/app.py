"""SPA reference (stdlib only). The login/register form is built by client-side JS via
createElement, so it does NOT appear in the static HTML source — a static crawl misses it, but
browser-rendered discovery finds it. Proves the headless-browser harness.
"""
import http.server
import os

PORT = int(os.environ.get("PORT", "8080"))

HOME = b"""<!doctype html><html><body>
<h1>spa</h1>
<div id="app"></div>
<script>
  var f = document.createElement('form');
  f.setAttribute('action', '/register');
  f.setAttribute('method', 'post');
  var u = document.createElement('input'); u.setAttribute('name', 'username'); f.appendChild(u);
  var p = document.createElement('input');
  p.setAttribute('name', 'password'); p.setAttribute('type', 'password'); f.appendChild(p);
  document.getElementById('app').appendChild(f);
</script>
</body></html>"""


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        body, code = (HOME, 200) if self.path == "/" else (b"not found", 404)
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    http.server.HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
