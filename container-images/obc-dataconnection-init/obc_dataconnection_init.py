from os import environ
from pprint import pformat
from time import sleep

from kubernetes.client.api_client import ApiClient
from kubernetes.config import load_incluster_config
from kubernetes.dynamic import DynamicClient
from kubernetes.dynamic.exceptions import NotFoundError


namespace = environ('NAMESPACE')
sleep_time = int(environ('SLEEP_TIME', '5'))
access_key_name = 'AWS_ACCESS_KEY_ID'
secret_key_name = 'AWS_SECRET_ACCESS_KEY'
source_secret_name = environ('SOURCE_SECRET_NAME')
target_secret_name = environ('TARGET_SECRET_NAME')
bucket_name = environ('BUCKET_NAME')

load_incluster_config()
k8s_client = DynamicClient(ApiClient())
secret_api = k8s_client.resources.get(api_version='v1', kind='Secret')


def transfer_s3_credentials():
    print(f'Transfering S3 credentials from {source_secret_name} to '
          f'{target_secret_name} in namespace {namespace}')
    s3_credentials = _read_s3_credentials(
        source_secret_name, namespace
    )
    data_connection_definition = _generate_data_connection(*s3_credentials)
    _deploy(data_connection_definition)


def _read_s3_credentials(source_secret_name, namespace):

    print(f'Reading secret {source_secret_name} in namespace {namespace}')
    source_secret_exists = False
    while not source_secret_exists:
        try:
            pipeline_bucket_secret = secret_api.get(
                name=source_secret_name, namespace=namespace
            )
            print(
                f'Found pipeline bucket secret: {pformat(pipeline_bucket_secret)}'
            )
            source_secret_exists = True
        except NotFoundError:
            print(
                f'Secret {source_secret_name} not found.'
                f'Retrying in {sleep_time} seconds.'
            )
            sleep(sleep_time)

    access_key_id = pipeline_bucket_secret['data'][access_key_name]
    secret_key_id = pipeline_bucket_secret['data'][secret_key_name]

    return access_key_id, secret_key_id


def _generate_data_connection(access_key_id, secret_key_id):
    data_connection_definition = {
        'apiVersion': 'v1',
        'kind': 'Secret',
        'metadata': {
            'name': target_secret_name,
            'namespace': namespace,
            'labels': {
                'opendatahub.io/dashboard': 'true',
                'opendatahub.io/managed': 'true',
            },
            'annotations': {
                'opendatahub.io/connection-type': 's3',
            },
        },
        'stringData': {
            access_key_name: access_key_id,
            secret_key_name: secret_key_id,
            'AWS_S3_BUCKET': bucket_name,
            'AWS_S3_ENDPOINT': 'http://s3.openshift-storage.svc',
            'AWS_DEFAULT_REGION': 'none',
        }
    }
    return data_connection_definition


def _deploy(data_connection_definition):

    print(f'Writing S3 credentials to secret {target_secret_name} '
          f'in namespace {namespace}')
    target_secret = secret_api.create(
        body=data_connection_definition,
        namespace=namespace,
    )
    print(f'Patched secret. Current state: {pformat(target_secret)}')


if __name__ == '__main__':
    transfer_s3_credentials()