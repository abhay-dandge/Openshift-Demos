# Demo 5: Complete Enterprise OpenShift Production Stack

This demo showcases a full-featured, zero-trust enterprise deployment on Red Hat OpenShift Container Platform 4.x.

---

## 1. Architecture Highlights

| OpenShift Resource | Purpose |
| :--- | :--- |
| **`00-namespace.yaml`** | Dedicated project namespace with cluster monitoring enabled. |
| **`01-serviceaccount.yaml`** | Least-privilege ServiceAccount (`prod-app-sa`) mapped to OpenShift `restricted-v2` SCC. |
| **`02-configmap.yaml`** | Application configuration parameters and volume-mounted JSON config file. |
| **`03-secret.yaml`** | Sensitive credentials (database password, API keys) securely injected into the pod. |
| **`04-imagestream.yaml`** | Native OpenShift ImageStream tracking application container images. |
| **`05-buildconfig.yaml`** | S2I BuildConfig using official Red Hat `python:3.9-ubi9` with build resource quotas. |
| **`06-deployment.yaml`** | 2 replicas, rolling updates (`maxSurge: 25%`, `maxUnavailable: 0`), Liveness, Readiness, Startup probes, and `seccompProfile: RuntimeDefault`. |
| **`07-service.yaml`** | Internal `ClusterIP` service routing port 8080. |
| **`08-route.yaml`** | OpenShift HAProxy router Ingress with **Edge TLS Termination**, automatic HTTPS redirect, and HSTS security headers. |
| **`09-hpa.yaml`** | HorizontalPodAutoscaler scaling pods between 2 and 5 instances based on 75% target CPU. |
| **`10-networkpolicy.yaml`** | Restricts ingress to only the OpenShift router namespace and internal pod traffic. |

---

## 2. One-Command Declarative Deployment

Deploy the entire stack with Kustomize:

```bash
# 1. Apply all manifests in order via Kustomize
oc apply -k .

# 2. Trigger the S2I build
oc start-build production-stack --from-dir=app --follow

# 3. Wait for rolling rollout
oc rollout status deployment/production-stack -n openshift-demos

# 4. View route endpoint
ROUTE_URL=$(oc get route production-stack -n openshift-demos -o jsonpath='{.spec.host}')
echo "Production Application Live at: https://${ROUTE_URL}/"

# 5. Query endpoints
curl -k "https://${ROUTE_URL}/"
curl -k "https://${ROUTE_URL}/healthz"
curl -k "https://${ROUTE_URL}/readyz"
curl -k "https://${ROUTE_URL}/metrics"
```
