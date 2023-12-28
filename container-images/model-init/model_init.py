from tempfile import NamedTemporaryFile
from os import environ

from kubernetes import client, config, utils
from minio import Minio
from requests import get


model_url = environ.get(
    'MODEL_URL',
    'https://github.com/mamurak/os-mlops-artefacts/blob/'
    'object-detection-model-v0.1/models/object-detection/yolov5m.onnx'
)
chunk_size = int(environ.get('CHUNK_SIZE', '128'))
minio_host = environ.get('MINIO_HOST', 'minio-service.minio.svc:9000')
access_key = environ.get('ACCESS_KEY', 'minio')
secret_key = environ.get('SECRET_KEY', 'minio123')
bucket_name = environ.get('BUCKET_NAME', 'models')
model_object_name = environ.get('MODEL_OBJECT_NAME', 'model.onnx')
manifest_location = 'inference-service.yaml'


def main():
    model_filename = _download(model_url, chunk_size)
    _upload_to_s3(bucket_name, model_object_name, model_filename)
    _apply_manifest(manifest_location)


def _download(url, chunk_size=128):
    print(f'Downloading model from {url} with chunk size {chunk_size}')
    model_file = NamedTemporaryFile(delete=False)
    download = get(url, stream=True)
    with open(model_file.name, 'wb') as outputfile:
        for chunk in download.iter_content(chunk_size=chunk_size):
            outputfile.write(chunk)
    print(f'Wrote model to {model_file.name}')
    return model_file.name


def _upload_to_s3(bucket_name, object_name, filename):
    print(f'Uploading model from {filename} to {object_name} '
          f'in bucket {bucket_name}')
    minio_client = Minio(minio_host, access_key, secret_key)
    minio_client.fput_object(bucket_name, object_name, filename)
    print('Upload complete')


def _apply_manifest(manifest_location):
    print(f'Applying manifest {manifest_location}')
    config.load_kube_config()
    k8s_client = client.ApiClient()
    utils.create_from_yaml(k8s_client, manifest_location, verbose=True)
    print('Applied manifest')


if __name__ == '__main__':
    main()