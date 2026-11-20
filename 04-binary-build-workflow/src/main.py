"""
High-performance inner-loop Python microservice for OpenShift Binary Builds.
"""

import json
import os
import sys
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = int(os.environ.get("PORT", 8080))
BUILD_TIMESTAMP = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())


class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()

        payload = {
            "service": "openshift-binary-build-demo",
            "message": "Instant inner-loop deployment via OpenShift Binary Build!",
            "build_timestamp": BUILD_TIMESTAMP,
            "path": self.path,
            "environment": {
                "user_id": os.getuid() if hasattr(os, "getuid") else "N/A",
                "hostname": os.environ.get("HOSTNAME", "local"),
                "python_version": sys.version.split()[0],
            },
        }
        self.wfile.write(json.dumps(payload, indent=2).encode("utf-8"))

    def log_message(self, format, *args):
        # Override to log cleanly
        sys.stderr.write(f"[{time.strftime('%X')}] {format % args}\n")


def run():
    server_address = ("0.0.0.0", PORT)
    httpd = HTTPServer(server_address, SimpleHandler)
    print(f"Binary build application listening on port {PORT}...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    run()
