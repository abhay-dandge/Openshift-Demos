"""
Production-grade OpenShift S2I Python Demo Application.
Works out-of-the-box with Red Hat UBI 8 / UBI 9 Python S2I builder images
(registry.access.redhat.com/ubi9/python-39 or ubi8/python-38).

Features:
- Dual execution: Runs standalone (python app.py) or under production WSGI (gunicorn)
- Health endpoints: /healthz (liveness), /readyz (readiness)
- System and OpenShift runtime diagnostics: /info
- OpenShift arbitrary UID compliance: Non-privileged port 8080 binding
"""

import json
import os
import platform
import sys
import time
from wsgiref.simple_server import make_server

START_TIME = time.time()
APP_NAME = os.environ.get("APP_NAME", "openshift-s2i-python-demo")
APP_VERSION = os.environ.get("APP_VERSION", "1.0.0")
PORT = int(os.environ.get("PORT", os.environ.get("LISTEN_PORT", 8080)))


def get_diagnostics():
    return {
        "app_name": APP_NAME,
        "version": APP_VERSION,
        "status": "UP",
        "uptime_seconds": round(time.time() - START_TIME, 2),
        "runtime": {
            "python_version": sys.version,
            "platform": platform.platform(),
            "pid": os.getpid(),
            "uid": os.getuid() if hasattr(os, "getuid") else "N/A",
            "gid": os.getgid() if hasattr(os, "getgid") else "N/A",
        },
        "openshift_environment": {
            "pod_name": os.environ.get("HOSTNAME", "unknown-pod"),
            "pod_namespace": os.environ.get("OPENSHIFT_BUILD_NAMESPACE", os.environ.get("POD_NAMESPACE", "local")),
            "build_name": os.environ.get("OPENSHIFT_BUILD_NAME", "local-build"),
            "build_reference": os.environ.get("OPENSHIFT_BUILD_REFERENCE", "main"),
            "app_file": os.environ.get("APP_FILE", "app.py"),
        },
    }


def application(environ, start_response):
    path = environ.get("PATH_INFO", "/")

    if path == "/" or path == "":
        status = "200 OK"
        headers = [("Content-Type", "application/json; charset=utf-8")]
        start_response(status, headers)
        payload = {
            "message": "Welcome to OpenShift Source-to-Image (S2I) Python Demo!",
            "details": get_diagnostics(),
            "endpoints": [
                {"path": "/", "description": "Application root and diagnostics"},
                {"path": "/healthz", "description": "Liveness probe endpoint"},
                {"path": "/readyz", "description": "Readiness probe endpoint"},
                {"path": "/info", "description": "Detailed runtime and environment metadata"},
            ],
        }
        return [json.dumps(payload, indent=2).encode("utf-8")]

    elif path == "/healthz":
        status = "200 OK"
        headers = [("Content-Type", "application/json; charset=utf-8")]
        start_response(status, headers)
        return [json.dumps({"status": "ALIVE", "timestamp": time.time()}).encode("utf-8")]

    elif path == "/readyz":
        status = "200 OK"
        headers = [("Content-Type", "application/json; charset=utf-8")]
        start_response(status, headers)
        return [json.dumps({"status": "READY", "timestamp": time.time()}).encode("utf-8")]

    elif path == "/info":
        status = "200 OK"
        headers = [("Content-Type", "application/json; charset=utf-8")]
        start_response(status, headers)
        return [json.dumps(get_diagnostics(), indent=2).encode("utf-8")]

    else:
        status = "404 Not Found"
        headers = [("Content-Type", "application/json; charset=utf-8")]
        start_response(status, headers)
        return [json.dumps({"error": "Not Found", "path": path}).encode("utf-8")]


# WSGI callable entrypoint for Gunicorn / S2I runner
app = application

if __name__ == "__main__":
    print(f"Starting OpenShift S2I Python Demo on 0.0.0.0:{PORT} (UID: {os.getuid() if hasattr(os, 'getuid') else 'N/A'})...")
    httpd = make_server("0.0.0.0", PORT, application)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down gracefully.")
