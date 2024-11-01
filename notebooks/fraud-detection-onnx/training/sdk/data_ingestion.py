from kfp.dsl import component, Dataset, Output


runtime_image = 'quay.io/mmurakam/runtimes:fraud-detection-v2.3.3'


@component(base_image=runtime_image)
def ingest_data(data_object_name: str, raw_data: Output[Dataset]):
    from os import environ

    import boto3

    print('Commencing data ingestion.')

    s3_endpoint_url = environ.get('AWS_S3_ENDPOINT')
    s3_access_key = environ.get('AWS_ACCESS_KEY_ID')
    s3_secret_key = environ.get('AWS_SECRET_ACCESS_KEY')
    s3_bucket_name = environ.get('AWS_S3_BUCKET')

    print(f'Downloading data "{data_object_name}" '
          f'from bucket "{s3_bucket_name}" '
          f'from S3 storage at {s3_endpoint_url}'
          f'to {raw_data.path}')

    s3_client = boto3.client(
        's3', endpoint_url=s3_endpoint_url,
        aws_access_key_id=s3_access_key, aws_secret_access_key=s3_secret_key
    )
    s3_client.download_file(
        s3_bucket_name,
        f'data/{data_object_name}',
        raw_data.path
    )
    print('Finished data ingestion.')