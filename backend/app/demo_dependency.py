"""Isolated synthetic dependency; no application/database administration capabilities."""
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Lock

lock = Lock()
faulted = False

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_args):
        pass

    def reply(self, status, data):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/live":
            return self.reply(200, {"status": "alive"})
        if self.path != "/health":
            return self.reply(404, {"detail": "Not found"})
        with lock:
            return self.reply(503 if faulted else 200, {"status": "faulted" if faulted else "healthy"})

    def do_POST(self):
        global faulted
        with lock:
            if self.path == "/work":
                return self.reply(503 if faulted else 200, {"status": "failed" if faulted else "completed"})
            if self.path not in ("/fault", "/reset"):
                return self.reply(404, {"detail": "Not found"})
            if self.headers.get("X-Demo-Control") != os.getenv("DEMO_CONTROL_TOKEN", "synthetic-local-demo"):
                return self.reply(403, {"detail": "Control denied"})
            faulted = self.path == "/fault"
            return self.reply(200, {"status": "faulted" if faulted else "healthy"})

if __name__ == "__main__":
    # Isolated Compose network service; no host port published.
    ThreadingHTTPServer(("0.0.0.0", int(os.getenv("PORT", "9000"))), Handler).serve_forever()  # nosec B104
