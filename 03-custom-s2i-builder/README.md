# Demo 3: Custom S2I Builder Image from Scratch

This demo demystifies OpenShift Source-to-Image by constructing a **complete Custom S2I Builder Image** from scratch using Red Hat Universal Base Image 9 (`ubi9-minimal`).

---

## 1. How S2I Works Under the Hood

The Source-to-Image (S2I) workflow replaces Dockerfiles for application developers. Instead of writing build steps in Dockerfiles, a **Builder Image** provides 4 contract scripts inside `/usr/libexec/s2i`:

```
┌─────────────────────────────────┐
│     S2I Builder Container       │
│  (Red Hat UBI9 Base Image)      │
│                                 │
│  /usr/libexec/s2i/              │
│    ├── assemble                 │ ── 1. Receives source from /tmp/src
│    ├── run                      │ ── 2. Installs dependencies & compiles
│    ├── save-artifacts           │ ── 3. Normalizes UID/GID (group 0)
│    └── usage                    │ ── 4. Executes entrypoint on port 8080
└─────────────────────────────────┘
```

### The S2I Script Contract

| Script | When Triggered | Responsibility |
| :--- | :--- | :--- |
| `assemble` | During `oc start-build` or `s2i build` | Copies source from `/tmp/src` to runtime directory, restores incremental caches, installs packages, and grants group 0 permissions. |
| `run` | When container starts in pod | Starts application in the foreground, forwarding OS signals. |
| `save-artifacts` | Incremental builds (`--incremental`) | Streams tar archive of cached assets to stdout. |
| `usage` | When builder image is run directly | Prints documentation and usage instructions. |

---

## 2. Red Hat OpenShift Security Architecture (Arbitrary UIDs)

A frequent cause of failure in poorly crafted custom builders is **UID assumption**:
In OpenShift, containers **never run as root** (unless granted the privileged SCC), and are assigned an arbitrary UID (e.g., `1000650000`) belonging to **Group ID `0` (root group)**.

To ensure your builder never fails:
1. All target directories must belong to group `0`: `chown -R 1001:0 /opt/app-root`
2. Group permissions must match user permissions: `chmod -R g=u /opt/app-root`
3. The container must bind to a non-privileged port (`>= 1024`), standard `8080`.

---

## 3. End-to-End Build & Run Walkthrough

### Step 1: Build the Custom Builder Image
```bash
# Apply builder ImageStream & BuildConfig
oc apply -f k8s/builder-imagestream.yaml
oc apply -f k8s/builder-buildconfig.yaml

# Build the builder image from this directory
oc start-build custom-s2i-builder --from-dir=. --follow
```

### Step 2: Use Your Custom Builder to Build an Application
```bash
# Apply application BuildConfig, Deployment, Service, and Route
oc apply -f k8s/app-buildconfig.yaml

# Build the sample app using your new custom builder!
oc start-build custom-s2i-sample-app --from-dir=sample-app --follow

# Verify deployment
oc rollout status deployment/custom-s2i-sample-app
oc get route custom-s2i-sample-app
```
