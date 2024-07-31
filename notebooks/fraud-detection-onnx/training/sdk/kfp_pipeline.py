from kfp.dsl import pipeline
from kfp.kubernetes import use_secret_as_env

from data_ingestion import ingest_data
from data_preprocessing import preprocess
from kfp_client import KfpPipeline
from model_training import train_model
from model_validation import validate_model
from model_upload import upload_model


data_connection_secret_name = 'aws-connection-fraud-detection'


@pipeline(name='model-training-kfp')
def model_training_pipeline(
    data_object_name: str = 'training-data.csv',
    epoch_count: int = 20,
    learning_rate: float = 0.001,
    model_object_prefix: str = 'model'
        ):

    data_ingestion_task = ingest_data(
        data_object_name=data_object_name
    )
    use_secret_as_env(
        data_ingestion_task,
        secret_name=data_connection_secret_name,
        secret_key_to_env={
            'AWS_S3_ENDPOINT': 'AWS_S3_ENDPOINT',
            'AWS_ACCESS_KEY_ID': 'AWS_ACCESS_KEY_ID',
            'AWS_SECRET_ACCESS_KEY': 'AWS_SECRET_ACCESS_KEY',
            'AWS_S3_BUCKET': 'AWS_S3_BUCKET',
        },
    )
    data_ingestion_task.set_caching_options(False)

    preprocessing_task = preprocess(raw_data=data_ingestion_task.output)
    preprocessing_task.set_caching_options(False)

    model_training_task = train_model(
        epoch_count=epoch_count,
        learning_rate=learning_rate,
        training_samples=preprocessing_task.outputs['training_samples'],
        training_labels=preprocessing_task.outputs['training_labels'],
    )
    model_training_task.set_caching_options(False)

    model_validation_task = validate_model(
        model=model_training_task.outputs['model'])
    model_validation_task.set_caching_options(False)

    model_upload_task = upload_model(
        model_object_prefix=model_object_prefix,
        model=model_training_task.outputs['model']
    )
    use_secret_as_env(
        model_upload_task,
        secret_name=data_connection_secret_name,
        secret_key_to_env={
            'AWS_S3_ENDPOINT': 'AWS_S3_ENDPOINT',
            'AWS_ACCESS_KEY_ID': 'AWS_ACCESS_KEY_ID',
            'AWS_SECRET_ACCESS_KEY': 'AWS_SECRET_ACCESS_KEY',
            'AWS_S3_BUCKET': 'AWS_S3_BUCKET',
        },
    )
    model_upload_task.after(model_validation_task).set_caching_options(False)


def run_experiment():
    uploaded_pipeline = KfpPipeline(
        model_training_pipeline, 'model-training-sdk-pipeline'
    )
    for epoch_count in [5, 10]:
        for learning_rate in [0.001, 0.002]:
            uploaded_pipeline.run_with_parameters(
                pipeline_parameters={
                    'data_object_name': 'training-data.csv',
                    'epoch_count': epoch_count,
                    'learning_rate': learning_rate,
                    'model_object_prefix': 'model',
                },
                experiment_name='model_training-kfp'
            )


if __name__ == '__main__':
    run_experiment()