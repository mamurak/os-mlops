# Visual Inspection on OpenShift

This use case is centered on using OpenShift Virtualization to implement an end-to-end AI use case on OpenShift. For this we're replicating the _Manuela Visual Inspection_ demo that was developed by Stefan Bergstein.

## Setup

* We're following the [Manuela Visual Inspection demo instructions](https://github.com/stefan-bergstein/manuela-visual-inspection) ([slides](https://docs.google.com/presentation/d/1t9dOPR_wkh0O70CX6ZT5gr-YmeqDrkzB1i9W5GczhO0/edit#slide=id.g105149e662a_0_131)).
* We're using an Equinix Metal OpenShift Cluster deployed through RHDP (OpenShift AIO) for the CNV / data labelling use case. Its specs are:
    * 3 controller nodes : 8cores / 24Gb memory
    * 3 worker nodes : 16cores / 50Gb memory
* We're using an SNO instance deployed on a GPU node for the model training and serving use case. The node specs are:
    * 24cores / 128Gb memory
    * NVidia Tesla M60 GPU

## Procedure

### Deploying CVAT with OCP-V

CVAT is the Computer Vision Annotation Toolkit maintained by the OpenCV community and allows to annotate images through a graphical user interface. In the demo it's used to showcase data labeling in a visual inspection use case.

CVAT is a containerized application. However, it's not compatible with Kubernetes, instead it's intended to be deployed through docker-compose. To still run it on OCP, next to the ML development and deployment environment, we're using OpenShift Virtualization to host CVAT in an OCP-based VM.

#### Preparation

1. Provision _OpenShift AIO (Equinix Metal) with OpenShift Virtualization_ Lab RHDP item.
2. Provision the virtualization cluster.
3. SSH into the bastion host.
4. Download `virtctl` to the bastion host through the OCP cluster (check out _Command Line Tools_).
    1. As we don’t have a valid CA cert, we need to use `wget –no-check-certificate` to handle `https`.
    2. Unpack the archive and copy the binary to `/usr/local/bin`.

#### VM deployment

