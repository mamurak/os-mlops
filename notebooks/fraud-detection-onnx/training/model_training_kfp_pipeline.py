from kfp.components import create_component_from_func
from kfp.dsl import pipeline
from kfp_tekton import TektonClient
from kubernetes.client import V1Volume, V1PersistentVolumeClaimVolumeSource, \
    V1EnvVar, V1EnvVarSource, V1SecretKeySelector


runtime_image = 'quay.io/mmurakam/runtimes:fraud-detection-v0.1.0'


def data_ingestion(data_object_name: str):
    from os import environ

    import boto3

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

    s3_client = boto3.client(
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
    from imblearn.over_sampling import SMOTE
    from numpy import save
    from pandas import read_csv
    from sklearn.model_selection import StratifiedKFold
    from sklearn.preprocessing import RobustScaler

    print('Preprocessing data.')

    raw_data_file_location = '/data/raw_data.csv'
    training_data_folder = '/data'
    df = read_csv(raw_data_file_location)

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

    X = df.drop('Class', axis=1)
    y = df['Class']
    sss = StratifiedKFold(n_splits=5, random_state=None, shuffle=False)

    for train_index, test_index in sss.split(X, y):
        print("Train:", train_index, "Test:", test_index)
        original_Xtrain = X.iloc[train_index]
        original_ytrain = y.iloc[train_index]

    original_Xtrain = original_Xtrain.values
    original_ytrain = original_ytrain.values

    sm = SMOTE(sampling_strategy='minority', random_state=42)
    Xsm_train, ysm_train = sm.fit_resample(original_Xtrain, original_ytrain)

    save(f'{training_data_folder}/training_samples.npy', Xsm_train)
    save(f'{training_data_folder}/training_labels.npy', ysm_train)

    print('data processing done')


def model_training(epoch_count: int, learning_rate: float):
    from os import environ

    environ['CUDA_VISIBLE_DEVICES'] = '-1'

    from keras.models import Sequential
    from keras.layers.core import Dense
    from keras.optimizers import Adam
    from numpy import load
    from onnx import save
    from tf2onnx import convert

    print('training model')

    Xsm_train = load('/data/training_samples.npy')
    ysm_train = load('/data/training_labels.npy')
    n_inputs = Xsm_train.shape[1]

    oversample_model = Sequential([
        Dense(n_inputs, input_shape=(n_inputs, ), activation='relu'),
        Dense(32, activation='relu'),
        Dense(2, activation='softmax'),
    ])
    oversample_model.compile(
        Adam(learning_rate=learning_rate),
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy'],
    )
    oversample_model.fit(
        Xsm_train,
        ysm_train,
        validation_split=0.2,
        batch_size=300,
        epochs=epoch_count,
        shuffle=True,
        verbose=2,
    )
    onnx_model, _ = convert.from_keras(oversample_model)
    save(onnx_model, '/data/model.onnx')


def model_validation():
    from time import sleep

    print('validating model using group fairness scores, for instance')
    sleep(1)
    print('model validated')


def model_upload(model_object_prefix: str):
    from os import environ
    from datetime import datetime

    from boto3 import client

    def _initialize_s3_client(s3_endpoint_url, s3_access_key, s3_secret_key):
        print('initializing S3 client')
        s3_client = client(
            's3', aws_access_key_id=s3_access_key,
            aws_secret_access_key=s3_secret_key,
            endpoint_url=s3_endpoint_url,
        )
        return s3_client

    def _generate_model_name(model_object_prefix, version=''):
        version = version if version else _timestamp()
        model_name = f'{model_object_prefix}-{version}.onnx'
        return model_name

    def _timestamp():
        return datetime.now().strftime('%y%m%d%H%M')

    def _do_upload(s3_client, object_name):
        print(f'uploading model to {object_name}')
        try:
            s3_client.upload_file('/data/model.onnx', s3_bucket_name, object_name)
        except:
            print(f'S3 upload to bucket {s3_bucket_name} at {s3_endpoint_url} failed!')
            raise
        print(f'model uploaded and available as "{object_name}"')

    s3_endpoint_url = environ.get('AWS_S3_ENDPOINT')
    s3_access_key = environ.get('AWS_ACCESS_KEY_ID')
    s3_secret_key = environ.get('AWS_SECRET_ACCESS_KEY')
    s3_bucket_name = environ.get('AWS_S3_BUCKET')

    s3_client = _initialize_s3_client(
        s3_endpoint_url=s3_endpoint_url,
        s3_access_key=s3_access_key,
        s3_secret_key=s3_secret_key
    )
    model_object_name = _generate_model_name(model_object_prefix)
    _do_upload(s3_client, model_object_name)

    model_object_name_latest = _generate_model_name(
        model_object_prefix, 'latest'
    )
    _do_upload(s3_client, model_object_name_latest)


data_ingestion_op = create_component_from_func(
    data_ingestion, base_image=runtime_image
)
preprocessing_op = create_component_from_func(
    preprocessing, base_image=runtime_image
)
model_training_op = create_component_from_func(
    model_training, base_image=runtime_image
)
model_validation_op = create_component_from_func(
    model_validation, base_image=runtime_image
)
model_upload_op = create_component_from_func(
    model_upload, base_image=runtime_image
)


@pipeline(name='model-training-kfp')
def model_training_pipeline(
    data_object_name: str = 'training-data.csv',
    epoch_count: int = 20,
    learning_rate: float = 0.001,
    model_object_prefix: str = 'model'
        ):

    data_volume = V1Volume(
        name='model-training-data-volume',
        persistent_volume_claim=V1PersistentVolumeClaimVolumeSource(
            claim_name='model-training-data-volume'
        )
    )

    data_ingestion_task = data_ingestion_op(data_object_name)
    data_ingestion_task.add_pvolumes({'/data': data_volume})
    data_ingestion_task.add_env_variable(
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
    data_ingestion_task.add_env_variable(
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
    data_ingestion_task.add_env_variable(
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
    data_ingestion_task.add_env_variable(
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

    preprocessing_task = preprocessing_op()
    preprocessing_task.add_pvolumes({'/data': data_volume})
    preprocessing_task.after(data_ingestion_task)

    model_training_task = model_training_op(
        epoch_count, learning_rate
    )
    model_training_task.add_pvolumes({'/data': data_volume})
    model_training_task.after(preprocessing_task)

    model_validation_task = model_validation_op()
    model_validation_task.add_pvolumes({'/data': data_volume})
    model_validation_task.after(model_training_task)

    model_upload_task = model_upload_op(model_object_prefix)
    model_upload_task.add_pvolumes({'/data': data_volume})
    model_upload_task.add_env_variable(
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
    model_upload_task.add_env_variable(
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
    model_upload_task.add_env_variable(
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
    model_upload_task.add_env_variable(
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
    model_upload_task.after(model_validation_task)


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
        model_training_pipeline,
        arguments={},
        experiment_name='model_training-kfp'
    )
    print(f'Starting pipeline run with run_id: {result.run_id}')
