from kfp.dsl import component, Dataset, Input, Model


runtime_image = 'quay.io/mmurakam/runtimes:fraud-detection-v2.6.1'


@component(base_image=runtime_image)
def upload_model(
        model_object_prefix: str, model: Input[Model],
        training_history: Input[Dataset]):
    from os import environ
    from pickle import load
    from random import choices
    from shutil import copy
    from string import ascii_lowercase, digits

    from model_registry import ModelRegistry
    from model_registry.utils import S3Params

    def _generate_version_id():
        alphabet = ascii_lowercase + digits
        version_id = ''.join(choices(alphabet, k=8))
        return version_id

    def _register_model_version(
            model_prefix, version, model_registry_endpoint_url):

        print(f'registering model version {version}')
        registry = _instantiate_model_registry(model_registry_endpoint_url)
        training_metrics = _load_training_metrics()

        model_description = '''
        Shallow neural network trained on Credit Card Fraud Detector dataset 
        (https://www.kaggle.com/code/janiobachmann/credit-fraud-dealing-with-imbalanced-datasets).\n
        Deployed model expects input vector of shape [1, 30] with FP32-type values, 
        returns vector of shape [1, 2] with FP32-type values denoting predicted 
        probabilities for non-fraud / fraud. See sample:
        https://github.com/mamurak/os-mlops/blob/main/notebooks/fraud-detection-onnx/online-scoring.ipynb
        '''
        s3_params = S3Params(
            bucket_name=s3_bucket_name,
            s3_prefix=model_prefix,
            access_key_id=s3_access_key,
            secret_access_key=s3_secret_key,
            endpoint_url=s3_endpoint_url
        )
        copy(model.path, 'model.onnx')
        registry.upload_artifact_and_register_model(
            name='fraud-detection',
            model_files_path='model.onnx',
            upload_params=s3_params,
            version=version,
            description=model_description,
            model_format_name='onnx',
            model_format_version='1',
            storage_key=s3_secret_name,
            metadata={
                'accuracy': str(training_metrics['accuracy'][-1]),
                'epoch_count': str(training_metrics['epoch_count']),
                'learning_rate': str(training_metrics['learning_rate']),
                'fraud-detection': '',
                'onnx': '',
            }
        )
        print('model registration complete.')

    def _instantiate_model_registry(model_registry_endpoint_url):
        sa_token_file_path = '/var/run/secrets/kubernetes.io/serviceaccount/token'
        with open(sa_token_file_path, 'r') as token_file:
            auth_token = token_file.read()

        registry = ModelRegistry(
            server_address=model_registry_endpoint_url,
            author='kfp-pipeline',
            user_token=auth_token,
        )
        return registry

    def _load_training_metrics():
        with open(training_history.path, 'rb') as inputfile:
            training_metrics = load(inputfile)
        return training_metrics

    s3_endpoint_url = environ.get('AWS_S3_ENDPOINT')
    s3_access_key = environ.get('AWS_ACCESS_KEY_ID')
    s3_secret_key = environ.get('AWS_SECRET_ACCESS_KEY')
    s3_bucket_name = environ.get('AWS_S3_BUCKET')
    s3_secret_name = 'aws-connection-fraud-detection'
    model_registry_endpoint_url = environ.get('MODEL_REGISTRY_ENDPOINT_URL')

    model_version = _generate_version_id()
    model_prefix = f'models/{model_version}'

    if model_registry_endpoint_url:
        _register_model_version(
            model_prefix, model_version,
            model_registry_endpoint_url
        )
    else:
        print('no model registry endpoint URL found. skipping model registration.')