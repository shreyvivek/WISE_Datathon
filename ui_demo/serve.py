"""Serve the SecondLook UI locally.
    python3 ui_demo/serve.py                         -> http://localhost:8080  (bundled demo data)
    python3 ui_demo/serve.py --api http://localhost:18000   -> same page, API calls proxied to the LinuxONE tunnel (LIVE)
Optional: --port 8080, --token <AUDIT_TOKEN> (added to proxied requests for the demographic endpoints)."""
import argparse, http.server, os, urllib.request, urllib.error, webbrowser
ap = argparse.ArgumentParser(); ap.add_argument("--port", type=int, default=8080); ap.add_argument("--api", default=""); ap.add_argument("--token", default="")
ap.add_argument("pos_port", nargs="?", type=int)  # backwards compatible: serve.py 8080
a = ap.parse_args(); port = a.pos_port or a.port; API = a.api.rstrip("/"); TOKEN = a.token
os.chdir(os.path.dirname(os.path.abspath(__file__)))
API_PREFIXES = ("/health", "/metrics", "/summary", "/lenders", "/review-queue", "/application/", "/analyse-application", "/generate-review-note",
                "/fairness-report", "/model-sensitivity", "/context/", "/questions", "/ask", "/review-decision", "/review-log", "/evaluation")

class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *x): pass
    def end_headers(self): self.send_header("Cache-Control", "no-store"); super().end_headers()
    def _is_api(self): return API and self.path.split("?")[0].startswith(API_PREFIXES)
    def _proxy(self):
        n = int(self.headers.get("content-length") or 0); body = self.rfile.read(n) if n else None
        hdr = {"content-type": self.headers.get("content-type", "application/json")}
        tok = self.headers.get("x-audit-token") or TOKEN
        if tok: hdr["x-audit-token"] = tok
        req = urllib.request.Request(API + self.path, data=body, headers=hdr, method=self.command)
        try:
            with urllib.request.urlopen(req, timeout=180) as r: code, data, ms = r.status, r.read(), r.headers.get("x-process-ms")
        except urllib.error.HTTPError as e: code, data, ms = e.code, e.read(), None
        except Exception as e: code, data, ms = 502, str(e).encode(), None
        self.send_response(code); self.send_header("content-type", "application/json")
        if ms: self.send_header("x-process-ms", ms)
        self.send_header("content-length", str(len(data))); self.end_headers(); self.wfile.write(data)
    def do_GET(self): self._proxy() if self._is_api() else super().do_GET()
    def do_POST(self): self._proxy() if self._is_api() else self.send_error(405)

print(f"SecondLook UI  http://localhost:{port}   " + (f"(LIVE: proxying API calls to {API})" if API else "(bundled demo data)") + "   Ctrl-C to stop")
webbrowser.open(f"http://localhost:{port}")
http.server.ThreadingHTTPServer(("", port), H).serve_forever()
