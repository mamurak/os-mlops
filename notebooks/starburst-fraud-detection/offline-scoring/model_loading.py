from os import environ

from boto3 import client


def load_model(bucket_name='', model_file_name=''):
    print('Commencing model loading.')

    s3_endpoint_url = environ.get('S3_ENDPOINT_URL')
    s3_access_key = environ.get('S3_ACCESS_KEY')
    s3_secret_key = environ.get('S3_SECRET_KEY')
    s3_bucket_name = bucket_name or environ.get('S3_BUCKET_NAME')
    model_file_name = model_file_name or environ.get('MODEL_FILE_NAME')

    print(f'Downloading model from bucket {s3_bucket_name} '
          f'from S3 storage at {s3_endpoint_url}')

    s3_client = client(
        's3', endpoint_url=s3_endpoint_url,
        aws_access_key_id=s3_access_key, aws_secret_access_key=s3_secret_key
    )

    s3_client.download_file(
        s3_bucket_name, model_file_name, 'model.bst'
    )

    print('Finished model loading.')


if __name__ == '__main__':
    load_model()
