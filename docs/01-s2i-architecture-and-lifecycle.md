# OpenShift Source-to-Image (S2I) Architecture & Lifecycle Guide

Source-to-Image (S2I) is an open-source toolkit and container workflow designed by Red Hat for reproducible container image builds directly from source code without requiring a Dockerfile.

---

## 1. S2I Core Architecture

In traditional container workflows, developers write a `Dockerfile` specifying base operating systems, package installations, source copies, and entrypoints. This introduces security risks (unpatched base images, hardcoded credentials, root execution) and operational fragmentation.

S2I decouples **Application Code** from **Container Runtime Environment**:

```
Application Source Code                  Official S2I Builder
┌───────────────────────┐             ┌─────────────────────────┐
│ • Python (app.py)     │             │ • Red Hat UBI 9 Base    │
│ • Node.js (server.js) │             │ • Language Runtime      │
│ • Java (pom.xml)      │             │ • S2I Lifecycle Scripts │
└───────────┬───────────┘             └────────────┬────────────┘
            │                                      │
            └──────────────────┬───────────────────┘
                               ▼
               ┌───────────────────────────────┐
               │    S2I Build Engine / Pod     │
               │  Executes 'assemble' script   │
               └───────────────┬───────────────┘
                               ▼
               ┌───────────────────────────────┐
               │   Deployable Application      │
               │       Container Image         │
               └───────────────────────────────┘
```

---

## 2. The S2I Lifecycle Script Contract

Every S2I builder image contains four dedicated lifecycle scripts located in the directory declared by label `io.openshift.s2i.scripts-url` (typically `/usr/libexec/s2i` or `/usr/local/s2i`):

```
/usr/libexec/s2i/
  ├── assemble         # Compiles, restores caches, installs dependencies
  ├── run              # Container entrypoint starting the application
  ├── save-artifacts   # Exports cache archives for incremental builds
  └── usage            # Documentation and instructions
```

### Detailed Script Contract

### `assemble`
- **When triggered:** During `oc start-build` or `s2i build`.
- **Environment:**
  - Source code placed in `/tmp/src`.
  - Artifacts from prior builds placed in `/tmp/artifacts` (if incremental).
- **Duties:**
  1. Copies `/tmp/src` to the application destination (e.g. `/opt/app-root/src`).
  2. Restores dependency caches.
  3. Executes language-specific build tools (`pip install`, `npm install`, `mvn package`).
  4. Applies OpenShift permissions (`chmod -R g=u /opt/app-root`).

### `run`
- **When triggered:** When the application container boots inside an OpenShift pod.
- **Duties:**
  - Must execute the process in the foreground using `exec <cmd>` so OS signals (`SIGTERM`, `SIGINT`) are delivered directly to the application.
  - Must bind to a non-privileged port (`>= 1024`, default `8080`).

### `save-artifacts`
- **When triggered:** Before a new build starts during an incremental build (`--incremental`).
- **Duties:**
  - Streams a `tar` stream of cached dependency folders (`node_modules`, `.cache/pip`, `.m2/repository`) to `stdout`.
  - OpenShift preserves this tarball and feeds it to the subsequent build pod's `assemble` phase as `/tmp/artifacts`.

### `usage`
- **When triggered:** When the builder container is run directly without source code (`podman run <builder-image>`).
- **Duties:**
  - Prints usage guidelines and supported environment variables.

---

## 3. Customizing S2I Builds in Source Code

Developers can customize builder behavior without modifying the builder container image itself:

### 1. `.s2i/environment`
Place key-value pairs in `.s2i/environment` in the root of your application repository:
```bash
APP_FILE=app.py
APP_MODULE=app:application
PORT=8080
PIP_NO_CACHE_DIR=1
```

### 2. Custom `.s2i/bin/assemble` & `run` Overrides
If your application needs custom compilation or pre-flight setup, create `.s2i/bin/assemble` in your source repo. Official Red Hat builders detect this file and execute your custom assemble script instead of or in addition to the default logic.

---

## 4. Official Red Hat S2I Builder Catalog

Red Hat provides Universal Base Image (UBI) S2I builders through Red Hat Ecosystem Catalog:

| Language | Red Hat UBI Builder Image | OpenShift ImageStream Tag |
| :--- | :--- | :--- |
| **Python 3.9** | `registry.access.redhat.com/ubi9/python-39` | `python:3.9-ubi9` |
| **Python 3.11** | `registry.access.redhat.com/ubi9/python-311` | `python:3.11-ubi9` |
| **Node.js 18** | `registry.access.redhat.com/ubi9/nodejs-18` | `nodejs:18-ubi9` |
| **Node.js 20** | `registry.access.redhat.com/ubi9/nodejs-20` | `nodejs:20-ubi9` |
| **OpenJDK 17** | `registry.access.redhat.com/ubi9/openjdk-17` | `java:17` / `openjdk-17-ubi9` |
| **OpenJDK 21** | `registry.access.redhat.com/ubi9/openjdk-21` | `java:21` / `openjdk-21-ubi9` |
| **Go 1.20** | `registry.access.redhat.com/ubi9/go-toolset` | `golang:1.20-ubi9` |
| **Nginx (Static)**| `registry.access.redhat.com/ubi9/nginx-120` | `nginx:1.20-ubi9` |
