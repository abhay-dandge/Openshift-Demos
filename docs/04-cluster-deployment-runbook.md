# OpenShift Cluster Deployment Runbook

This runbook guides you through deploying the demo suite across various OpenShift platforms:
- **Red Hat OpenShift on AWS (ROSA)**
- **Azure Red Hat OpenShift (ARO)**
- **Red Hat OpenShift Container Platform (Self-Managed / Bare Metal / VMware)**
- **Red Hat OpenShift Local (formerly CRC - CodeReady Containers)**

---

## 1. Prerequisites Checklist

1. **`oc` CLI:** Version 4.10 or higher.
   ```bash
   oc version --client
   ```
2. **Active Cluster Session:**
   ```bash
   oc whoami
   ```
3. **Cluster Ingress / Router:** Ensure the OpenShift default ingress controller is operational:
   ```bash
   oc get ingresscontroller default -n openshift-ingress-operator
   ```

---

## 2. Local Cluster Setup: Red Hat OpenShift Local (CRC)

If testing on your local workstation without a cloud cluster:

```bash
# 1. Download OpenShift Local from console.redhat.com
# 2. Setup CRC
crc setup

# 3. Start cluster (requires 4 vCPUs and 9-16 GB RAM)
crc start --pull-secret-file /path/to/pull-secret.txt

# 4. Set up oc environment
eval $(crc oc-env)
oc login -u developer -p developer https://api.crc.testing:6443
```

---

## 3. Automated Deployment Across All Demos

To deploy all demos in one operation:

```bash
cd "Openshift Demos"
./scripts/deploy-all.sh openshift-demos
```

The script will:
1. Create project `openshift-demos`
2. Deploy Demo 1 (Python S2I App)
3. Deploy Demo 2 (Node.js S2I App)
4. Deploy Demo 3 (Custom S2I Builder & Sample Web App)
5. Deploy Demo 5 (Enterprise Production Stack)
6. Stream builds and await deployment rollouts
7. Print active edge-terminated Route URLs

---

## 4. Manual Per-Demo Deployment

If you want to deploy an individual demo:

### Deploy Python S2I:
```bash
oc project openshift-demos
oc apply -f 01-s2i-python-app/k8s/
oc start-build s2i-python-demo --from-dir=01-s2i-python-app --follow
oc get route s2i-python-demo
```

### Deploy Node.js S2I:
```bash
oc apply -f 02-s2i-nodejs-app/k8s/
oc start-build s2i-nodejs-demo --from-dir=02-s2i-nodejs-app --follow
oc get route s2i-nodejs-demo
```

### Deploy Production Stack with Kustomize:
```bash
oc apply -k 05-complete-production-stack/
oc start-build production-stack --from-dir=05-complete-production-stack/app --follow
oc get route production-stack
```

---

## 5. Teardown & Cleanup

```bash
./scripts/cleanup-all.sh openshift-demos
```
