from os import environ, path, walk

from boto3 import client


models_cache_folder = '/models'
s3_endpoint_url = environ.get('S3_ENDPOINT')
s3_access_key = environ.get('S3_ACCESS_KEY_ID')
s3_secret_key = environ.get('S3_SECRET_ACCESS_KEY')
s3_bucket_name = environ.get('S3_BUCKET')
s3_client = client(
    's3', endpoint_url=s3_endpoint_url,
    aws_access_key_id=s3_access_key, aws_secret_access_key=s3_secret_key
)


def upload_artifacts():
    print('Commencing upload.')
    print(f'Uploading artifacts in {models_cache_folder} '
          f'to bucket {s3_bucket_name} '
          f'to S3 storage at {s3_endpoint_url}')

    for root, dirs, files in walk(models_cache_folder):
        for filename in files:
            local_path = path.join(root, filename)

            relative_path = path.relpath(local_path, models_cache_folder)
            s3_path = path.join(models_cache_folder, relative_path)

            s3_client.upload_file(local_path, s3_bucket_name, s3_path)
            print(f"File {local_path} uploaded to {s3_path}")

    print('Finished uploading objects.')


if __name__ == '__main__':
    upload_artifacts()