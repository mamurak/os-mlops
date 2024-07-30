from datetime import datetime

from kfp.client import Client
from kfp.compiler import Compiler


compiler = Compiler()


class KfpPipeline:
    def __init__(self, sdk_pipeline, pipeline_name, caching=False):
        self.pipeline_name = pipeline_name
        self.caching = caching
        self._client = _get_kfp_client()
        self._pipeline_id = None
        self._pipeline_version_id = None
        self._compiled_pipeline_location = './pipeline.yaml'
        self._upload_pipeline(sdk_pipeline)

    def _upload_pipeline(self, sdk_pipeline):
        print('compiling pipeline')
        compiler.compile(
            sdk_pipeline,
            package_path=self._compiled_pipeline_location
        )
        print(f'compiled pipeline to {self._compiled_pipeline_location}')

        print(f'uploading pipeline {self.pipeline_name}')
        pipeline_id = self._client.get_pipeline_id(self.pipeline_name)
        if not pipeline_id:
            print(f'pipeline {self.pipeline_name} not found. creating.')
            remote_pipeline = self._client.upload_pipeline(
                pipeline_package_path=self._compiled_pipeline_location,
                pipeline_name=self.pipeline_name,
                description='Pipeline demonstrating KFP SDK'
            )
            pipeline_id = remote_pipeline.pipeline_id

        self._pipeline_id = pipeline_id
        print(f'uploading new version for pipeline {self.pipeline_name} with '
              f'ID {pipeline_id}')

        pipeline_version_name = f'model-training-{_timestamp()}'
        remote_pipeline = self._client.upload_pipeline_version(
            pipeline_package_path=self._compiled_pipeline_location,
            pipeline_version_name=pipeline_version_name,
            pipeline_name=self.pipeline_name
        )
        self._pipeline_version_id = remote_pipeline.pipeline_version_id
        print(f'uploaded pipeline as new version {pipeline_version_name} '
              f'with ID {self._pipeline_version_id}')

    def run_with_parameters(self, pipeline_parameters, experiment_name):
        print(f'starting new pipeline run in experiment {experiment_name}')
        try:
            remote_experiment = self._client.get_experiment(
                experiment_name=experiment_name
            )
        except Exception:
            print(f'experiment {experiment_name} not found. creating.')
            remote_experiment = self._client.create_experiment(
                experiment_name
            )
        experiment_id = remote_experiment.experiment_id

        run_name = f'model-training-run-{_timestamp()}'
        print(f'starting new pipeline run name {run_name}')
        self._client.run_pipeline(
            experiment_id=experiment_id,
            job_name=run_name,
            pipeline_id=self._pipeline_id,
            version_id=self._pipeline_version_id,
            params=pipeline_parameters,
            enable_caching=self.caching
        )
        print('pipeline run submitted')


def _get_kfp_client():
    namespace_file_path =\
        '/var/run/secrets/kubernetes.io/serviceaccount/namespace'
    with open(namespace_file_path, 'r') as namespace_file:
        namespace = namespace_file.read()

    kubeflow_endpoint =\
        f'https://ds-pipeline-dspa.{namespace}.svc:8443'

    sa_token_file_path = '/var/run/secrets/kubernetes.io/serviceaccount/token'
    with open(sa_token_file_path, 'r') as token_file:
        bearer_token = token_file.read()

    ssl_ca_cert =\
        '/var/run/secrets/kubernetes.io/serviceaccount/service-ca.crt'

    print(f'Connecting to Data Science Pipelines: {kubeflow_endpoint}')
    client = Client(
        host=kubeflow_endpoint,
        existing_token=bearer_token,
        ssl_ca_cert=ssl_ca_cert
    )
    return client


def _timestamp():
    return datetime.now().strftime('%y%m%d%H%M')
