from os import environ, path, walk
from shutil import rmtree

from boto3 import client
from transformers import AutoTokenizer, AutoModel


hf_repo_id_env = environ.get('hf-repo-id')
s3_endpoint_url = environ.get('AWS_S3_ENDPOINT')
s3_access_key = environ.get('AWS_ACCESS_KEY_ID')
s3_secret_key = environ.get('AWS_SECRET_ACCESS_KEY')
s3_bucket_name = environ.get('AWS_S3_BUCKET')
s3_client = client(
    's3', endpoint_url=s3_endpoint_url,
    aws_access_key_id=s3_access_key, aws_secret_access_key=s3_secret_key
)


def transfer_artifacts(hf_repo_id=''):
    hf_repo_id = hf_repo_id or hf_repo_id_env
    artifacts = _download_from_hf(hf_repo_id)
    _store_locally(artifacts, hf_repo_id)
    _upload(hf_repo_id)
    _clean_up(hf_repo_id)
    print(f'Transferring model artifacts from {hf_repo_id} to S3 complete.')


def _download_from_hf(hf_repo_id):
    print(f'Downloading artifacts from {hf_repo_id}.')
    model = AutoModel.from_pretrained(hf_repo_id)
    tokenizer = AutoTokenizer.from_pretrained(hf_repo_id)
    return model, tokenizer


def _store_locally(artifacts, folder_name):
    print('Serializing artifacts.')
    model, tokenizer = artifacts
    model.save_pretrained(folder_name)
    tokenizer.save_pretrained(folder_name)


def _upload(folder_name):
    print('Commencing upload.')
    print(f'Uploading artifacts in {folder_name} to bucket {s3_bucket_name} '
          f'to S3 storage at {s3_endpoint_url}')

    for root, dirs, files in walk(folder_name):
        for filename in files:
            local_path = path.join(root, filename)

            relative_path = path.relpath(local_path, folder_name)
            s3_path = path.join(folder_name, relative_path)

            s3_client.upload_file(local_path, s3_bucket_name, s3_path)
            print(f"File {local_path} uploaded to {s3_path}")

    print('Finished uploading objects.')


def _clean_up(folder_name):
    print(f'Removing folder {folder_name}.')
    rmtree(folder_name)


if __name__ == '__main__':
    load_from_hf_to_s3()