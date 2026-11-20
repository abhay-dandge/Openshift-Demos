# Demo 4: OpenShift Binary Build Workflow (Inner-Loop Development)

In standard CI/CD, builds are triggered by git commits pushed to remote repositories. However, during daily local coding (**the inner loop**), pushing git commits for every test edit is slow and pollutes git history.

OpenShift provides a native **Binary Build** mechanism (`source.type: Binary`) that streams local filesystem changes directly into the cluster's build pod over the Kubernetes API.

---

## 1. How Binary Builds Work

```
 Developer Workstation                   OpenShift Cluster
┌───────────────────────┐             ┌───────────────────────────────┐
│  ./src/main.py        │             │  BuildConfig (type: Binary)   │
│                       │             │              │                │
│  $ oc start-build \   │ ──HTTP POST │              ▼                │
│    --from-dir=./src   │   Tar Stream│   Build Pod (S2I Builder)     │
│                       │             │   - Extracts tar to /tmp/src  │
│                       │             │   - Runs S2I assemble         │
│                       │             │   - Pushes to ImageStream     │
└───────────────────────┘             └───────────────────────────────┘
```

---

## 2. Fast Step-by-Step Execution

### Step 1: Create or Switch to OpenShift Project
```bash
oc new-project openshift-demos || oc project openshift-demos
```

### Step 2: Apply Manifests
```bash
oc apply -f k8s/complete-binary-pipeline.yaml
```

### Step 3: Stream Local Code to OpenShift
```bash
# Upload contents of ./src to start the build
oc start-build binary-python-demo --from-dir=./src --follow
```

### Step 4: Make a Code Edit and Re-trigger (Sub-10-Second Feedback)
Edit `src/main.py`:
```python
# Change message or add new route
```
Re-run:
```bash
./trigger-build.sh
```

---

## 3. Advanced Binary Build Options

- Stream from a tar archive:
  ```bash
  tar -czf app.tar.gz -C src .
  oc start-build binary-python-demo --from-file=app.tar.gz --follow
  ```
- Build from a specific single file:
  ```bash
  oc start-build binary-python-demo --from-file=src/main.py --follow
  ```
