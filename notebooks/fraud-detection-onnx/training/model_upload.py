from datetime import datetime
from os import environ
from pickle import load

from boto3 import client
from model_registry import ModelRegistry
from model_registry.utils import s3_uri_from


model_object_prefix = environ.get('model_object_prefix', 'model')
s3_endpoint_url = environ.get('AWS_S3_ENDPOINT')
s3_access_key = environ.get('AWS_ACCESS_KEY_ID')
s3_secret_key = environ.get('AWS_SECRET_ACCESS_KEY')
s3_bucket_name = environ.get('AWS_S3_BUCKET')
s3_region = environ.get('AWS_DEFAULT_REGION', 'None')
s3_secret_name = 'aws-connection-fraud-detection'
epoch_count = environ.get('epoch_count', '20')
learning_rate = environ.get('learning_rate', '0.001')
model_registry_endpoint_url_env = environ.get('MODEL_REGISTRY_ENDPOINT_URL')
registry_user = environ.get('registry_user', 'workbench')


def upload_model(
        model_object_prefix='model', model_registry_endpoint_url=''):

    s3_client = _initialize_s3_client(
        s3_endpoint_url=s3_endpoint_url,
        s3_access_key=s3_access_key,
        s3_secret_key=s3_secret_key
    )
    model_version = _timestamp()
    model_object_name = f'models/{model_object_prefix}-{model_version}.onnx'
    _do_upload(s3_client, model_object_name)

    model_registry_endpoint_url = (
        model_registry_endpoint_url_env or model_registry_endpoint_url
    )
    if model_registry_endpoint_url:
        _register_model_version(
            model_object_name, model_version, model_registry_endpoint_url
        )
    else:
        print('no model registry endpoint URL found. skipping model registration.')


def _initialize_s3_client(s3_endpoint_url, s3_access_key, s3_secret_key):
    print('initializing S3 client')
    s3_client = client(
        's3', aws_access_key_id=s3_access_key,
        aws_secret_access_key=s3_secret_key,
        endpoint_url=s3_endpoint_url,
    )
    return s3_client


def _timestamp():
    return datetime.now().strftime('%y%m%d%H%M')


def _do_upload(s3_client, object_name):
    print(f'uploading model to {object_name}')
    try:
        s3_client.upload_file('model.onnx', s3_bucket_name, object_name)
    except Exception:
        print(f'S3 upload to bucket {s3_bucket_name} at {s3_endpoint_url} failed!')
        raise
    print(f'model uploaded and available as "{object_name}"')


def _register_model_version(
        model_object_name, version, model_registry_endpoint_url):

    print(f'registering model version {version}')
    registry = _instantiate_model_registry(model_registry_endpoint_url)
    training_metrics = _load_training_metrics()

    model_description = '''
    Shallow neural network trained on Credit Card Fraud Detector dataset 
    (https://www.kaggle.com/code/janiobachmann/credit-fraud-dealing-with-imbalanced-datasets).\n
    Deployed model expects input vector of shape [1, 30] with FP32-type values, 
    returns vector of shape [1, 2] with FP32-type values denoting predicted 
    probabilities for non-fraud / fraud. See sample:
    https://github.com/mamurak/os-mlops/blob/main/notebooks/fraud-detection-onnx/online-scoring.ipynb
    '''
    s3_uri = s3_uri_from(
        path=model_object_name,
        bucket=s3_bucket_name,
        endpoint=s3_endpoint_url,
        region=s3_region,
    )
    registry.register_model(
        'fraud-detection',
        uri=s3_uri,
        version=version,
        description=model_description,
        model_format_name='onnx',
        model_format_version='1',
        storage_key=s3_secret_name,
        metadata={
            'accuracy': str(training_metrics['accuracy'][-1]),
            'epoch_count': epoch_count,
            'learning_rate': learning_rate,
            'fraud-detection': '',
            'onnx': '',
        }
    )
    print('model registration complete.')


def _instantiate_model_registry(model_registry_endpoint_url):
    sa_token_file_path = '/var/run/secrets/kubernetes.io/serviceaccount/token'
    with open(sa_token_file_path, 'r') as token_file:
        auth_token = token_file.read()

    registry = ModelRegistry(
        server_address=model_registry_endpoint_url,
        author=registry_user,
        user_token=auth_token,
    )
    return registry


def _load_training_metrics():
    metrics_file_path = 'metrics.pickle'
    with open(metrics_file_path, 'rb') as inputfile:
        training_metrics = load(inputfile)
    return training_metrics


if __name__ == '__main__':
    upload_model(model_object_prefix)
