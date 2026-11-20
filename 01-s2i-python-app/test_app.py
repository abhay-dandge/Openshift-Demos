"""
Unit tests for 01-s2i-python-app.
Can run locally or in a CI pipeline without external dependencies.
"""

import json
import unittest
from app import application, get_diagnostics


class TestPythonS2IApp(unittest.TestCase):

    def simulate_request(self, path="/"):
        environ = {
            "PATH_INFO": path,
            "REQUEST_METHOD": "GET",
        }
        response_headers = {}
        status_code = [None]

        def start_response(status, headers):
            status_code[0] = status
            for k, v in headers:
                response_headers[k] = v

        body_chunks = application(environ, start_response)
        body = b"".join(body_chunks).decode("utf-8")
        return status_code[0], response_headers, body

    def test_root_endpoint(self):
        status, headers, body = self.simulate_request("/")
        self.assertEqual(status, "200 OK")
        self.assertIn("application/json", headers["Content-Type"])
        data = json.loads(body)
        self.assertIn("message", data)
        self.assertEqual(data["details"]["status"], "UP")

    def test_healthz_endpoint(self):
        status, _, body = self.simulate_request("/healthz")
        self.assertEqual(status, "200 OK")
        data = json.loads(body)
        self.assertEqual(data["status"], "ALIVE")

    def test_readyz_endpoint(self):
        status, _, body = self.simulate_request("/readyz")
        self.assertEqual(status, "200 OK")
        data = json.loads(body)
        self.assertEqual(data["status"], "READY")

    def test_info_endpoint(self):
        status, _, body = self.simulate_request("/info")
        self.assertEqual(status, "200 OK")
        data = json.loads(body)
        self.assertIn("runtime", data)
        self.assertIn("openshift_environment", data)

    def test_404_endpoint(self):
        status, _, body = self.simulate_request("/non-existent")
        self.assertEqual(status, "404 Not Found")
        data = json.loads(body)
        self.assertIn("error", data)


if __name__ == "__main__":
    unittest.main()
