# Table of contents
1. [Getting started](#getting-started)
    * [Deploying the environment](#deploying-the-environment)
    * [Set up the data infrastructure](#set-up-the-data-infrastructure)
    * [Run the pipelines](#run-the-pipelines)
2. [Data engineer and data scientist workflow](#data-engineer-and-data-scientist-workflow)
3. [Folder structure](#folder-structure)
4. [References](#references)

# Getting started

## Deploying the environment

#### Install OpenShift Data Foundation cluster

* Go to Operator Hub. Find OpenShift Data Foundation (OpenShift Container Storage in older versions). Install the operator.
* Instantiate a storage cluster. This will take some time (~ 15 minutes).
* Switch to the `openshift-storage` project.
* Find the `noobaa-admin` secret. Note the S3 credentials.
* Find the `noobaa-mgmt` route and log into the management console using the Noobaa admin credentials.
* Create buckets:
    * accounts
    * creditcards
    * demographics
    * features
    * labels
    * loans
    * pachyderm
    * trino

#### Deploy PostgresQL instance

* Install operator (`Crunchy Postgres for Kubernetes` community operator) from the Operator Hub.
    * Note: mlflow deployment depends on this.
* Deploy `manifests/postgresql/custom-sql.yaml`.

#### Install Open Data Hub

* Create a new project `odh`.
* Adapt and deploy `manifests/trino/trino-s3-credentials.yaml`.
* Install the Open Data Hub operator from the Operator Hub.
* Select Open Data Hub operator in Installed Operators within project `odh`.
* Adapt and deploy `manifests/odh.yaml`.
    * The Trino parameter `s3_endpoint_url` needs to be set to the https location of the `s3` route in `openshift-storage`.
* After all components have been deployed, scale down the `opendatahub-operator` pod to 0 in the `openshift-operators` project. This is required so we can freely configure the ODH components.
* Verify the deployment by opening the `odh-dashboard`route URL. You should see the ODH dashboard.

#### Set up Trino

* Adapt and deploy `manifests/trino/hive-config.yaml`.
    * Property `fs.s3a.endpoint` in `hive-site.xml` needs to be set to the https location of the `s3` route in `openshift-storage`.
* Adapt and deploy `manifests/trino/trino-catalog.yaml`.
    * Property `hive.s3.endpoint` in `hive.properties` needs to be set to the https location of the `s3` route in `openshift-storage`.
    * Property `connection-password` in `postgresql.properties` needs to be set to the value of `password` in secret `custom-sql-pguser-custom-sql`.
* Adapt and deploy `manifests/trino/trino-config.yaml`.
    * Property `s3_endpoint_url` needs to be set to the https location of the `s3` route in `openshift-storage`. Remove the `https://` prefix.
* Adapt and deploy `manifests/trino/hive-metastore.yaml`.
    * `S3_ENDPOINT` in `spec.template.spec.containers[0].env` needs to be set to the https location of the `s3` route in `openshift-storage`. Remove the `https://` prefix.
* Deploy `manifests/trino/trino-coordinator.yaml`.
* Deploy `manifests/trino/trino-worker.yaml`.
* Restart the `hive-metastore`, `trino-coordinator`, and `trino-worker` pods.

#### Install Pachyderm

* Install Pachyderm operator from the Operator Hub.
* Adapt and deploy `manifests/pachyderm/pachyderm-s3-secret.yaml`.
* Deploy `manifests/pachyderm/pachyderm.yaml`.

#### Install mlflow

* Note: The PostgresQL operator needs to be installed prior to deploying mlflow (see above).
* Log into bastion host (machine that has full access to the OCP nodes and is logged into the cluster through `oc`).
* Install Helm
    * `sudo su -`
    * `curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3`
    * `sed -i 's/\/local//' get_helm.sh`
    * `chmod 700 get_helm.sh`
    * `bash get_helm.sh`
    * `logout`
* Install mlflow Helm chart (if S3 is backed by ODF. For other S3 variants, see below.)
    * `oc project odh`
    * `helm repo add strangiato https://strangiato.github.io/helm-charts/`
    * `helm repo update`
    * `helm install mlflow strangiato/mlflow-server`
* Verify the deployment by opening the `mlflow-mlflow-server` route URL. You should see the mlflow dashboard.
* If using other S3 variants,
    * ensure bucket `mlflow` is present and note credentials and S3 endpoint.
    * `oc project odh`
    * `git clone https://github.com/mamurak/helm-charts.git`
    * `cd helm-charts`
    * `git checkout alternate-s3`
    * `cd charts/mlflow-server`
    * `vim values.yaml`
        * set `objectStorage.objectBucketClaim.enabled` to `false`
        * set `S3EndpointUrl`
        * set `MlflowBucketName` to `mlflow`
        * set `S3AccessKeyId`
        * set `S3SecretAccessKey`
    * `helm repo add strangiato https://strangiato.github.io/helm-charts/`
    * `helm dependency build`
    * `helm install mlflow -f values.yaml .`

#### Set up custom notebook

* Create imagestream `s2i-custom-notebook`.
    * Use metadata from `manifests/jupyterhub/s2i-custom-notebook-imagestream.yaml`.
* Deploy `manifests/jupyterhub/s2i-custom-notebook.yaml`.
* Trigger a build.
* Once the build finishes, adapt and deploy `manifests/jupyterhub/s2i-custom-notebook-ist.yaml`.
    * Replace the imagestream name (starting with `sha256:`) with the one from the new build:
        * `tag.from.name`
        * `image.metadata.name`
        * `image.dockerImageReference`

#### JupyterHub

* Access JupyterHub through the `jupyterhub` route URL.
* You should see the Jupyter environment configuration page. You should see the `custom notebook image` among the available notebook images.
* In case you're using custom certificates in your environment, you might not be able to access the JupyterHub entry page (HTTP error 599). To work around this issue, do the following:
    * In the `jupyterhub-cfg` configmap, set the `jupyterhub_config.py` parameter to `c.OpenShiftOAuthenticator.validate_cert = False`.
    * Restart the JupyterHub pods.

#### Set up pipeline builds

* The folder `manifests/pipelines` contains for each pipeline (`X`) a subfolder with three resources: a secret, an imagestream, and a build config.
* Adapt and deploy the secrets (`X-pipeline-secret.yaml`).
* Deploy the imagestreams (`X-pipeline-is.yaml`).
* Deploy the build configs (`X-pipeline-bc.yaml`).
* Trigger a build for each pipeline.

## Set up the data infrastructure

#### Load custom notebook

* Access `jupyterhub` route URL.
* On the JupyterHub configuration page
    * select `custom notebook image`,
    * choose container size `Medium`,
    * and Start Server.
* If the loading screen is stuck, open the `jupyterhub` route URL again. You should see the JupyterLab screen.

#### Run data notebooks

* Click the Git icon in the left toolbar.
* Clone this repository.
* Open `notebooks/s3-upload.ipynb`.
    * Adapt S3 credentials and run the notebook.
* Run `notebooks/initialize_tables.ipynb`.

## Run the pipelines

#### Install Pachyderm client

* Open shell session on management host. It needs the `oc` client and connectivity to the OpenShift cluster (e.g. the bastion host).
* Run `curl -o /tmp/pachctl.tar.gz -L https://github.com/pachyderm/pachyderm/releases/download/v2.2.7/pachctl_2.2.7_linux_amd64.tar.gz && tar -xvf /tmp/pachctl.tar.gz -C /tmp && sudo cp /tmp/pachctl_2.2.7_linux_amd64/pachctl /usr/local/bin`
* Verify installation by running `pachctl version --client-only`. You should see the client version.

#### Connect with Pachyderm instance

* `oc project odh`
* `pachctl config import-kube local --overwrite`
* `pachctl config set active-context local`
* `pachctl port-forward`
    * This command blocks. Open a new shell session to continue.
* Verify integration by running `pachctl version`. You should see the client and instance versions.

#### Deploy pipelines

* `git clone {this repository}`
* `cd {repository}/pipeline-definitions`
* For each pipeline `X` run:
    * `pachctl create pipeline -f X.json`
* For updating existing pipelines `X` run:
    * `pachctl update pipeline -f X.json`
* For inspecting a running pipeline `X` run:
    * `pachctl inspect pipeline X`

# Data engineer and data scientist workflow

* Develop pipeline code in notebooks, see `notebooks/preprocessing.ipynb`.
* To prepare the containerized pipeline, create a folder in `container-images` containing
    * a `Containerfile`,
    * a `requirements.txt`,
    * the main code.
    * See `container-images/preprocessing-pipeline`.
* To prepare the container builds, create a folder in `manifests/pipelines` with three manifests:
    * a secret,
    * an imagestream,
    * a build config.
    * See `manifests/pipelines/preprocessing`.
* Deploy these resources into the `odh` project and trigger a container build.
* Create a pipeline definition in `pipeline-definitions`, see `pipeline-definitions/preprocessing_pipeline.json`.
* Run the pipeline with `pachctl create pipeline -f <pipeline definition>`.
* Monitor pipeline progress:
    * through the client: `pachctl inspect pipeline <pipeline>`,
    * through OpenShift: access the logs of the pipeline pod,
    * through Trino, for instance via the `trino-access` notebook.

# Folder structure

* `data`: the dummy data representing raw data to be stored in the datalake and processed by the preprocessing pipelines.
* `notebooks`: scripts and sample procedures for ODH component integration.
* `pipeline definitions`: Pachyderm pipeline manifests.
* `manifests`: OpenShift deployment artifacts.
* `container-images`: dependencies of container builds.

# References

* [OpenShift Container Platform](https://docs.openshift.com/container-platform/4.10/welcome/index.html)
* [OpenShift Data Foundation](https://access.redhat.com/documentation/en-us/red_hat_openshift_data_foundation/4.10)
* [Open Data Hub](https://opendatahub.io/) ([Github](https://github.com/opendatahub-io/odh-manifests))
* [Trino](https://trino.io/docs/current/index.html)
* [Pachyderm](https://docs.pachyderm.com/latest/)
* [JupyterHub](https://jupyterhub.readthedocs.io/en/latest/)
* [mlflow](https://www.mlflow.org/docs/latest/index.html)
* [Prometheus](https://prometheus.io/docs/introduction/overview/)
* [Grafana](https://grafana.com/docs/grafana/latest/)
* [OpenShift Logging](https://docs.openshift.com/container-platform/4.10/logging/cluster-logging.html)
