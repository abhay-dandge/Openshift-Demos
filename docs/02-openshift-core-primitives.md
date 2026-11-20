# OpenShift Core Primitives & Developer Concepts

This document details the core API objects used across Red Hat OpenShift Container Platform 4.x.

---

## 1. BuildConfig (`build.openshift.io/v1`)

A `BuildConfig` describes a single build definition and the triggers for new builds:

```yaml
apiVersion: build.openshift.io/v1
kind: BuildConfig
metadata:
  name: sample-app
spec:
  runPolicy: Serial # Or Parallel
  source:
    type: Git # Or Binary, Dockerfile, ConfigMap, Secret
    git:
      uri: https://github.com/redhat-developer/s2i-python-container.git
      ref: master
  strategy:
    type: Source # S2I Source strategy
    sourceStrategy:
      from:
        kind: ImageStreamTag
        name: python:3.9-ubi9
        namespace: openshift
  output:
    to:
      kind: ImageStreamTag
      name: sample-app:latest
  triggers:
    - type: ConfigChange # Trigger build when BuildConfig is modified
    - type: ImageChange  # Trigger build when builder image is updated (CVE patches!)
    - type: GitHub       # Trigger build on git commit push
      github:
        secretReference:
          name: github-webhook-secret
```

---

## 2. ImageStream (`image.openshift.io/v1`)

An `ImageStream` abstracts container images. Rather than pods binding directly to remote container registries (e.g. `quay.io` or `docker.io`), OpenShift applications reference ImageStreams:

- **Decoupled references:** Pods reference `sample-app:latest`. If the underlying image digest changes, OpenShift notifies the Deployment controller.
- **CVE automatic rolling updates:** When Red Hat publishes a security patch to `python:3.9-ubi9`, OpenShift detects the new digest and triggers automatic rebuilds and deployments of all downstream apps!

---

## 3. Route (`route.openshift.io/v1`)

A `Route` exposes an internal Kubernetes `Service` to the outside world via OpenShift's HAProxy-based Ingress Controller.

### TLS Termination Modes:

1. **Edge Termination:** TLS is terminated at the OpenShift Router. Traffic from router to pod is unencrypted HTTP (ideal for low-latency internal networks).
2. **Passthrough Termination:** TLS traffic passes directly to the pod untouched. Pod must possess TLS certificates.
3. **Re-encryption:** TLS terminates at the router with public certs, then re-encrypts using internal CA certs to the pod.

```yaml
apiVersion: route.openshift.io/v1
kind: Route
metadata:
  name: sample-app
  annotations:
    haproxy.router.openshift.io/hsts_header: "max-age=31536000;includeSubDomains;preload"
spec:
  to:
    kind: Service
    name: sample-app
  port:
    targetPort: http
  tls:
    termination: edge
    insecureEdgeTerminationPolicy: Redirect # Enforces HTTPS redirect
```

---

## 4. Deployment vs. DeploymentConfig

| Feature | `apps/v1` `Deployment` | `apps.openshift.io/v1` `DeploymentConfig` |
| :--- | :--- | :--- |
| **Standard** | Kubernetes standard (OCP 4.x default) | OpenShift legacy (pre-Kubernetes 1.2) |
| **Tooling** | Native Helm, Kustomize, ArgoCD | `oc` CLI specific |
| **Recommendation** | **Recommended for all new workloads** | Maintenance mode |
| **Image Trigger** | Via OpenShift annotations or GitOps | Built-in `imageChangeParams` |

---

## 5. ConfigMaps & Secrets

- **ConfigMaps:** Plaintext key-value pairs or mounted configuration files (e.g. `nginx.conf`, `settings.json`).
- **Secrets:** Base64-encoded sensitive keys, tokens, or credentials mounted as env vars or read-only volume files.
