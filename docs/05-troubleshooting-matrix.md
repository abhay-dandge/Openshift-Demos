# OpenShift & S2I Troubleshooting Matrix

This guide provides diagnostic workflows and fixes for common failure modes encountered when deploying applications on Red Hat OpenShift Container Platform.

---

## 1. Quick Diagnostic Cheat Sheet

```bash
# 1. View overall project status and failed components
oc status

# 2. Inspect build pod logs in real time
oc logs -f bc/<buildconfig-name>
oc logs -f build/<build-name>

# 3. View application pod logs
oc logs deployment/<deployment-name> --all-containers=true --tail=100

# 4. View Kubernetes events for the project (order by time)
oc get events --sort-by='.metadata.creationTimestamp'

# 5. Describe pod to check reasons for CrashLoopBackOff or ErrImagePull
oc describe pod <pod-name>
```

---

## 2. Comprehensive Failure Matrix

### Issue 1: `Permission denied` on Startup (UID `1000650000`)
- **Symptom:** Application crashes immediately on startup. Logs show: `PermissionError: [Errno 13] Permission denied: '/opt/app-root/src/...'` or `EACCES: permission denied, open ...`
- **Root Cause:** Container image was built assuming fixed user `root` (UID 0) or user `1000`. OpenShift executes the container with an arbitrary non-root UID belonging to Group `0`.
- **Diagnosis:**
  ```bash
  oc describe pod <pod-name> | grep "Security Context"
  ```
- **Fix:** Ensure all target directories are owned by Group 0 and group write permissions are set (`g=u`):
  ```bash
  chown -R 1001:0 /opt/app-root && chmod -R g=u /opt/app-root
  ```

---

### Issue 2: Pod stuck in `CrashLoopBackOff` (Liveness / Readiness Probe Failure)
- **Symptom:** Pod starts, runs for 10-30 seconds, gets killed and restarted continuously.
- **Root Cause:**
  1. The application binds to `localhost` (`127.0.0.1`) instead of `0.0.0.0`, blocking kubelet probes from outside the container.
  2. The health check path (`/healthz` or `/readyz`) returns an HTTP 500 error or does not respond before `timeoutSeconds`.
  3. `initialDelaySeconds` is shorter than the application's boot duration.
- **Diagnosis:**
  ```bash
  oc describe pod <pod-name> | grep -A 5 "Liveness"
  oc logs <pod-name> --previous
  ```
- **Fix:**
  - Ensure the application listens on `0.0.0.0:8080`.
  - Increase `initialDelaySeconds: 15` and add a `startupProbe` if the app takes a long time to warm up.

---

### Issue 3: `ImagePullBackOff` / `ErrImagePull` on ImageStream
- **Symptom:** Deployment cannot pull the built container image.
- **Root Cause:**
  1. Build did not finish or failed.
  2. The Deployment references an image tag not present in the ImageStream.
  3. ImageStream `lookupPolicy.local` is `false`, requiring external registry authentication.
- **Diagnosis:**
  ```bash
  oc get is
  oc describe is <imagestream-name>
  ```
- **Fix:**
  - Verify build succeeded: `oc get builds`
  - In the ImageStream manifest, enable local lookup:
    ```yaml
    spec:
      lookupPolicy:
        local: true
    ```

---

### Issue 4: S2I Build Pod Error: `assemble exited with code 1`
- **Symptom:** `oc start-build` fails during build step.
- **Root Cause:**
  1. Dependency installation failure (e.g. invalid package version in `requirements.txt` or `package.json`).
  2. Builder container ran out of memory (OOMKilled).
  3. Network policy blocks egress from the build pod to external package repositories.
- **Diagnosis:**
  ```bash
  oc logs -f build/<build-name>
  ```
- **Fix:**
  - Add build resource limits in `BuildConfig`:
    ```yaml
    spec:
      resources:
        limits:
          memory: "1Gi"
    ```
  - For offline environments, vendoring dependencies into the repo or using an internal Nexus/Artifactory mirror is required.

---

### Issue 5: Route returns `503 Service Unavailable`
- **Symptom:** Visiting the Route URL in a browser returns OpenShift HAProxy `503 Service Unavailable - No server is available to handle this request`.
- **Root Cause:**
  1. The Route `spec.to.name` does not match the `Service` name.
  2. The Service selector does not match the Pod labels.
  3. Pods are not passing Readiness probes (Pods are `0/1 Running` or `Pending`).
- **Diagnosis:**
  ```bash
  # Check if Service has active Endpoints
  oc get endpoints <service-name>
  # If endpoints is <none>, pods are failing readiness or labels do not match!
  ```
- **Fix:**
  - Verify labels: `oc get pods --show-labels` vs `oc describe svc <service-name>`
  - Ensure pods are in `Ready` state.

---

### Issue 6: Binary Build fails with `tar: unexpected EOF` or Broken Pipe
- **Symptom:** `oc start-build --from-dir=.` crashes midway.
- **Root Cause:** Directory contains large untracked files (e.g., massive `.git` history, `node_modules`, virtualenvs, ISOs).
- **Fix:** Create a `.dockerignore` or `.s2iignore` in the source directory to exclude heavy folders, or stream specific subdirectories:
  ```bash
  oc start-build <name> --from-dir=src/
  ```
