# Example: Fraud Detection

This folder contains a simple fraud detection example to demonstrate:
- ML model training using Elyra Pipelines & Data Science Pipelines,
- offline scoring using Elyra Pipelines & Data Science Pipelines,
- online scoring using RHOAI Model Serving.

## Prerequisites

The content in this folder has been developed on Red Hat OpenShift Data Science 1.27 running on OpenShift Container Platform 4.13. It assumes you're running a workbench with custom image `quay.io/mmurakam/trino-notebook:trino-notebook-v0.1.2` in a Data Science Project with an enabled Pipeline server. It further assumes that you have cloned this repository in that workbench.

## Demo Setup

### S3 Data Connection

- Create a bucket in your connected S3 storage.
- Create a Data Connection in the current Data Science Project using the credentials, endpoint configuration, and bucket name of the new bucket. The name of the Data Connection should be `fraud-detection`.
- Mount the Data Connection into this workbench. If there is another mounted Data Connection, unmount that one first. Restart the workbench.

### Sample Data

- Upload the data samples `training-data.csv` and `live-data.csv` from [here](https://github.com/mamurak/os-mlops-artefacts/tree/fraud-detection-data-v0.1/data/fraud-detection) into the S3 bucket.

### Persistent Volume Claims

- Deploy the `manifests/pvcs.yaml` manifest into the current Data Science Project namespace (skip this step if you deployed the RHODS Demo Pack).

## Running the demo

### Model Training

Open `training/training-workflow.ipynb`. This notebook contains the essential steps of a generic model training workflow. Execute the cells. During execution, the training data should be downloaded into the `data` subfolder and a `model.onnx` artifact should appear in the working directory. Browse the connected S3 bucket. You should see the trained model as `model-latest.onnx` as well as with a timestamped identifier.

Open the preconfigured Elyra pipeline `training/model-training.pipeline`. It consists of the same code that you have executed through the notebook, but now the individual steps are defined as part of a linear workflow. Click `Run Pipeline`. You are able to edit the values of three parameters with which to customize your training run:
- `data_object_name`: The object name of your serialized training data in the connected S3 bucket.
- `epoch_count`: Training parameter governing the training duration.
- `learning_rate`: Training parameter governing the model plasticity.
- `model_object_prefix`: Prefix of the published model artifact identifier.

Click `OK` to submit the pipeline to Data Science Pipelines. You should see the confirmation message _Job submission to Kubeflow Pipelines succeeded_.

In the RHODS dashboard, navigate to `Data Science Pipelines` -> `Runs` -> `Triggered`. Ensure your current Project is selected. Select the top run that starts with `model-training-`. You can now observe the execution of the model training pipeline in realtime.

In the connected S3 bucket, you will see the new model artifacts as before. In the Elyra bucket, you will see a new folder with the run identifier starting with `model-training-`. This folder contains the file dependencies, log output, and produced artifacts of each pipeline task.

### Offline Scoring

Open `offline-scoring/offline-scoring.ipynb`. This notebook contains the essential steps of a generic offline scoring workflow. Execute the cells. During execution, the "live" data should be downloaded into the `data` subfolder and a `model.onnx` artifact should appear in the working directory. Browse the connected S3 bucket. You should see the prediction results with a timestamped identifier (`predictions-...csv`).

Open the preconfigured Elyra pipeline `offline-scoring/offline-scoring.pipeline`. It consists of the same code that you have executed through the notebook, but now the individual steps are defined as part of a workflow. Click `Run Pipeline`. You are able to edit the values of two parameters with which to customize your scoring run:
- `data_object_name`: The object name of your serialized "live" data in the connected S3 bucket.
- `model_object_name`: Identifier of the loaded model artifact.

Click `OK` to submit the pipeline to Data Science Pipelines. You should see the confirmation message _Job submission to Kubeflow Pipelines succeeded_.

In the RHODS dashboard, navigate to `Data Science Pipelines` -> `Runs` -> `Triggered`. Ensure your current Project is selected. Select the top run that starts with `offline-scoring-`. You can now observe the execution of the offline scoring pipeline in realtime.

In the connected S3 bucket, you will see the prediction results as before. In the Elyra bucket, you will see a new folder with the run identifier starting with `offline-scoring-`. This folder contains the file dependencies, log output, and produced artifacts of each pipeline task.

### Online Scoring

In the RHOAI dashboard, navigate to project `fraud-detection`. Under `Models and model server`, select `Deploy model` under `OVMS`:
- give the deployed model a name,
- select as model framework `onnx`,
- as the existing data connection, select `fraud-detection`,
- under path enter `model-latest.onnx`,
- hit `Deploy`.

The initial instantiation of the model server might take a few minutes. Once it's running and the model is loaded, it will indicate a green status. Copy the `Inference endpoint` URL.

Within the workbench, open the `online-scoring` notebook. In the second cell, paste the inference endpoint URL of the deployed model. Run the remaining cells. You should see the model response to a sample inference request.