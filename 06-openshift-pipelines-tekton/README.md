# Demo 6: OpenShift Pipelines (Tekton) Cloud-Native S2I CI/CD

Red Hat OpenShift Pipelines provides cloud-native CI/CD based on the Tekton project, running natively inside OpenShift with Kubernetes-native resources.

---

## 1. What This Demo Demonstrates

- Using official Red Hat **ClusterTasks**:
  - `git-clone`: Clones git repository into a shared PersistentVolume workspace.
  - `s2i-python`: Executes Source-to-Image in a pipeline step using Red Hat UBI builders.
  - `openshift-client`: Triggers rolling deployment and verifies rollout status using `oc`.
- Declarative `Pipeline` and `PipelineRun` specifications.

---

## 2. Prerequisites

The **Red Hat OpenShift Pipelines Operator** must be installed on your cluster:
```bash
# In the OpenShift Web Console:
# Operators -> OperatorHub -> Search "Red Hat OpenShift Pipelines" -> Install
```

---

## 3. Running the Pipeline

### Via OpenShift CLI (`oc` / `tkn`)
```bash
# 1. Switch to demo project
oc project openshift-demos

# 2. Apply pipeline definition and PVC
oc apply -f pipeline.yaml

# 3. Start a PipelineRun using the Tekton CLI (tkn)
tkn pipeline start s2i-python-ci-cd-pipeline \
  --workspace name=shared-workspace,claimName=s2i-pipeline-workspace-pvc \
  --showlog

# Or launch via oc
oc create -f pipeline.yaml
```

### Visual Tracking
Navigate to the OpenShift Web Console:
**Pipelines** -> **Pipelines** -> Click `s2i-python-ci-cd-pipeline` to see real-time graphical execution graph and task logs.
