from os import environ

import boto3


def ingest_data(data_object_name='', data_folder='./data'):
    print('Commencing data ingestion.')

    s3_endpoint_url = environ.get('AWS_S3_ENDPOINT')
    s3_access_key = environ.get('AWS_ACCESS_KEY_ID')
    s3_secret_key = environ.get('AWS_SECRET_ACCESS_KEY')
    s3_bucket_name = environ.get('AWS_S3_BUCKET')
    data_object_name = data_object_name or environ.get(
        'data_object_name'
    )

    print(f'Downloading data "{data_object_name}" '
          f'from bucket "{s3_bucket_name}" '
          f'from S3 storage at {s3_endpoint_url}')

    s3_client = boto3.client(
        's3', endpoint_url=s3_endpoint_url,
        aws_access_key_id=s3_access_key, aws_secret_access_key=s3_secret_key
    )

    s3_client.download_file(
        s3_bucket_name,
        data_object_name,
        f'{data_folder}/data.csv'
    )
    print('Finished data ingestion.')


if __name__ == '__main__':
    ingest_data(data_folder='/data')
