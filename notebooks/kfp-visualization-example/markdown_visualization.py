from kfp import dsl
from kfp.client import Client
from kfp.dsl import component, Output, Markdown


@component
def markdown_visualization(markdown_artifact: Output[Markdown]):
    markdown_content = '''
## This should be rendered as a header
The following should be rendered as a table:

| Item | Quantity |
| ---- | -------- |
| Apples | 2 |
| Pears | 2.5 |
| **Total** | **4.5** |
    '''
    markdown_artifact.path += '.md'
    with open(markdown_artifact.path, 'w') as f:
        f.write(markdown_content)


@dsl.pipeline(name='markdown-visualization-pipeline')
def markdown_visualization_pipeline():
    markdown_visualization()


def submit(pipeline):
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
    result = client.create_run_from_pipeline_func(
        pipeline,
        arguments={},
        experiment_name='markdown-visualization-pipeline',
    )
    print(f'Starting pipeline run with run_id: {result.run_id}')


if __name__ == '__main__':
    submit(markdown_visualization_pipeline)