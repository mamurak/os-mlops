from os import environ
from typing import NamedTuple

from kfp.components import create_component_from_func, InputPath, OutputPath
from kfp.dsl import pipeline
from kfp_tekton import TektonClient
from kubernetes.client import V1Volume, V1PersistentVolumeClaimVolumeSource, \
    V1EnvVar, V1EnvVarSource, V1SecretKeySelector


environ['DEFAULT_ACCESSMODES'] = 'ReadWriteOnce'
environ['DEFAULT_STORAGE_SIZE'] = '2Gi'
environ['DEFAULT_STORAGE_CLASS'] = 'gp3-csi'
runtime_image = 'quay.io/mmurakam/runtimes:fraud-detection-v0.2.0'


def data_ingestion(data_object_name: str):
    from os import environ

    from boto3 import client

    raw_data_file_location = '/data/raw_data.csv'

    print('Commencing data ingestion.')

    s3_endpoint_url = environ.get('AWS_S3_ENDPOINT')
    s3_access_key = environ.get('AWS_ACCESS_KEY_ID')
    s3_secret_key = environ.get('AWS_SECRET_ACCESS_KEY')
    s3_bucket_name = environ.get('AWS_S3_BUCKET')

    print(f'Downloading data "{data_object_name}" '
        f'from bucket "{s3_bucket_name}" '
        f'from S3 storage at {s3_endpoint_url}'
        f'to {raw_data_file_location}')

    s3_client = client(
        's3', endpoint_url=s3_endpoint_url,
        aws_access_key_id=s3_access_key, aws_secret_access_key=s3_secret_key
    )

    s3_client.download_file(
        s3_bucket_name,
        data_object_name,
        raw_data_file_location
    )
    print('Finished data ingestion.')


def preprocessing():
    from numpy import save
    from pandas import read_csv
    from sklearn.preprocessing import RobustScaler


    print('Preprocessing data.')

    raw_data_file_location = '/data/raw_data.csv'
    features_file_location = '/data/features.npy'
    df = read_csv(raw_data_file_location, index_col=0)

    rob_scaler = RobustScaler()

    df['scaled_amount'] = rob_scaler.fit_transform(
        df['Amount'].values.reshape(-1, 1)
    )
    df['scaled_time'] = rob_scaler.fit_transform(
        df['Time'].values.reshape(-1, 1)
    )
    df.drop(['Time', 'Amount'], axis=1, inplace=True)
    scaled_amount = df['scaled_amount']
    scaled_time = df['scaled_time']

    df.drop(['scaled_amount', 'scaled_time'], axis=1, inplace=True)
    df.insert(0, 'scaled_amount', scaled_amount)
    df.insert(1, 'scaled_time', scaled_time)

    save(features_file_location, df.values)

    print('data processing done')


def load_model(model_object_name: str, model_path: OutputPath()):
    from os import environ

    from boto3 import client

    print('Commencing model loading.')

    s3_endpoint_url = environ.get('AWS_S3_ENDPOINT')
    s3_access_key = environ.get('AWS_ACCESS_KEY_ID')
    s3_secret_key = environ.get('AWS_SECRET_ACCESS_KEY')
    s3_bucket_name = environ.get('AWS_S3_BUCKET')

    print(f'Downloading model "{model_object_name}" '
          f'from bucket {s3_bucket_name} '
          f'from S3 storage at {s3_endpoint_url}')

    s3_client = client(
        's3', endpoint_url=s3_endpoint_url,
        aws_access_key_id=s3_access_key, aws_secret_access_key=s3_secret_key
    )

    s3_client.download_file(
        s3_bucket_name, model_object_name, model_path
    )

    print('Finished model loading.')


def predict(model_path: InputPath()):
    from numpy import argmax, array, load
    from onnxruntime import InferenceSession
    from pandas import DataFrame

    print('Commencing offline scoring.')

    X = load('/data/features.npy').astype('float32')

    session = InferenceSession(model_path)
    raw_results = session.run([], {'dense_input': X})[0]

    results = argmax(raw_results, axis=1)
    class_map_array = array(['no fraud', 'fraud'])
    mapped_results = class_map_array[results]

    print(f'Scored data set. Writing report.')

    column_names = [f'V{i}' for i in range(1, 31)]
    report = DataFrame(X, columns=column_names)
    report.insert(0, 'Prediction', mapped_results)

    report.to_csv(f'/data/predictions.csv')

    print('Wrote report. Offline scoring complete.')


