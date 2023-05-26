# Installing Data Science Pipelines

Data Science Pipelines is currently not included in RHODS. This guide details how it can be deployed and integrated as a beta feature and used with Elyra.

## Prerequisites

* Red Hat OpenShift Data Science version 1.21 or above.
* OpenShift Pipelines operator version 1.7.2 or above.
* S3 based object storage, e.g. OpenShift Data Foundation or Minio.

### Restricted access to Internet

There are multiple artifacts from Github that will need to be downloaded while setting up and running the environment. In case Github is not accessible from the OpenShift cluster, make the following files available on a file server that is accessible from the OpenShift cluster:
* the [ODH 1.4 manifests](https://github.com/opendatahub-io/odh-manifests/tarball/v1.4),
* the Elyra bootstrap files located in `manifests/elyra/`.

## Preparing the S3 storage backend

Both Data Science Pipelines and Elyra require an S3 bucket. Create these buckets in your S3 storage and note their respective S3 service endpoint URLs, bucket names, access keys, and secret keys.

To quickly spin up a Minio instance for testing purposes, you can deploy the `manifests/minio/minio.yaml` manifest. Once it's running, create the `elyra` bucket through its GUI, which is exposed through the Minio route in project `minio`. The credentials are:
- login, access key: `minio`
- password, secret key: `minio123`

Note that the pipelines bucket does not have to be created manually in Minio since it is generated directly by Data Science Pipelines, given that the credentials provide permissions to create buckets.

## Installing Data Science Pipelines

Review `manifests/odh/ds-pipelines.yaml`. You can deploy it without modifications if you're using S3 through Minio as deployed in the previous step. In case of an alternative S3 backend, modify the following parameters before deploying the manifest:
- In secret `mlpipeline-minio-artifact`:
    - `accessKey`: S3 access key for pipelines bucket,
    - `host`: host name of S3 service,
    - `port`: port of S3 service,
    - `secretkey`: S3 secret key for pipelines bucket,
    - `secure`: `true` if HTTPS is used, else `false`.
- In configmap `pipeline-install-config`:
    - `bucketName`: name of pipelines bucket.
- In configmap `ds-pipeline-config`:
    - `artifact_endpoint`: host name of S3 service,
    - `artifact_endpoint_scheme`: S3 URL protocol prefix,
    - `artifact_bucket`: name of pipelines bucket.

The deployment may take ca. 5-10 minutes. Open the RHODS dashboard and navigate to `Applications` -> `Explore`. Click on the `Data Science Pipelines` tile and select `Enable`. You can now access the Data Science Pipelines dashboard through `Applications` -> `Enabled` once the Data Science Pipelines pods have been deployed.

## Configure the Elyra environment

### If access to internet is restricted

* Ensure Elyra bootstrap files are hosted as described [above](#restricted-access-to-internet).
* Access JupyterHub spawner page (ODH dashboard -> Launch JupyterHub application).
* Add the following environment variables
    * `ELYRA_BOOTSTRAP_SCRIPT_URL`: URL of hosted `bootstrapper.py`
    * `ELYRA_PIP_CONFIG_URL`: URL of hosted `pip.conf`
    * `ELYRA_REQUIREMENTS_URL`: URL of hosted `requirements-elyra.txt`
    * `ELYRA_REQUIREMENTS_URL_PY37`: URL of hosted `requirements-elyra-py37.txt`
* TODO: move this configuration into the custom notebook image.

### Prepare backend services

* Deploy `manifests/odh/kfp/ds-pipeline-ui-service.yaml`.
* In project `openshift-storage` deploy `manifests/odf/s3-http-route.yaml` if using OpenShift Data Foundation.

### Set up Elyra runtime

Deploy `manifests/odh/custom-notebooks.yaml` for Elyra-enabled custom workbench images.

The default runtime assumes you're using the Minio backend as described above. In case of an alternative S3 storage, edit the S3 configuration through the Runtimes settings:
* Launch Elyra notebook in the Jupyter spawner page.
* Open Runtimes configuration (`Runtime` in left toolbar).
* Next to `Default`, select `Edit`.
* Update the `Kubeflow Pipelines` settings as shown below. In case of RHODS, replace `odh-applications` with `redhat-ods-applications`.
* Update the cloud object storage endpoint, bucket name, user name, and password using your S3 storage and Elyra bucket details.

![Elyra runtime](elyra-runtime.png "Eyra runtime")

### Configure pipeline

* Update and deploy `notebooks/elyra-kfp-onnx-example/manifests/pipeline-secret.yaml` (use the default values if you're using the Minio installation outlined above):
    * `AWS_S3_ENDPOINT`: your S3 endpoint URL such as `http://s3.openshift-storage.svc.cluster.local`
    * `AWS_ACCESS_KEY_ID`: S3 access key with bucket creation permissions, for example value of `AWS_ACCESS_KEY_ID` in secret `noobaa-admin` in project `openshift-storage`.
    * `AWS_SECRET_ACCESS_KEY`: corresponding S3 secret key, for example value of `AWS_SECRET_ACCESS_KEY_ID` in secret `noobaa-admin` in project `openshift-storage`.

# Run the pipeline

* Enter or launch the Elyra KFNBC notebook in the Jupyter spawner page.
* Clone this repository.
    * Open git client (`Git` in left toolbar).
    * Select `Clone a Repository`.
    * Enter the repository URL `https://github.com/mamurak/os-mlops.git` and select `Clone`.
    * Authenticate if necessary.
* Open `notebooks/elyra-kfp-onnx-example/model-training.pipeline` in the Kubeflow Pipeline Editor.
* Select `Run Pipeline` in the top toolbar.
* Select `OK`.
* Monitor pipeline execution in the Kubeflow Pipelines user interface (`ds-pipelines-ui` route URL) under `Runs`.

# How-To

* Change the available notebook deployment sizes.
    * Find the `odh-dashboard-config` object of kind `OdhDashboardConfig` in project `odh-applications`.
    * Add or update the `spec.notebookSizes` property. Check `manifests/odh/odh-dashboard-config.yaml` for reference.

* Clone git repositories with JupyterLab.
    * Open git client (`Git` in left toolbar).
    * Select `Clone a Repository`.
    * Enter the repository URL and select `Clone`.
    * Authenticate if necessary.

* Build and add custom notebook
    * Deploy `manifests/odh/images/custom-notebook-is.yaml`.
    * Deploy `manifests/odh/images/custom-notebook-bc.yaml`.
    * Trigger build of the new build config and wait until build finishes.
    * As an ODH admin user, open the `Settings` tab in the ODH dashboard.
    * Select `Notebook Images` and `Import new image`.
    * Add new notebook with repository URL `custom-notebook:latest` and appropriate metadata.
    * Verify custom notebook integration in the JupyterHub provisioning page. You should be able to provision an instance of the custom notebook that you have defined in the previous step.

* Add packages to custom notebook image with pinned versions.
    * Within a custom notebook instance, install the package through `pip install {your-package}`.
    * Note the installed version of the package.
    * Add a new entry in `container-images/custom-notebook/requirements.txt` with `{your-package}=={installed-version}`.
    * Trigger a new image build.
    * Once the build is finished, provision a new notebook instance using the custom notebook image. The new package is now available.

* Create Elyra pipelines within JupyterLab.
    * Open the Launcher (blue plus symbol on top left corner of the frame).
    * Select `Kubeflow Pipeline Editor`.
    * Drag and drop notebooks from the file browser into the editor.
    * Build a pipeline by connecting the notebooks by drawing lines from the output to input ports of the node representation. Any directed acyclic graph is supported.
    * For each node, update the node properties (right click on node and select `Open Properties`):
        * `Runtime Image`: Select the appropriate runtime image containing the runtime dependencies of the notebook.
        * `File Dependencies`: If the notebook expects a file to be present, add this file dependency here. It must be present in the file system of the notebook instance.
        * `Environment Variables`: If the notebook expects particular environment variables to be set, you can set them here.
        * `Kubernetes Secrets`: If you would like to set environment variables through Kubernetes secrets rather than defining them in the Elyra interface explicitly, you can reference the environment variables through the corresponding secrets in this field.
        * `Output Files`: If the notebook generates files that are needed by downstream pipeline nodes, reference these files here.
    * Save the pipeline (top toolbar).

* Submit Elyra pipeline to Kubeflow Pipelines backend.
    * Open an existing pipeline within the Elyra pipeline editor.
    * Select `Run Pipeline` (top toolbar).
    * Select the runtime configuration you have prepared before and click `OK`.
    * You can now monitor the pipeline execution within the Kubeflow Pipelines GUI under `Runs`.