Follow the [demo setup instructions](https://github.com/stefan-bergstein/manuela-visual-inspection/blob/main/docs/cvat-cnv.md). Additional notes below.

1. Create project `hackathon`.
2. Provision a VM:
    * CentOS Stream 8
    * project `hackathon`
    * customize the deployment: 2 CPU, 8 GB RAM
    * use PVC as per template

#### App deployment

Follow the [demo setup instructions](https://github.com/stefan-bergstein/manuela-visual-inspection/blob/main/docs/cvat-cnv.md). Additional notes below.

1. Install `docker-compose`.
2. Clone the CVAT repository.
    * NOTE: Check out version 1.4.0 as the more recent versions are deployed differently than documented in the demo instructions.
3. Add image tag `v1.4.0` to the CVAT service container entries.
4. Start CVAT through `docker-compose`.
5. Expose the service on the bastion host using `virtctl`.
    * Ensure the VM name is correct, replace it if necessary.
6. Expose the service externally using a `route`.
7. Log into the app admin console and add users. Proceed with the demo as documented.

### ML training

Using the annotated image data we're training a machine learning model for detecting scratches and bents in metal nut images. The training is run within a JupyterLab instance in OpenShift Data Science (RHODS). Running the training algorithm on a GPU node is recommended but not required.

1. Deploying SNO on GPU node using Assisted Installer (with LMVS installation option).
2. Installing Node Feature Discovery Operator.
    * Create `NodefeatureDiscovery` instance: `nfd-instance`
    * Node Feature Discovery Operator uses vendor PCI IDs to identify hardware in our node. `0x10de` is the PCI vendor ID that is assigned to NVIDIA:
        ```
        $ oc describe node | egrep 'Roles|pci'
        Roles:              control-plane,master,worker
                            feature.node.kubernetes.io/pci-102b.present=true
                            feature.node.kubernetes.io/pci-10de.present=true
                            feature.node.kubernetes.io/pci-14e4.present=true
        ```
3. Installing NVIDIA GPU Operator.
    * Create ClusterPolicy: `gpu-cluster-policy`
    * Both GPUs are detected:
        ```
        $ oc describe node| sed '/Capacity/,/System/!d;/System/d'
        Capacity:
        cpu:                          24
        ephemeral-storage:  936104940Ki
        hugepages-1Gi:       0
        hugepages-2Mi:       0
        memory:                   131556044Ki
        nvidia.com/gpu:      2
        pods:                        250
        ```
4. Installing Red Hat OpenShift Data Science Operator.
    * On platforms that do not provide shareable object storage, the OpenShift Image Registry Operator bootstraps itself as `Removed`. This allows `openshift-installer` to complete installations on these platform types. After installation, you must configure the storage and edit the Image Registry Operator configuration to switch the managementState from `Removed` to `Managed`.
        * Create PVC: `image-registry-storage`
        * Enable [Image registry](https://access.redhat.com/documentation/en-us/openshift_container_platform/4.12/html-single/registry/index#configuring-registry-storage-baremetal)
    * Create Data Science Project: `hackathon-ds`
    * Create Workbench: `hackathon-wb` (`CUDA` image)
    * Create Cluster Storage: `hackathon-cs`
    * GPU: not shown (but will use it) - BUG???
5. Enter workbench.
    * Clone [Git Repository](https://github.com/stefan-bergstein/manuela-visual-inspection).
    * Run notebook: `manuela-visual-inspection/ml/pytorch/Manuela_Visual_Inspection_Yolov5_Model_Training.ipynb`

### ML deployment

The actual visual inspection use case with "live" data is implemented through a simulated camera data source that streams metal nut images onto a Kafka topic. A serverless ML client consumes these images and sends them to an ML service managed by RHODS. A dashboard application visualizes the metal nut images and the defects that are detected by the deployed ML model.

The model can be deployed within a separate environment, in principle even on MicroShift (reflecting the likely customer scenario). During the hackathon we chose to reuse the SNO instance that we used for the ML training part.

Follow the instructions as per [demo documentation](https://github.com/stefan-bergstein/manuela-visual-inspection/blob/main/docs/runtime.md#installation). Additional comments below.

1. Deploy [Minio](https://github.com/mamurak/os-mlops/blob/master/manifests/minio/minio.yaml) for S3 storage.
    * Call the Minio dashboard route and log in (`minio`/`minio123`). Create a bucket with name `models`.
2. Deploy the trained model with RHODS model serving.
    * In the RHODS dashboard, navigate to project `hackathon-ds`.
    * Configure the model server.
    * Download the [trained model](https://github.com/stefan-bergstein/manuela-visual-inspection/releases/tag/v0.3-alpha-pytorch-rhods). Choose `manu-vi-best-yolov5m.onnx` for the best performance.
    * Upload the model file into the `models` bucket through the Minio GUI.
    * Select `Deploy model` in the RHODS dashboard. Specify the data connection parameters:
        * name: models
        * access key: `minio`
        * secret key: `minio123`
        * S3 endpoint URL: `http:minio-service.minio.svc:9000`
        * bucket name: `models`
        * model format: `ONNX`
        * model path: `manu-vi-best-yolov5m.onnx`
    * Validate the model deployment through the [inference notebook](https://github.com/stefan-bergstein/manuela-visual-inspection/blob/main/ml/pytorch/Manuela_Visual_Inspection_Yolov5_Infer_Rest.ipynb).
3. Deploy Kafka.
    * Deploy the AMQ Streams operator version 2.3.x.
    * Deploy the Kafka cluster manifest.
    * Deploy the Kafka topic manifest.
4. Deploy OpenShift Serverless.
    * Deploy the operator.
    * Instantiate `KnativeServing`, `KnativeEventing`, `KnativeKafka`.
        * In the `KnativeKafka` specs, set the following flags:
            * `spec.broker.enabled`: `true`
            * `spec.channel.enabled`: `true`
            * `spec.sink.enabled`: `true`
            * `spec.source.enabled`: `true`
5. Deploy the ML application.
    * Deploy the build configs and imagestreams.
        * Fix the API versions of the imagestreams. They should be:
            * `apiVersion: image.openshift.io/v1`
    * Deploy the `KafkaSource`.
        * Update the Kafka bootstrap server URL.
        * Ensure the `manuela-visual-inspection` namespace is used.
    * Deploy the `KafkaTriggers`.
    * Call the visual inspection dashboard to see real-time scratch and bent detection.
        * Call the dashboard through HTTP instead of HTTPS.
        * You may want to double check the Network Policies to ensure the `image-processor` can send requests to the deployed model within the `hackathon-ds` namespace.
