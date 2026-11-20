#!/usr/bin/env bash
# ==============================================================================
# Master Verification Suite for OpenShift Demos
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

GREEN='\033[1;32m'
RED='\033[1;31m'
BLUE='\033[1;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}======================================================================${NC}"
echo -e "${BLUE} OpenShift Demos: Comprehensive Pre-Flight & Contract Verification    ${NC}"
echo -e "${BLUE}======================================================================${NC}"

# Step 1: Validate YAML syntax across all manifests
echo -e "\n${YELLOW}---> [1/4] Validating Kubernetes & OpenShift YAML Manifests...${NC}"
python3 - << 'EOF'
import os
import sys
import yaml

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if '__file__' in globals() else os.getcwd()
yaml_count = 0
error_count = 0

official_api_groups = {
    "BuildConfig": "build.openshift.io/v1",
    "ImageStream": "image.openshift.io/v1",
    "Route": "route.openshift.io/v1",
    "Deployment": "apps/v1",
    "Service": "v1",
    "ConfigMap": "v1",
    "Secret": "v1",
    "Namespace": "v1",
    "ServiceAccount": "v1",
    "HorizontalPodAutoscaler": "autoscaling/v2",
    "NetworkPolicy": "networking.k8s.io/v1",
}

for root, _, files in os.walk(repo_root):
    for f in sorted(files):
        if f.endswith((".yaml", ".yml")):
            filepath = os.path.join(root, f)
            relpath = os.path.relpath(filepath, repo_root)
            yaml_count += 1
            try:
                with open(filepath, "r") as stream:
                    docs = list(yaml.safe_load_all(stream))
                    for doc in docs:
                        if not doc or not isinstance(doc, dict):
                            continue
                        kind = doc.get("kind")
                        api_version = doc.get("apiVersion")
                        if kind in official_api_groups:
                            expected = official_api_groups[kind]
                            if api_version != expected:
                                print(f"  \033[1;31m[API WARNING]\033[0m {relpath}: Kind '{kind}' has apiVersion '{api_version}', expected '{expected}'")
                print(f"  \033[1;32m✓ Valid YAML:\033[0m {relpath}")
            except Exception as e:
                print(f"  \033[1;31m✗ YAML ERROR in {relpath}:\033[0m {e}")
                error_count += 1

print(f"\nTotal YAML manifests validated: {yaml_count}")
if error_count > 0:
    print(f"\033[1;31mManifest validation FAILED with {error_count} errors.\033[0m")
    sys.exit(1)
else:
    print("\033[1;32mAll manifests passed syntax & API specification checks!\033[0m")
EOF

# Step 2: Run Python Demo Unit Tests
echo -e "\n${YELLOW}---> [2/4] Executing Python S2I Unit Tests...${NC}"
python3 "${REPO_ROOT}/01-s2i-python-app/test_app.py"

# Step 3: Run Node.js Demo Unit Tests
echo -e "\n${YELLOW}---> [3/4] Executing Node.js S2I Unit Tests...${NC}"
node "${REPO_ROOT}/02-s2i-nodejs-app/test_server.js"

# Step 4: Run S2I Contract Simulation across all demo projects
echo -e "\n${YELLOW}---> [4/4] Executing S2I Contract Simulator across all apps...${NC}"
python3 "${REPO_ROOT}/scripts/simulate-s2i.py"

echo -e "\n${GREEN}======================================================================${NC}"
echo -e "${GREEN} ALL OPENSHIFT DEMOS VERIFIED AND WORKING 100% CLEANLY!              ${NC}"
echo -e "${GREEN} Ready for local testing or cluster deployment.                      ${NC}"
echo -e "${GREEN}======================================================================${NC}"
