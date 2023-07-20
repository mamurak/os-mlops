from os import environ, path

from boto3 import client


def ingest_data(bucket_name='', data_folder='./data'):
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

    paginator = s3_client.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=s3_bucket_name)

    for page in pages:
        for obj in page.get('Contents', []):
            key = obj['Key']
            if key.endswith('.jpg'):
                local_file_path = path.join(data_folder, key)

                print(f'Downloading {key} to {local_file_path}')
                s3_client.download_file(
                    s3_bucket_name, key, local_file_path
                )

    print('Finished data ingestion.')


if __name__ == '__main__':
    ingest_data(data_folder='/data')
