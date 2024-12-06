# Red Hat OpenShift AI on Developer Hub

A Backstage Golden Path Template for a Red Hat OpenShift AI data science project.

Current version:
- Simple [Golden Path Template](template.yaml)
- Component [Catalog Info](./skeleton/catalog-info.yaml)
- [Helm chart](./manifests/helm/ds-project/) for the data science project:
  - Data science project
  - Data Connection
  - Data Storage
  - Workbench
  - Rolebinding for `rhods-users` (please create the [group](manifests/k8s/rhods-users.yaml) first)
- Tekton pipeline for loading a notebook in the workbench
- ArgoCD applications
- Jupyter notebook with a scikit-learn regression exercise
- TechDocs - Please see [Generate TechDocs with a Tekton pipeline](https://github.com/stefan-bergstein/doc-pipe)

Main limitations:
- Github only
- Experimental only. No support. Use on your own risk!

Next steps:
- Deploy a model server
- Notebook for deploying and testing a trained model
- Support GitLab
