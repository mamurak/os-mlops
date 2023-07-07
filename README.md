# OS MLOps

This repository contains a number of open source MLOps tool chains that can be deployed on OpenShift Container Platform.

### [RHODS Pipelines and Serving](odh-kfp-modelmesh.md)

- RHODS Workbench Controller based on Kubeflow Notebook Controller for notebook-based development,
- Data Science Pipelines based on Kubeflow Pipelines for workflow orchestration and experiment tracking,
- RHODS Model Serving based on KServe ModelMesh for model serving.

### RHODS Demo Pack

To quickly set up a RHODS environment for fraud detection and object detection demos, follow these steps:
1. Deploy the RHODS operator on your OpenShift cluster. The demo pack has been tested with RHODS 1.28.1.
2. Deploy the OpenShift Pipelines operator. The demo pack has been tested with Pipelines versions 1.8 to 1.10.
3. (optional) Deploy the Codeflare operator. The demo pack has been tested with Codeflare version 0.0.4.
4. Clone this repository and navigate to `manifests`.
5. Run `oc apply -f projects.yaml`
6. Run `oc apply -k .`

Once the manifests have been deployed, your environment contains:
- A Minio instance as a lightweight S3 storage provider. You can manage the S3 buckets through the Minio UI through the `minio-ui` route URL in project `minio`. Use `minio` and `minio123` for logging in.
- A Data Science Project `fraud-detection` for running the [fraud detection demo](notebooks/fraud-detection/instructions.md). The pipeline server is instantiated and cluster storage and data connections are configured.
- A Data Science Project `object-detection` for running the [object detection demo](notebooks/object-detection-example). The pipeline server is instantiated and cluster storage and data connections are configured. The OVMS model server is instantiatend for model deployment.
- A number of [community workbench images](manifests/odh/custom-notebooks.yaml).
- A number of [custom serving runtimes](manifests/odh/modelmesh/custom-runtimes.yaml).

To get started with your demo, instantiate the respective workbenches.

#### Fraud detection

1. In the RHODS dashboard, enter the `fraud-detection` project.
2. Create a new workbench with an arbitrary name and these parameters:
    - image: `Trino Elyra`
    - existing cluster storage: `development`
    - existing data connection: `fraud-detection`
3. In the workbench, clone this repository, navigate to `notebooks/fraud-detection` and follow the [instructions](notebooks/fraud-detection/instructions.md).

#### Object detection

1. In the RHODS dashboard, enter the `object-detection` project.
2. Create a new workbench with an arbitrary name and these parameters:
    - image: `Object detection Elyra`
    - existing cluster storage: `development`
    - existing data connection: `object-detection`
3. In the workbench, clone this repository, navigate to `notebooks/fraud-detection` and follow the notebooks.