# Ray demo

Here is how you set up and go through the Ray demo.

## Requirements

Make sure you have the RHODS demo pack installed. Note that RHODS operator v2 is needed for deploying the CodeFlare stack:
- If you're on RHODS 1.33.0, change the operator subscription channel to `alpha`.
- Once operator 2.x is installed, create a new `Data Science Cluster` instance through the operator page.
- In the form view of `DataScienceCluster`, open the `Components` drop-down view and ensure that the `managementState` of `codeflare` and `ray` has the value `Managed`. Click `Create`.
- Ensure that the `CodeFlare Operator` is installed. The community operator version is recommended as of RHODS 1.33.

Deploying the demo requires [Helm v3](https://helm.sh/docs/intro/install/).


## Deploying the demo

Ensure you're logged into the OpenShift cluster as cluster admin and the required operators are installed (see above).

Navigate to `/manifests/ray-demo` and edit `values.yaml`:
- Set `clusterdomainurl` to the domain URL of your OpenShift cluster.
- Set `ocptoken` to the token value of your OpenShift authentication token. You can find it in the OpenShift web console after clicking on your user name (top right corner) and `Copy login command`.

Deploy the Helm chart:

```
helm install ray-demo .
```

The deployment of all components may take up to 30 minutes.

## Post-configuration

### Prepare data sources

Open the Minio admin console via the `minio-ui` route URL in the `minio` namespace. Log in with `minio` / `minio123`. Navigate to `Buckets` and select `Create Bucket`. Enter `ray-demo` under bucket name and select `Create Bucket`.

## Running the end-to-end workflow

### Interactive 

TODO