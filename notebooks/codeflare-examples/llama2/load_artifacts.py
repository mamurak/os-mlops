from os import environ, listdir, path, unlink
from shutil import rmtree

from boto3 import client


s3_endpoint_url = environ.get('S3_ENDPOINT')
s3_access_key = environ.get('S3_ACCESS_KEY_ID')
s3_secret_key = environ.get('S3_SECRET_ACCESS_KEY')
s3_bucket_name = environ.get('S3_BUCKET')

models_cache_folder = '/models'
model_id = environ.get('hf_model_id', 'Trelis/Llama-2-7b-chat-hf-sharded-bf16')


def load_artifacts():
    _clean_folder(models_cache_folder)
    s3_client = client(
        's3', endpoint_url=s3_endpoint_url,
        aws_access_key_id=s3_access_key, aws_secret_access_key=s3_secret_key
    )
    paginator = s3_client.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=s3_bucket_name)

    for page in pages:
        for obj in page.get('Contents', []):
            key = obj['Key']
            if model_id in key:
                local_file_path = path.join(
                    models_cache_folder, key.split('/')[-1]
                )

                print(f'Downloading {key} to {local_file_path}')
                s3_client.download_file(
                    s3_bucket_name, key, local_file_path
                )


def _clean_folder(folder):
    print(f'Cleaning folder {folder}')

    for filename in listdir(folder):
        file_path = path.join(folder, filename)
        try:
            if path.isfile(file_path) or path.islink(file_path):
                unlink(file_path)
            elif path.isdir(file_path):
                rmtree(file_path)
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')


if __name__ == '__main__':
    load_artifacts()