def upload_results():
    from datetime import datetime
    from os import environ

    from boto3 import client

    print('Commencing results upload.')

    s3_endpoint_url = environ.get('AWS_S3_ENDPOINT')
    s3_access_key = environ.get('AWS_ACCESS_KEY_ID')
    s3_secret_key = environ.get('AWS_SECRET_ACCESS_KEY')
    s3_bucket_name = environ.get('AWS_S3_BUCKET')

    timestamp = datetime.now().strftime('%y%m%d%H%M')
    results_name = f'predictions-{timestamp}.csv'

    print(f'Uploading predictions to bucket {s3_bucket_name} '
          f'to S3 storage at {s3_endpoint_url}')

    s3_client = client(
        's3', endpoint_url=s3_endpoint_url,
        aws_access_key_id=s3_access_key, aws_secret_access_key=s3_secret_key
    )

    with open(f'/data/predictions.csv', 'rb') as results_file:
        s3_client.upload_fileobj(results_file, s3_bucket_name, results_name)

    print('Finished uploading results.')


data_ingestion_op = create_component_from_func(
    data_ingestion, base_image=runtime_image
)
preprocessing_op = create_component_from_func(
    preprocessing, base_image=runtime_image
)
load_model_op = create_component_from_func(
    load_model, base_image=runtime_image
)
predict_op = create_component_from_func(
    predict, base_image=runtime_image
)
upload_results_op = create_component_from_func(
    upload_results, base_image=runtime_image
)


@pipeline(name='offline-scoring-kfp')
def offline_scoring_pipeline(
    data_object_name: str = 'live-data.csv',
    model_object_name: str = 'model-latest.onnx'
        ):

    data_volume = V1Volume(
        name='offline-scoring-data-volume',
        persistent_volume_claim=V1PersistentVolumeClaimVolumeSource(
            claim_name='offline-scoring-data-volume'
        )
    )

    data_ingestion_task = data_ingestion_op(data_object_name)
    data_ingestion_task.add_pvolumes({'/data': data_volume})
    _mount_data_connection(data_ingestion_task)

    preprocessing_task = preprocessing_op()
    preprocessing_task.add_pvolumes({'/data': data_volume})
    preprocessing_task.after(data_ingestion_task)

    load_model_task = load_model_op(model_object_name)
    _mount_data_connection(load_model_task)

    predict_task = predict_op(model=load_model_task.outputs['model'])
    predict_task.add_pvolumes({'/data': data_volume})
    predict_task.after(preprocessing_task)
    predict_task.after(load_model_task)

    upload_results_task = upload_results_op()
    upload_results_task.add_pvolumes({'/data': data_volume})
    _mount_data_connection(upload_results_task)
    upload_results_task.after(predict_task)


def _mount_data_connection(task):
    task.add_env_variable(
        V1EnvVar(
            name='AWS_S3_ENDPOINT',
            value_from=V1EnvVarSource(
                secret_key_ref=V1SecretKeySelector(
                    name='aws-connection-fraud-detection',
                    key='AWS_S3_ENDPOINT'
                )
            )
        )
    )
    task.add_env_variable(
        V1EnvVar(
            name='AWS_ACCESS_KEY_ID',
            value_from=V1EnvVarSource(
                secret_key_ref=V1SecretKeySelector(
                    name='aws-connection-fraud-detection',
                    key='AWS_ACCESS_KEY_ID'
                )
            )
        )
    )
    task.add_env_variable(
        V1EnvVar(
            name='AWS_SECRET_ACCESS_KEY',
            value_from=V1EnvVarSource(
                secret_key_ref=V1SecretKeySelector(
                    name='aws-connection-fraud-detection',
                    key='AWS_SECRET_ACCESS_KEY'
                )
            )
        )
    )
    task.add_env_variable(
        V1EnvVar(
            name='AWS_S3_BUCKET',
            value_from=V1EnvVarSource(
                secret_key_ref=V1SecretKeySelector(
                    name='aws-connection-fraud-detection',
                    key='AWS_S3_BUCKET'
                )
            )
        )
    )


if __name__ == '__main__':
    kubeflow_endpoint = 'http://ds-pipeline-pipelines-definition:8888'
    sa_token_file_path = '/var/run/secrets/kubernetes.io/serviceaccount/token'
    with open(sa_token_file_path, 'r') as token_file:
        bearer_token = token_file.read()

    print(f'Connecting to Data Science Pipelines: {kubeflow_endpoint}')
    client = TektonClient(
        host=kubeflow_endpoint,
        existing_token=bearer_token
    )
    result = client.create_run_from_pipeline_func(
        offline_scoring_pipeline,
        arguments={},
        experiment_name='offline-scoring-kfp'
    )
    print(f'Starting pipeline run with run_id: {result.run_id}')
