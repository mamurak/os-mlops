### Pipeline server stays in pending state

- If you're using an HTTP-based S3 storage endpoint, verify that the Pipelines CR is configured properly.
    - Within your Data Science Project namespace, look up the `DataSciencePipelinesApplication` CR named `pipelines-definition`.
    - Ensure that `spec.objectStorage.externalStorage.secure` is `false`. If it's not, set it to `false` and save the CR. The pipeline server should now initialize properly.
    - Refer to `manifests/odh/pipelines-definition.yaml` for reference.

### Pipeline Run request in Elyra fails

- Verify that OpenShift Pipelines operator is installed (versions 1.7.x or 1.8.x).
- Check used Runtime configuration.
    - Verify Kubeflow Pipelines API Endpoint maps to an existing service with an accessible port.
        - check namespace, e.g. for RHODS: `http://ds-pipeline-ui.redhat-ods-applications.svc.cluster.local:3000/pipeline`
    - Verify Cloud Object Storage Endpoint maps to an existing service with an accessible port.
        - e.g. if using Minio in namespace `minio`: `http://minio-service.minio.svc.cluster.local:9000`
    - Verify Cloud Object Storage Bucket Name maps to an existing bucket in S3 storage.
    - Verify Cloud Object Storage credentials are valid and grant RW permissions.

### Elyra unable to submit pipeline jobs to Kubeflow Pipelines

- Verify Elyra runtime:
    - Kubeflow Pipelines API Endpoint:
        - protocol
        - port (verify on service)
        - `/pipeline` suffix
    - Cloud Object Storage:
        - Cloud Object Storage Endpoint
        - bucket name
        - credentials
- Check Network Policies.
    - Are connections between the notebook and the target pod allowed?
    - Are there proxies present in the environment? You might have to allow traffic from all namespaces and from ingress namespace.
- Status of `ds-pipeline` and `ds-pipeline-ui` pod?
- Verify KFP-S3 integration:
    - `mlpipeline-minio-artifact` secret for S3 credentials and endpoint config.
    - `ds-pipeline-config` config map for S3 endpoint.
