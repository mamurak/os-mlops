from argparse import ArgumentParser
from os import environ
from typing import Dict, Union

from boto3 import client
from kserve import Model, ModelServer, model_server, InferRequest, InferResponse
from kserve.errors import InvalidInput
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

    def preprocess(
            self,
            payload: Union[Dict, InferRequest],
            headers: Dict[str, str] = None
    ) -> Union[Dict, InferRequest]:

        _validate_request(payload, headers)
        sample_path = self._download_from_s3(payload['sample_uri'])
        audio_sample, _ = load(sample_path, sr=self._sample_rate)

        return audio_sample

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

    def predict(
            self,
            payload: Union[Dict, InferRequest],
            headers: Dict[str, str] = None
    ) -> Union[Dict, InferResponse]:

        print('Generating transcription')
        audio_sample = payload
        pipeline_output = self._pipeline(audio_sample, return_timestamps='word')
        print(f'Returning pipeline output: {pipeline_output}')

        return pipeline_output


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


def _validate_request(payload, headers):
    print('Validating request payload')
    if isinstance(payload, Dict) and "sample_uri" in payload:
        headers["request-type"] = "v1"
    elif isinstance(payload, bytes):
        raise InvalidInput("form data not implemented")
    elif isinstance(payload, InferRequest):
        raise InvalidInput("v2 protocol not implemented")
    else:
        raise InvalidInput("invalid payload")


if __name__ == '__main__':
    parser = ArgumentParser(parents=[model_server.parser])
    args, _ = parser.parse_known_args()

    whisper_bucket = WhisperBucket(args.model_name)
    ModelServer().start([whisper_bucket])