from kfp.dsl import Artifact,component, Dataset, Input, Output, pipeline
from kfp.kubernetes import use_secret_as_env

from kfp_client import KfpPipeline


data_connection_secret_name = 'aws-connection-fraud-detection'
runtime_image = 'quay.io/mmurakam/runtimes:fraud-detection-v2.6.1'


@component(base_image=runtime_image)
def ingest_data(input_bucket_folder: str, output_dir: Output[Artifact]):
    from os import environ, makedirs, path

    from boto3 import client

    print('Commencing data ingestion.')

    s3_endpoint_url = environ.get('AWS_S3_ENDPOINT')
    s3_access_key = environ.get('AWS_ACCESS_KEY_ID')
    s3_secret_key = environ.get('AWS_SECRET_ACCESS_KEY')
    s3_bucket_name = environ.get('AWS_S3_BUCKET')

    print(f'Downloading data from bucket "{s3_bucket_name}" '
          f'from S3 storage at {s3_endpoint_url}')

    s3_client = client(
        's3', endpoint_url=s3_endpoint_url,
        aws_access_key_id=s3_access_key, aws_secret_access_key=s3_secret_key
    )

    makedirs(output_dir.path, exist_ok=True)
    paginator = s3_client.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=s3_bucket_name)

    for page in pages:
        for obj in page.get('Contents', []):
            key = obj['Key']
            if key.startswith(input_bucket_folder):
                local_file_path = path.join(output_dir.path, key.split('/')[-1])

                print(f'Downloading {key} to {local_file_path}')
                s3_client.download_file(
                    s3_bucket_name, key, local_file_path
                )

    print('Finished data ingestion.')


@component(base_image=runtime_image)
def upload_data(output_bucket_folder: str, input_dir:Input[Artifact]):
    from pathlib import Path
    from os import environ

    from boto3 import client

    print('Commencing data upload.')

    s3_endpoint_url = environ.get('AWS_S3_ENDPOINT')
    s3_access_key = environ.get('AWS_ACCESS_KEY_ID')
    s3_secret_key = environ.get('AWS_SECRET_ACCESS_KEY')
    s3_bucket_name = environ.get('AWS_S3_BUCKET')

    print(f'Uploading data to bucket "{s3_bucket_name}" '
          f'from S3 storage at {s3_endpoint_url}')

    s3_client = client(
        's3', endpoint_url=s3_endpoint_url,
        aws_access_key_id=s3_access_key, aws_secret_access_key=s3_secret_key
    )

    dir_path = Path(input_dir.path)
    files = [file for file in dir_path.glob('*') if file.is_file()]

    for file in files:
        print(f'Uploading {file.name} to {output_bucket_folder}')
        with open(file, 'rb') as upload_file:
            s3_client.upload_fileobj(
                upload_file, s3_bucket_name, f'{output_bucket_folder}/{file.name}'
            )

    print('Finished data upload.')


@pipeline(name='copy-pipeline')
def copy_pipeline(
        input_bucket_folder: str = 'data',
        output_bucket_folder: str='output'):

    data_ingestion_task = ingest_data(
        input_bucket_folder=input_bucket_folder
    )
    use_secret_as_env(
        data_ingestion_task,
        secret_name=data_connection_secret_name,
        secret_key_to_env={
            'AWS_S3_ENDPOINT': 'AWS_S3_ENDPOINT',
            'AWS_ACCESS_KEY_ID': 'AWS_ACCESS_KEY_ID',
            'AWS_SECRET_ACCESS_KEY': 'AWS_SECRET_ACCESS_KEY',
            'AWS_S3_BUCKET': 'AWS_S3_BUCKET',
        },
    )
    data_ingestion_task.set_caching_options(False)

    # Resource assignment

    data_ingestion_task.set_cpu_request('200m')
    data_ingestion_task.set_cpu_limit('600m')
    data_ingestion_task.set_memory_request('70Mi')
    data_ingestion_task.set_memory_limit('600Mi')
    # data_ingestion_task.set_accelerator_type('nvidia.com/gpu')
    # data_ingestion_task.set_accelerator_limit(1)

    data_upload_task = upload_data(
        output_bucket_folder=output_bucket_folder,
        input_dir=data_ingestion_task.output,
    )
    use_secret_as_env(
        data_upload_task,
        secret_name=data_connection_secret_name,
        secret_key_to_env={
            'AWS_S3_ENDPOINT': 'AWS_S3_ENDPOINT',
            'AWS_ACCESS_KEY_ID': 'AWS_ACCESS_KEY_ID',
            'AWS_SECRET_ACCESS_KEY': 'AWS_SECRET_ACCESS_KEY',
            'AWS_S3_BUCKET': 'AWS_S3_BUCKET',
            'AWS_DEFAULT_REGION': 'AWS_DEFAULT_REGION',
        },
    )


def run_experiment():
    uploaded_pipeline = KfpPipeline(
        copy_pipeline, 'copy-pipeline'
    )
    uploaded_pipeline.run_with_parameters(
        pipeline_parameters={
            'input_bucket_folder': 'data',
            'output_bucket_folder': 'output'
        },
        experiment_name='copy-pipeline'
    )


if __name__ == '__main__':
    run_experiment()