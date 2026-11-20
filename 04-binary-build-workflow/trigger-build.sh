#!/usr/bin/env bash
# ==============================================================================
# Fast Inner-Loop Binary Build Trigger Script
# ==============================================================================
set -euo pipefail

APP_NAME="binary-python-demo"
SRC_DIR="./src"

echo "======================================================================"
echo " Starting OpenShift Binary Build for: ${APP_NAME}"
echo " Streaming directory: ${SRC_DIR}"
echo "======================================================================"

if ! command -v oc &> /dev/null; then
  echo "Error: 'oc' CLI is not found in PATH. Please install or login to an OpenShift cluster."
  exit 1
fi

# Ensure manifests exist in cluster
echo "---> Ensuring OpenShift manifests are applied..."
oc apply -f k8s/complete-binary-pipeline.yaml

# Stream local directory into build pod
echo "---> Streaming local source directly to build pod..."
oc start-build "${APP_NAME}" --from-dir="${SRC_DIR}" --follow

# Wait for rolling deployment to finish
echo "---> Awaiting deployment rollout..."
oc rollout status "deployment/${APP_NAME}"

# Print Route endpoint
ROUTE_HOST=$(oc get route "${APP_NAME}" -o jsonpath='{.spec.host}' 2>/dev/null || true)
if [[ -n "${ROUTE_HOST}" ]]; then
  echo "======================================================================"
  echo " Deployment Successful! Live Route URL:"
  echo " https://${ROUTE_HOST}/"
  echo "======================================================================"
fi
