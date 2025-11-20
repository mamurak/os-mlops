from argparse import ArgumentParser
from asyncio import create_task
from json import dump
from os import environ
from typing import Dict, Union

from boto3 import client
from kserve import Model, ModelServer, model_server, InferRequest, InferResponse
from librosa import load
from torch import cuda
from transformers import pipeline


s3_access_key = environ.get('AWS_ACCESS_KEY_ID')
s3_secret_key = environ.get('AWS_SECRET_ACCESS_KEY')
s3_endpoint = environ.get('AWS_S3_ENDPOINT')
bucket_name = environ.get('AWS_S3_BUCKET')
model_id_env = environ.get("MODEL_ID", default="/mnt/models")


class WhisperBucket(Model):
    def __init__(self, name: str, sample_rate=16000):
        super().__init__(name)
        model_id = model_id_env
        self._sample_rate = sample_rate
        self._s3_client = _init_s3_client()
        self._pipeline = _init_pipeline(model_id)
        self.ready = True

    async def predict(
            self,
            payload: Union[Dict, InferRequest],
            headers: Dict[str, str] = None
    ) -> Union[Dict, InferResponse]:

        sample_uris = payload['sample_uris']
        uri_mapping = _map_uris(sample_uris)
        create_task(self._transcript_generation(uri_mapping))
        response_body = _create_response_body(uri_mapping)

        print(f'Returning to client: {response_body}')
        return response_body

    async def _transcript_generation(self, uri_mapping):
        for sample_uri, transcript_uri in uri_mapping.items():
            print(f'Processing {sample_uri} into {transcript_uri}')

            local_sample_path = self._download_from_s3(sample_uri)
            audio_sample, _ = load(local_sample_path, sr=self._sample_rate)
            pipeline_output = self._pipeline(
                audio_sample, return_timestamps='word'
            )
            local_transcript_path = _write(pipeline_output, local_sample_path)
            self._upload_to_s3(local_transcript_path, transcript_uri)
            print(f'S3 upload of {transcript_uri} complete')

    def _download_from_s3(self, object_key):
        local_path = f"/tmp/{object_key.split('/')[-1]}"
        print(f'Downloading sample {object_key} in bucket {bucket_name} to {local_path}')
        try:
            self._s3_client.download_file(bucket_name, object_key, local_path)
            print(f"File downloaded successfully to {local_path}")
        except Exception as e:
            print(f"Error downloading file: {e}")
            raise e
        return local_path

    def _upload_to_s3(self, local_path, s3_uri):
        print(f'Uploading transcripts from {local_path} to {s3_uri} at bucket {bucket_name}')
        self._s3_client.upload_file(local_path, bucket_name, s3_uri)


def _init_s3_client():
    print(f'Instantiating S3 client against S3 endpoint {s3_endpoint}')
    s3_client = client(
        service_name='s3',
        aws_access_key_id=s3_access_key,
        aws_secret_access_key=s3_secret_key,
        endpoint_url=s3_endpoint,
    )
    return s3_client


def _init_pipeline(model_id):
    device = "cuda" if cuda.is_available() else "cpu"

    print(f"Loading model {model_id} on device {device}")
    whisper_pipeline = pipeline(
        "automatic-speech-recognition", model=model_id, device=device
    )
    return whisper_pipeline


def _map_uris(sample_uris):
    uri_mapping = {
        sample_uri: _build_transcript_uri(sample_uri)
        for sample_uri in sample_uris
    }
    return uri_mapping


def _build_transcript_uri(sample_uri):
    transcript_uri = f"transcripts/{sample_uri.split('/')[-1].split('.')[0]}.json"
    return transcript_uri


def _write(pipeline_output, local_sample_path):
    local_transcript_path = f"{local_sample_path.split('.')[0]}.json"
    print(f'Writing pipeline output to {local_transcript_path}')
    with open(local_transcript_path, 'w') as transcript_file:
        dump(pipeline_output, transcript_file)
    return local_transcript_path


def _create_response_body(uri_mapping):
    response_body = {
        'message': 'generating transcripts',
        'source-target URIs': uri_mapping,
        'S3 bucket': bucket_name,
    }
    return response_body


if __name__ == '__main__':
    parser = ArgumentParser(parents=[model_server.parser])
    args, _ = parser.parse_known_args()

    whisper_bucket = WhisperBucket(args.model_name)
    ModelServer().start([whisper_bucket])