# Insurance Claims Workshop Helm Chart

This chart deploys:
- an HTPasswd identity provider for 100 workshop participants,
- the object detection workshop imagestream,
- a variable number of data science projects,
- individual Minio instances with prepopulated S3 buckets.

## Prerequisites

- An OpenShift cluster with internet access. This chart was tested on OCP 4.15.
- Cluster admin access.
- The RHOAI operator and an instantiated Data Science Cluster (e.g. the one in [here](../../dependencies.yaml)). The chart was tested with RHOAI 2.8.0.
- The OpenShift Pipelines operator. The chart was tested with OpenShift Pipelines 1.13.1.

If you don't have Helm installed yet, you can use this recipe:
```
sudo su -
curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 && \
sed -i 's/\/local//' get_helm.sh && \
chmod 700 get_helm.sh && \
bash get_helm.sh && \
su lab-user && \
cd ~
```

## Installation

1. Clone this repository and navigate to this folder:
```
git clone https://github.com/mamurak/os-mlops.git
cd os-mlops/manifests/object-detection-workshop/od-workshop-chart
```

2. Update the number of workshop participants in the `values.yaml` file.

3. Install the chart:
```
helm install od-workshop .
```

4. Update the cluster's `OAuth` CR to consume the htpasswd file that was deployed through the chart. It should contain the following identity provider entry:
```
apiVersion: config.openshift.io/v1
kind: OAuth
metadata:
  name: cluster
spec:
  identityProviders:
  - name: htpasswd
    mappingMethod: claim 
    type: HTPasswd
    htpasswd:
      fileData:
        name: htpass-secret 
```

The new IDP should be usable in a few minutes, after the authentication and console pods have restarted.

5. Optional: You may want to prevent workshop participants from creating new namespaces, which may be enabled by default. Check whether the following role binding exists and remove it if needed.
```
kind: ClusterRoleBinding
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: self-provisioners
subjects:
  - kind: Group
    apiGroup: rbac.authorization.k8s.io
    name: 'system:authenticated:oauth'
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: self-provisioner
```

6. Optional: You may also want to restrict the amount of resources that participants can request.
- As RHOAI admin, go to Settings -> Cluster settings and update `PVC size` (5 GB is a reasonable value).
- Find and customize the workbench and model server sizes in the `OdhDashboardConfig` CR. The following is a reasonable version for the workshop.
```
apiVersion: opendatahub.io/v1alpha
kind: OdhDashboardConfig
metadata:
  name: odh-dashboard-config
  namespace: redhat-ods-applications
  labels:
    app.kubernetes.io/part-of: rhods-dashboard
    app.opendatahub.io/rhods-dashboard: 'true'
spec:
  dashboardConfig:
    modelMetricsNamespace: ''
    enablement: true
    disableProjects: false
    disableSupport: false
    disablePipelines: false
    disableProjectSharing: false
    disableModelServing: false
    disableKServe: false
    disableCustomServingRuntimes: false
    disableModelMesh: false
    disableISVBadges: false
    disableInfo: false
    disableClusterManager: false
    disableBYONImageStream: false
    disableTracking: false
  groupsConfig:
    adminGroups: rhods-admins
    allowedGroups: 'system:authenticated'
  modelServerSizes:
    - name: Small
      resources:
        limits:
          cpu: '2'
          memory: 8Gi
        requests:
          cpu: '1'
          memory: 4Gi
  notebookController:
    enabled: false
    notebookNamespace: rhods-notebooks
    pvcSize: 5Gi
  notebookSizes:
    - name: Small
      resources:
        limits:
          cpu: '2'
          memory: 8Gi
        requests:
          cpu: '1'
          memory: 8Gi
  templateOrder: []
```

## Usage

Log into the RHOAI dashboard with a participant account:
- login: user[n]
- password: user[n]

You should only have access to your namespace / data science project, in which you can follow the [workshop guide](https://mamurak.github.io/rhods-od-workshop/rhods-od-workshop/index.html). By navigating to the OpenShift console, you can find your personal Minio instance and browse its S3 buckets.

## Deinstallation

Delete the Helm chart:

```
helm delete od-workshop
```