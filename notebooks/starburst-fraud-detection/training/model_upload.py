from os import environ
from datetime import datetime

from boto3 import client


model_object_prefix = environ.get('model_object_prefix', 'model')
s3_endpoint_url = environ.get('AWS_S3_ENDPOINT')
s3_access_key = environ.get('AWS_ACCESS_KEY_ID')
s3_secret_key = environ.get('AWS_SECRET_ACCESS_KEY')
s3_bucket_name = environ.get('AWS_S3_BUCKET')


def upload_model(model_object_prefix='model', version=''):
    s3_client = _initialize_s3_client(
        s3_endpoint_url=s3_endpoint_url,
        s3_access_key=s3_access_key,
        s3_secret_key=s3_secret_key
    )
    model_object_name = _generate_model_name(
        model_object_prefix, version=version
    )
    _do_upload(s3_client, model_object_name)

    model_object_name_latest = _generate_model_name(
        model_object_prefix, 'latest'
    )
    _do_upload(s3_client, model_object_name_latest)


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
        s3_client.upload_file('model.onnx', s3_bucket_name, object_name)
    except:
        print(f'S3 upload to bucket {s3_bucket_name} at {s3_endpoint_url} failed!')
        raise
    print(f'model uploaded and available as "{object_name}"')


if __name__ == '__main__':
    upload_model(model_object_prefix)
