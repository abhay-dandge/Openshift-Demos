#!/usr/bin/env bash
# ==============================================================================
# OpenShift Cluster Cleanup Script
# Safely removes demo resources or deletes the demo project
# ==============================================================================
set -euo pipefail

PROJECT_NAME="${1:-openshift-demos}"

echo "======================================================================"
echo " OpenShift Demos Cleanup"
echo " Target Project: ${PROJECT_NAME}"
echo "======================================================================"

if ! command -v oc &> /dev/null; then
  echo "Error: 'oc' command not found."
  exit 1
fi

read -p "Are you sure you want to delete the entire '${PROJECT_NAME}' project? (y/N): " -r CONFIRM
if [[ "${CONFIRM}" =~ ^[Yy]$ ]]; then
  echo "---> Deleting project '${PROJECT_NAME}'..."
  oc delete project "${PROJECT_NAME}" --wait=false
  echo "Project deletion initiated."
else
  echo "---> Cleaning up demo resources in '${PROJECT_NAME}'..."
  oc delete all,routes,configmaps,secrets -l app.kubernetes.io/part-of=openshift-demos -n "${PROJECT_NAME}" || true
  echo "Cleaned up labeled resources."
fi
