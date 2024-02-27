from os import environ

from boto3 import client


def load_model(model_file_name=''):
    print('Commencing model loading.')

    s3_endpoint_url = environ.get('S3_ENDPOINT_URL')
    s3_access_key = environ.get('S3_ACCESS_KEY_ID')
    s3_secret_key = environ.get('S3_SECRET_ACCESS_KEY')
    s3_bucket_name = environ.get('S3_BUCKET')
    model_object_name = model_file_name or environ.get('model_object_name')

    print(f'Downloading model "{model_object_name}" '
          f'from bucket {s3_bucket_name} '
          f'from S3 storage at {s3_endpoint_url}')

    s3_client = client(
        's3', endpoint_url=s3_endpoint_url,
        aws_access_key_id=s3_access_key, aws_secret_access_key=s3_secret_key
    )

    s3_client.download_file(
        s3_bucket_name, model_object_name, 'model.joblib'
    )

    print('Finished model loading.')


if __name__ == '__main__':
    load_model()
