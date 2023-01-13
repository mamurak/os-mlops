### Pipeline Run request in Elyra fails

- Verify that OpenShift Pipelines operator is installed (versions 1.7.x or 1.8.x).
- Check used Runtime configuration.
    - Verify Kubeflow Pipelines API Endpoint maps to an existing service with an accessible port.
        - check namespace, e.g. for RHODS: `http://ds-pipeline-ui.redhat-ods-applications.svc.cluster.local:3000/pipeline`
    - Verify Cloud Object Storage Endpoint maps to an existing service with an accessible port.
        - e.g. if using Minio in namespace `minio`: `http://minio-service.minio.svc.cluster.local:9000`
    - Verify Cloud Object Storage Bucket Name maps to an existing bucket in S3 storage.
    - Verify Cloud Object Storage credentials are valid and grant RW permissions.