# OS MLOps

This repository contains a number of open source MLOps tool chains that can be deployed on OpenShift Container Platform.

### [ODH Pachyderm Pipelines](odh-pachyderm-pipelines.md)
- OpenShift Data Foundation / Ceph S3 as a data lake,
- Trino for data integration,
- Pachyderm for data versioning,
- JupyterHub for notebook-based development,
- mlflow for experiment tracking.

### [ODH KFP Seldon](odh-kfp-seldon.md)
- JupyterHub for notebook-based development,
- Kubeflow Pipelines for workflow orchestration and experiment tracking,
- Seldon Core for model serving,
- ArgoCD for continuous model deployment,
- Prometheus and Grafana for model monitoring.

### [ODH KFP ModelMesh](odh-kfp-modelmesh.md)
- Kubeflow Notebook Controller for notebook-based development,
- Kubeflow Pipelines for workflow orchestration and experiment tracking,
- KServe ModelMesh for model serving,
- ArgoCD for continuous model deployment,
- Prometheus and Grafana for model monitoring.