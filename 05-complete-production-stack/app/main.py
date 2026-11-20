"""
Production-grade OpenShift Microservice.
Demonstrates:
- ConfigMap injection via environment and file volume mounts
- Secret injection (safely masked in output)
- Liveness (/healthz), Readiness (/readyz)
- Prometheus-compatible metrics endpoint (/metrics)
"""

import json
import os
import sys
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = int(os.environ.get("PORT", 8080))
START_TIME = time.time()
REQUEST_COUNT = 0


def get_config_file_data():
    config_file = os.environ.get("CONFIG_FILE_PATH", "/etc/config/app-config.json")
    if os.path.exists(config_file):
        try:
            with open(config_file, "r") as f:
                return json.load(f)
        except Exception as e:
            return {"error": f"Failed to read {config_file}: {str(e)}"}
    return {"status": "default_in_memory_config", "path": config_file}


def mask_secret(value):
    if not value:
        return "<not set>"
    if len(value) <= 4:
        return "****"
    return value[:2] + "****" + value[-2:]


class ProductionHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global REQUEST_COUNT
        REQUEST_COUNT += 1

        if self.path in ("/", ""):
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()

            payload = {
                "service": "openshift-production-stack",
                "status": "HEALTHY",
                "uptime_seconds": round(time.time() - START_TIME, 2),
                "configmap_data": {
                    "environment": os.environ.get("APP_ENV", "production"),
                    "log_level": os.environ.get("LOG_LEVEL", "INFO"),
                    "feature_analytics": os.environ.get("FEATURE_ANALYTICS", "false"),
                    "file_mounted_config": get_config_file_data(),
                },
                "secret_data": {
                    "database_user": os.environ.get("DB_USER", "db_admin"),
                    "database_password": mask_secret(os.environ.get("DB_PASSWORD", "")),
                    "api_key": mask_secret(os.environ.get("API_KEY", "")),
                },
                "security_context": {
                    "uid": os.getuid() if hasattr(os, "getuid") else "N/A",
                    "gid": os.getgid() if hasattr(os, "getgid") else "N/A",
                    "non_root_verified": os.getuid() != 0 if hasattr(os, "getuid") else True,
                },
            }
            self.wfile.write(json.dumps(payload, indent=2).encode("utf-8"))

        elif self.path == "/healthz":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ALIVE"}).encode("utf-8"))

        elif self.path == "/readyz":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "READY"}).encode("utf-8"))

        elif self.path == "/metrics":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
            self.end_headers()
            uptime = time.time() - START_TIME
            metrics = (
                f"# HELP app_http_requests_total Total number of HTTP requests\n"
                f"# TYPE app_http_requests_total counter\n"
                f'app_http_requests_total{{handler="all"}} {REQUEST_COUNT}\n\n'
                f"# HELP app_uptime_seconds Total application uptime in seconds\n"
                f"# TYPE app_uptime_seconds gauge\n"
                f"app_uptime_seconds {uptime:.2f}\n"
            )
            self.wfile.write(metrics.encode("utf-8"))

        else:
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode("utf-8"))

    def log_message(self, format, *args):
        # Structured log output
        sys.stderr.write(f'{{"time": "{time.time()}", "client": "{self.client_address[0]}", "log": "{format % args}"}}\n')


def main():
    print(f"Production service booting on 0.0.0.0:{PORT}...")
    server = HTTPServer(("0.0.0.0", PORT), ProductionHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
