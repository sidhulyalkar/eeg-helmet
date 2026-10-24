"""Local-only, read-only synthetic demo HTTP service using Python stdlib."""
from __future__ import annotations
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from importlib.resources import files
import json
from .models import Parameters, SCENARIOS
from .analysis import comparison

MAX_REQUEST_BYTES = 8192
ASSETS = {"/": ("index.html", "text/html; charset=utf-8"),
          "/index.html": ("index.html", "text/html; charset=utf-8"),
          "/app.css": ("app.css", "text/css; charset=utf-8"),
          "/app.js": ("app.js", "application/javascript; charset=utf-8")}


class Handler(BaseHTTPRequestHandler):
    server_version = "NeuroShieldDemo/0.2"

    def _respond(self, code, contents: bytes, content_type: str):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(contents)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(contents)

    def _json(self, code, payload):
        return self._respond(code, json.dumps(payload, allow_nan=False).encode("utf-8"), "application/json; charset=utf-8")

    def do_GET(self):
        if self.path == "/api/health":
            return self._json(200, {"ok": True, "mode": "synthetic_only", "clinical": False})
        if self.path == "/api/config":
            return self._json(200, {"scenarios": SCENARIOS, "baseline": Parameters().to_dict(),
                                    "suggested": Parameters.suggested().to_dict(),
                                    "data_policy": "No uploaded, identifiable, clinical or real subject data accepted."})
        asset = ASSETS.get(self.path)
        if not asset:
            return self._json(404, {"error": "not found"})
        name, mime = asset
        return self._respond(200, files("neuroshield").joinpath("web", name).read_bytes(), mime)

    def do_POST(self):
        if self.path not in ("/api/compare", "/api/qualify"):
            return self._json(404, {"error": "not found; no real-data ingestion endpoint"})
        try:
            raw_length = self.headers.get("Content-Length", "")
            if not raw_length.isdecimal():
                return self._json(411, {"error": "Content-Length required"})
            length = int(raw_length)
            if length > MAX_REQUEST_BYTES:
                return self._json(413, {"error": "Request too large"})
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict) or set(payload) - {"scenario", "parameters"}:
                raise ValueError("Expected scenario and parameters only")
            scenario = payload.get("scenario", "oblique")
            if not isinstance(scenario, str) or scenario not in SCENARIOS:
                raise ValueError("Invalid scenario")
            params = Parameters.from_payload(payload.get("parameters"))
            if self.path == "/api/qualify":
                from .qualification import qualify
                return self._json(200, qualify(scenario, params))
            return self._json(200, comparison(scenario, params))
        except (ValueError, TypeError, UnicodeError, json.JSONDecodeError) as exc:
            return self._json(400, {"error": str(exc)})


def serve(host="127.0.0.1", port=8765):
    if host not in ("127.0.0.1", "localhost", "::1"):
        raise ValueError("Demo service can only bind to loopback. No real-data security or authentication exists.")
    with ThreadingHTTPServer((host, port), Handler) as server:
        print(f"NeuroShield SYNTHETIC RESEARCH DEMO: http://{host}:{server.server_port}", flush=True)
        print("Not a medical device. No real subject data is accepted.", flush=True)
        server.serve_forever()
