from os import environ

import boto3


def ingest_data(data_object_name=''):
    print('Commencing data ingestion.')

    s3_endpoint_url = environ.get('S3_ENDPOINT_URL')
    s3_access_key = environ.get('S3_ACCESS_KEY_ID')
    s3_secret_key = environ.get('S3_SECRET_ACCESS_KEY')
    s3_bucket_name = environ.get('S3_BUCKET_NAME')
    data_object_name = data_object_name or environ.get(
        'data_object_name', 'raw-data.csv'
    )

    print(f'Downloading data "{data_object_name}" '
          f'from bucket "{s3_bucket_name}" '
          f'from S3 storage at {s3_endpoint_url}')

    s3_client = boto3.client(
        's3', endpoint_url=s3_endpoint_url,
        aws_access_key_id=s3_access_key, aws_secret_access_key=s3_secret_key
    )

    s3_client.download_file(
        s3_bucket_name, data_object_name, 'raw-data.csv'
    )
    print('Finished data ingestion.')


if __name__ == '__main__':
    ingest_data()
