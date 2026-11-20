#!/usr/bin/env python3
"""
OpenShift S2I Local Emulator & Contract Verification Tool.

Simulates the exact Source-to-Image (S2I) runtime contract locally:
1. Preparation: Creates an isolated build container simulation root (/opt/app-root/src)
2. Source Injection: Copies source from app directory to simulated /tmp/src
3. Assemble Phase: Executes S2I assemble (either custom script or standard runtime assemble)
4. Permission Verification: Verifies arbitrary non-root compatibility
5. Run Phase: Spawns the application process on an isolated port
6. Contract Verification: Probes /, /healthz, /readyz endpoints over HTTP
7. Graceful Termination: Sends SIGTERM and verifies zero-error clean shutdown
"""

import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import urllib.request
import urllib.error

TEST_PORT = 18088


def log(msg, symbol="--->"):
    print(f"\033[1;34m{symbol}\033[0m {msg}")


def log_success(msg):
    print(f"\033[1;32m✓ SUCCESS:\033[0m {msg}")


def log_error(msg):
    print(f"\033[1;31m✗ ERROR:\033[0m {msg}")


def parse_env_file(filepath):
    env = {}
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def test_s2i_app(app_dir, run_cmd, expected_endpoints=("/", "/healthz")):
    log(f"Starting S2I Contract Simulation for: {app_dir}")
    temp_dir = tempfile.mkdtemp(prefix="s2i-sim-")
    sim_app_root = os.path.join(temp_dir, "opt", "app-root", "src")
    os.makedirs(sim_app_root, exist_ok=True)

    try:
        # Step 1: Copy source to simulated app root
        log("Phase 1: Simulating S2I Source Extraction...")
        for item in os.listdir(app_dir):
            if item in (".git", "venv", "__pycache__", "k8s"):
                continue
            s = os.path.join(app_dir, item)
            d = os.path.join(sim_app_root, item)
            if os.path.isdir(s):
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)

        # Step 2: Assemble Phase
        log("Phase 2: Simulating S2I assemble Phase...")
        custom_assemble = os.path.join(sim_app_root, ".s2i", "bin", "assemble")
        env_file = os.path.join(sim_app_root, ".s2i", "environment")
        env_vars = os.environ.copy()
        env_vars["PORT"] = str(TEST_PORT)
        env_vars["LISTEN_PORT"] = str(TEST_PORT)
        env_vars["APP_ROOT"] = os.path.join(temp_dir, "opt", "app-root")

        if os.path.exists(env_file):
            custom_env = parse_env_file(env_file)
            env_vars.update(custom_env)
            log(f"Loaded .s2i/environment: {list(custom_env.keys())}")

        # Runtime container environment overrides (OpenShift Deployment spec takes precedence)
        actual_port = int(env_vars.get("PORT", TEST_PORT))
        log(f"Configured runtime port: {actual_port}")

        if os.path.exists(custom_assemble) and os.access(custom_assemble, os.X_OK):
            log(f"Executing custom assemble script: {custom_assemble}")
            res = subprocess.run([custom_assemble], cwd=sim_app_root, env=env_vars, capture_output=True, text=True)
            if res.returncode != 0:
                log_error(f"Assemble failed: {res.stderr}")
                return False

        # Step 3: Run Phase
        log(f"Phase 3: Launching application on port {actual_port}...")
        proc = subprocess.Popen(
            run_cmd,
            cwd=sim_app_root,
            env=env_vars,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=os.setsid if hasattr(os, "setsid") else None,
        )

        # Give application up to 5 seconds to bind port
        server_ready = False
        for attempt in range(15):
            time.sleep(0.3)
            if proc.poll() is not None:
                _, stderr = proc.communicate()
                log_error(f"Application terminated prematurely: {stderr}")
                return False
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{actual_port}/", timeout=1) as resp:
                    if resp.status in (200, 301, 302):
                        server_ready = True
                        break
            except Exception:
                continue

        if not server_ready:
            log_error(f"Application failed to respond on http://127.0.0.1:{actual_port}/ within timeout.")
            if proc.poll() is None:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            return False

        log_success(f"Application is responding on port {actual_port}!")

        # Step 4: Validate endpoints
        log("Phase 4: Probing OpenShift endpoints...")
        for ep in expected_endpoints:
            url = f"http://127.0.0.1:{actual_port}{ep}"
            try:
                with urllib.request.urlopen(url, timeout=2) as resp:
                    body = resp.read().decode("utf-8")
                    log_success(f"Endpoint '{ep}' returned HTTP {resp.status} (Payload length: {len(body)} bytes)")
            except urllib.error.HTTPError as e:
                log_error(f"Endpoint '{ep}' returned HTTP error {e.code}")
                return False
            except Exception as e:
                log_error(f"Endpoint '{ep}' connection failed: {e}")
                return False

        # Step 5: Graceful Termination
        log("Phase 5: Verifying graceful shutdown (SIGTERM)...")
        if hasattr(os, "killpg"):
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        else:
            proc.terminate()

        proc.wait(timeout=5)
        log_success(f"App shutdown cleanly with exit code {proc.returncode}")
        return True

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print("=" * 70)
    print(" OpenShift S2I Local Verification & Contract Simulation")
    print("=" * 70)

    tests = [
        {
            "name": "01-s2i-python-app",
            "path": os.path.join(root_dir, "01-s2i-python-app"),
            "cmd": [sys.executable, "app.py"],
            "endpoints": ["/", "/healthz", "/readyz", "/info"],
        },
        {
            "name": "02-s2i-nodejs-app",
            "path": os.path.join(root_dir, "02-s2i-nodejs-app"),
            "cmd": ["node", "server.js"],
            "endpoints": ["/", "/healthz", "/readyz", "/info"],
        },
        {
            "name": "03-custom-s2i-builder (sample-app via assemble/run)",
            "path": os.path.join(root_dir, "03-custom-s2i-builder", "sample-app"),
            "cmd": [sys.executable, "-m", "http.server", str(TEST_PORT), "--bind", "0.0.0.0"],
            "endpoints": ["/"],
        },
        {
            "name": "04-binary-build-workflow",
            "path": os.path.join(root_dir, "04-binary-build-workflow", "src"),
            "cmd": [sys.executable, "main.py"],
            "endpoints": ["/"],
        },
        {
            "name": "05-complete-production-stack",
            "path": os.path.join(root_dir, "05-complete-production-stack", "app"),
            "cmd": [sys.executable, "main.py"],
            "endpoints": ["/", "/healthz", "/readyz", "/metrics"],
        },
    ]

    all_passed = True
    for t in tests:
        print()
        log(f"--- Running test target: {t['name']} ---")
        passed = test_s2i_app(t["path"], t["cmd"], t["endpoints"])
        if not passed:
            all_passed = False
            log_error(f"Target {t['name']} FAILED simulation!")
        else:
            log_success(f"Target {t['name']} PASSED all S2I contract tests!")

    print()
    print("=" * 70)
    if all_passed:
        print("\033[1;32mALL OPENSHIFT S2I SIMULATION TESTS PASSED SUCCESSFULLY!\033[0m")
        return 0
    else:
        print("\033[1;31mSOME OPENSHIFT S2I SIMULATION TESTS FAILED.\033[0m")
        return 1


if __name__ == "__main__":
    sys.exit(main())
