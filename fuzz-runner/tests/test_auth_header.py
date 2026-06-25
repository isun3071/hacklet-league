"""--header auth injection: a supplied header (Cookie / Authorization) reaches the target so the
runner crawls and probes the authenticated surface behind a session/SSO wall, not just the login page.
"""
import http.server
import threading

from hacklet_runner.discovery import discover


class _Gated(http.server.BaseHTTPRequestHandler):
    """Serves the authed surface only when the right bearer token is present; otherwise a 401 wall."""
    def log_message(self, *a):
        pass

    def do_GET(self):
        if self.headers.get("Authorization") != "Bearer test-token":
            self.send_response(401)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        body = b'<a href="/vip">vip</a>' if self.path == "/" else b"vip area"
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def _serve():
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Gated)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def test_auth_header_unlocks_authenticated_surface():
    srv = _serve()
    url = f"http://127.0.0.1:{srv.server_address[1]}"
    try:
        anon = discover(url)                                              # no header -> only the 401 wall
        authed = discover(url, headers={"Authorization": "Bearer test-token"})
        assert "/vip" not in anon.routes
        assert "/vip" in authed.routes  # the header reached the target and unlocked the authed crawl
    finally:
        srv.shutdown()
