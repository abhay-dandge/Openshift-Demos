# OpenShift Security Context Constraints (SCC) & Arbitrary UID Guidelines

One of Red Hat OpenShift's strongest enterprise features is **Security Context Constraints (SCC)**. SCCs control the actions that a pod can perform and what it has the ability to access.

---

## 1. The Core OpenShift Security Model: Why Dockerfiles Fail

In standard Docker / vanilla Kubernetes tutorials, containers often run as `root` (UID `0`) or a fixed user (e.g. `USER 1000`).
In OpenShift, by default under the **`restricted-v2`** or **`restricted`** SCC:

1. **Containers CANNOT run as root (UID 0).**
2. **OpenShift assigns an arbitrary random UID per project/namespace** (e.g. `1000650000` to `1000659999`).
3. **The GID (Group ID) is always `0` (`root` group).**
4. **Containers CANNOT bind to ports lower than 1024** (such as port 80 or 443).

```
   OpenShift Namespace Policy (e.g., openshift.io/sa.scc.uid-range: 1000650000/10000)
                                      │
                                      ▼
                        ┌───────────────────────────┐
                        │ Assigned Container UID:   │
                        │ UID = 1000650024          │
                        │ GID = 0 (root group)      │
                        └─────────────┬─────────────┘
                                      │
               ┌──────────────────────┴──────────────────────┐
               ▼                                             ▼
  ❌ FAILS IF:                                   ✅ SUCCEEDS IF:
  - Dockerfile runs as root (UID 0)              - Directory owned by GID 0 (root group)
  - Files owned by 1000:1000 without group write - chmod -R g=u /opt/app-root
  - Binds to port 80 or 443                      - Binds to port 8080 or 8443
```

---

## 2. The Golden Rule for S2I & Containerfiles in OpenShift

If an application writes to any directory (e.g., `/tmp`, `/opt/app-root/src`, SQLite database, upload folder, caches), that directory **MUST have Group 0 ownership and Group Write permissions (`g=u`)**:

```dockerfile
# 1. Base directory creation
ENV APP_ROOT=/opt/app-root
RUN mkdir -p ${APP_ROOT}/src

# 2. Assign root group ownership (GID 0) and replicate user permissions to group
RUN chown -R 1001:0 ${APP_ROOT} && \
    chmod -R g=u ${APP_ROOT}

# 3. Define non-privileged user (OpenShift will override UID, keeping GID 0)
USER 1001

# 4. Bind to non-privileged port (8080)
EXPOSE 8080
```

---

## 3. Recommended Pod `securityContext` Spec

In modern OpenShift 4 clusters, enforce zero-trust container security in your `Deployment` YAML:

```yaml
spec:
  template:
    spec:
      securityContext:
        runAsNonRoot: true
        seccompProfile:
          type: RuntimeDefault
      containers:
        - name: app
          image: ...
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: false
            capabilities:
              drop:
                - ALL
```

---

## 4. Understanding SCC Levels

| SCC Name | Privilege Level | Use Case |
| :--- | :--- | :--- |
| **`restricted-v2`** | Strictest (OCP 4.11+) | Default for all user workloads. Drops ALL capabilities, enables runtime default seccomp, arbitrary UID. |
| **`restricted`** | Strict (OCP 4.x legacy) | Drops most capabilities, arbitrary UID. |
| **`nonroot`** | Medium | Allows container to specify a fixed non-root UID (e.g. `USER 1001`). |
| **`anyuid`** | Loose | Allows container to run as `root` (UID 0). Requires cluster-admin grant. |
| **`privileged`** | Unrestricted | Full host access (CNI plugins, storage drivers, node monitoring). |

> [!WARNING]
> Never grant `anyuid` or `privileged` to standard application workloads. Build your images to support arbitrary UIDs with Group 0 permissions instead.
