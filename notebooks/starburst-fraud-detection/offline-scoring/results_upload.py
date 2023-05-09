from datetime import datetime
from os import environ

from boto3 import client


def upload_results(bucket_name='', data_folder='./data'):
    print('Commencing results upload.')

    s3_endpoint_url = environ.get('S3_ENDPOINT_URL')
    s3_access_key = environ.get('S3_ACCESS_KEY')
    s3_secret_key = environ.get('S3_SECRET_KEY')
    s3_bucket_name = bucket_name or environ.get('S3_BUCKET_NAME')

    timestamp = datetime.now().strftime('%y%m%d%H%M')
    results_name = f'predictions-{timestamp}.csv'

    print(f'Uploading predictions to bucket {s3_bucket_name} '
          f'to S3 storage at {s3_endpoint_url}')

    s3_client = client(
        's3', endpoint_url=s3_endpoint_url,
        aws_access_key_id=s3_access_key, aws_secret_access_key=s3_secret_key
    )

    with open(f'{data_folder}/predictions.csv', 'rb') as results_file:
        s3_client.upload_fileobj(results_file, s3_bucket_name, results_name)

    print('Finished uploading results.')


if __name__ == '__main__':
    upload_results(data_folder='/data')
