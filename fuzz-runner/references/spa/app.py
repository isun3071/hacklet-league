"""SPA reference (stdlib only). Every form is built by client-side JS, so none appear in the static
HTML source — a static crawl misses them, browser-rendered discovery finds them. Exercises the
client-rendered form surfaces the harness has to handle:
  (1) a <form> on the ENTRY page          -> rendering "/" finds it
  (2) a <form> on a SUB-route (/login)    -> only MULTI-route rendering reaches it
"""
import http.server
import os

PORT = int(os.environ.get("PORT", "8080"))

# (1) entry page: JS-built <form action=/register> + a nav link so discovery finds the sub-route
HOME = b"""<!doctype html><html><body>
<h1>spa</h1>
<nav><a href="/login">login</a></nav>
<div id="app"></div>
<script>
  var f = document.createElement('form');
  f.setAttribute('action', '/register'); f.setAttribute('method', 'post');
  var u = document.createElement('input'); u.setAttribute('name', 'username'); f.appendChild(u);
  var p = document.createElement('input');
  p.setAttribute('name', 'password'); p.setAttribute('type', 'password'); f.appendChild(p);
  document.getElementById('app').appendChild(f);
</script>
</body></html>"""

# (2) sub-route: JS-built <form action=/session> — NOT on the entry page, so a single-"/" render misses it
LOGIN = b"""<!doctype html><html><body>
<h1>login</h1><div id="app"></div>
<script>
  var f = document.createElement('form');
  f.setAttribute('action', '/session'); f.setAttribute('method', 'post');
  var u = document.createElement('input'); u.setAttribute('name', 'username'); f.appendChild(u);
  var p = document.createElement('input');
  p.setAttribute('name', 'password'); p.setAttribute('type', 'password'); f.appendChild(p);
  document.getElementById('app').appendChild(f);
</script>
</body></html>"""

_ROUTES = {"/": HOME, "/login": LOGIN}


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        body = _ROUTES.get(self.path)
        code = 200 if body is not None else 404
        if body is None:
            body = b"not found"
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    http.server.HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
