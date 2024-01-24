from pprint import pformat
from time import sleep

from kubernetes.client.api_client import ApiClient
from kubernetes.config import load_incluster_config
from kubernetes.dynamic import DynamicClient
from kubernetes.dynamic.exceptions import NotFoundError


namespace = 'user2'
sleep_time = 5
access_key = 'AWS_ACCESS_KEY_ID'
secret_key = 'AWS_SECRET_ACCESS_KEY'
source_secret_name = 'pipeline-bucket'
target_secret_name = 'aws-connection-pipelines2'

load_incluster_config()
k8s_client = DynamicClient(ApiClient())
secret_api = k8s_client.resources.get(api_version='v1', kind='Secret')


def transfer_s3_credentials(
        source_secret_name, target_secret_name, namespace, sleep_time=5):

    print(f'Transfering S3 credentials from {source_secret_name} to '
          f'{target_secret_name} in namespace {namespace}')
    access_key_id, secret_key_id = _read_s3_credentials(
        source_secret_name, namespace, sleep_time
    )
    _write_s3_to_target(
        access_key_id, secret_key_id, target_secret_name, namespace
    )


def _read_s3_credentials(source_secret_name, namespace, sleep_time=5):

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

    access_key_id = pipeline_bucket_secret['data'][access_key]
    secret_key_id = pipeline_bucket_secret['data'][secret_key]

    return access_key_id, secret_key_id


def _write_s3_to_target(
        access_key_id, secret_key_id, target_secret_name, namespace):

    print(f'Writing S3 credentials to secret {target_secret_name} '
          f'in namespace {namespace}')
    target_secret_patch = {
        'apiVersion': 'v1',
        'kind': 'Secret',
        'metadata': {
            'name': target_secret_name,
            'namespace': namespace,
        },
        'data': {
            access_key: access_key_id,
            secret_key: secret_key_id,
        }
    }
    target_secret = secret_api.patch(
        body=target_secret_patch,
        content_type='application/merge-patch+json'
    )
    print(f'Patched secret. Current state: {pformat(target_secret)}')


if __name__ == '__main__':
    transfer_s3_credentials(
        source_secret_name, target_secret_name, namespace, sleep_time
    )