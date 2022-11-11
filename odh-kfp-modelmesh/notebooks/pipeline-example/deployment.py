def get_deployment_resource(s3_bucket_name):
    deployment_resource = {
        'apiVersion': 'machinelearning.seldon.io/v1',
        'kind': 'SeldonDeployment',
        'metadata': {
            'name': 'inference-service',
        },
        'spec': {
            'name': 'inference-service',
            'predictors': [{
                'name': 'predictor',
                'replicas': 1,
                'graph': {
                    'name': 'inference-service',
                    'implementation': 'SKLEARN_SERVER',
                    'storageInitializerImage': 'seldonio/rclone-storage-initializer:1.12.0',
                    'envSecretRefName': 'seldon-rclone-secret',
                    'parameters': [{
                        'name': 'method',
                        'type': 'STRING',
                        'value': 'predict',
                    }],
                    'modelUri': f's3://{s3_bucket_name}'
                }
            }]
        }
    }
    return deployment_resource
