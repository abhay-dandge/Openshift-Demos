#!/usr/bin/env bash
# ==============================================================================
# OpenShift Cluster Automated Deployment Script
# Deploys all demos to an active Red Hat OpenShift cluster
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

PROJECT_NAME="${1:-openshift-demos}"

echo "======================================================================"
echo " Deploying OpenShift Demos to Cluster Project: ${PROJECT_NAME}"
echo "======================================================================"

if ! command -v oc &> /dev/null; then
  echo "Error: 'oc' command not found. Please install the OpenShift CLI tool."
  exit 1
fi

CURRENT_USER=$(oc whoami 2>/dev/null || true)
if [[ -z "${CURRENT_USER}" ]]; then
  echo "Error: Not logged into an OpenShift cluster. Run 'oc login' first."
  exit 1
fi
echo "Authenticated as: ${CURRENT_USER}"

# 1. Project setup
echo "---> Ensuring project '${PROJECT_NAME}' exists..."
oc new-project "${PROJECT_NAME}" 2>/dev/null || oc project "${PROJECT_NAME}"

# 2. Deploy Demo 1: Python S2I App
echo -e "\n---> [1/4] Deploying Demo 1: Python S2I Application..."
oc apply -f "${REPO_ROOT}/01-s2i-python-app/k8s/"
oc start-build s2i-python-demo --from-dir="${REPO_ROOT}/01-s2i-python-app" --follow

# 3. Deploy Demo 2: Node.js S2I App
echo -e "\n---> [2/4] Deploying Demo 2: Node.js S2I Application..."
oc apply -f "${REPO_ROOT}/02-s2i-nodejs-app/k8s/"
oc start-build s2i-nodejs-demo --from-dir="${REPO_ROOT}/02-s2i-nodejs-app" --follow

# 4. Deploy Demo 3: Custom S2I Builder & Sample App
echo -e "\n---> [3/4] Deploying Demo 3: Custom S2I Builder Image..."
oc apply -f "${REPO_ROOT}/03-custom-s2i-builder/k8s/builder-imagestream.yaml"
oc apply -f "${REPO_ROOT}/03-custom-s2i-builder/k8s/builder-buildconfig.yaml"
oc start-build custom-s2i-builder --from-dir="${REPO_ROOT}/03-custom-s2i-builder" --follow

echo "---> Deploying sample app using the custom builder..."
oc apply -f "${REPO_ROOT}/03-custom-s2i-builder/k8s/app-buildconfig.yaml"
oc start-build custom-s2i-sample-app --from-dir="${REPO_ROOT}/03-custom-s2i-builder/sample-app" --follow

# 5. Deploy Demo 5: Complete Production Stack
echo -e "\n---> [4/4] Deploying Demo 5: Complete Production Stack..."
oc apply -k "${REPO_ROOT}/05-complete-production-stack"
oc start-build production-stack --from-dir="${REPO_ROOT}/05-complete-production-stack/app" --follow

# Summary of active routes
echo -e "\n======================================================================"
echo " All Demos Deployed Successfully! Active OpenShift Routes:"
echo "======================================================================"
oc get routes -n "${PROJECT_NAME}"
