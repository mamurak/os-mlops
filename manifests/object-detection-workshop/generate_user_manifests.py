import yaml
from argparse import ArgumentParser


def main():
    arguments = _read_arguments()
    user_count = arguments.user_count
    output_file_path = arguments.output_file_path
    generate_overall_manifest(user_count, output_file_path)


def _read_arguments():
    parser = ArgumentParser()
    parser.add_argument('--user_count', type=int)
    parser.add_argument('--output_file_path', default='user_manifests.yaml')
    arguments = parser.parse_args()
    return arguments


def generate_overall_manifest(user_count, output_file_path='generated_manifest.yaml'):
    overall_resources = _get_overall_resources(user_count)
    _generate_manifest(overall_resources, output_file_path)


def _get_overall_resources(user_count):
    overall_resources = []
    for index in range(1, user_count+1):
        if not (index == 10 or index == 11): 
            overall_resources += _get_user_resources(f'user{index}')
    return overall_resources


def _generate_manifest(resources, output_file_path):
    manifests = [
        yaml.dump(resource) for resource in resources
    ]
    overall_manifest = ''
    for manifest in manifests:
        overall_manifest += manifest
        overall_manifest += '---\n'
    with open(output_file_path, 'w') as outputfile:
        outputfile.write(overall_manifest)
    print(f'Wrote manifest {output_file_path}')


def _get_user_resources(user_id):
    user_resources = [
        _get_project_resource(user_id),
        _get_role_binding_resource(user_id),
        _get_pvc_resource(user_id),

        #### New ones ####
        _get_aws_connection_pipelines_resource(user_id),
        _get_aws_connection_object_detection_resource(user_id),
        _get_allow_from_all_namespaces_resource(user_id),
        _get_allow_from_ingress_namespace_resource(user_id),
        _get_pvc_development_resource(user_id),
        _get_pipelines_definition_resource(user_id),
        _get_ovms_resource(user_id),
        _get_offline_scoring_pvc_resource(user_id),
        _get_object_detection_training_pvc_resource(user_id)
    ]
    return user_resources


def _get_project_resource(user_id):
    project_resource = {
        'kind': 'Project',
        'apiVersion': 'project.openshift.io/v1',
        'metadata': {
            'name': user_id,
            'labels': {
                'kubernetes.io/metadata.name': user_id,
                'modelmesh-enabled': 'true',
                'opendatahub.io/dashboard': 'true',
            },
            'annotations': {
                'openshift.io/description': '',
                'openshift.io/display-name': user_id,
            }
        },
        'spec': {
            'finalizers': ['kubernetes']
        }
    }
    return project_resource


def _get_role_binding_resource(user_id):
    role_binding_resource = {
        'apiVersion': 'rbac.authorization.k8s.io/v1',
        'kind': 'RoleBinding',
        'metadata': {
            'name': 'admin',
            'namespace': user_id,
        },
        'subjects': [{
            'kind': 'User',
            'apiGroup': 'rbac.authorization.k8s.io',
            'name': user_id,
        }],
        'roleRef': {
            'apiGroup': 'rbac.authorization.k8s.io',
            'kind': 'ClusterRole',
            'name': 'admin',
        },
    }
    return role_binding_resource


def _get_pvc_resource(user_id):
    pvc_resource = {
        'apiVersion': 'v1',
        'kind': 'PersistentVolumeClaim',
        'metadata': {
            'name': user_id,
            'namespace': 'redhat-ods-applications',
        },
        'spec': {
            'accessModes': ['ReadWriteOnce'],
            'resources': {
                'requests': {'storage': '5Gi'},
            },
            'volumeMode': 'Filesystem',
        },
    }
    return pvc_resource


def _get_aws_connection_pipelines_resource(user_id):
    aws_connection_pipelines_resource = {
        'kind': 'Secret',
        'apiVersion': 'v1',
        'metadata': {
            'name': 'aws-connection-pipelines',
            'namespace': user_id,
            'labels':{
                'opendatahub.io/dashboard': 'true',
                'opendatahub.io/managed': 'true',
            },
            'annotations': {
                'opendatahub.io/connection-type': 's3',
                'openshift.io/display-name': 'pipelines',
            },
        },
        'stringData':{
            'AWS_ACCESS_KEY_ID': 'minio',
            'AWS_DEFAULT_REGION': 'us-east-1',
            'AWS_S3_BUCKET': f'{user_id}-pipelines',
            'AWS_S3_ENDPOINT': 'http://minio-service.minio.svc:9000',
            'AWS_SECRET_ACCESS_KEY': 'minio123',
            'type': 'Opaque',
        }
    }
    return aws_connection_pipelines_resource


def _get_aws_connection_object_detection_resource(user_id):
    aws_connection_object_detection_resource = {
        'kind': 'Secret',
        'apiVersion': 'v1',
        'metadata':{
            'name': 'aws-connection-object-detection',
            'namespace': user_id,
            'labels':{
                'opendatahub.io/dashboard': 'true',
                'opendatahub.io/managed': 'true',
            },
            'annotations':{
                'opendatahub.io/connection-type': 's3',
                'openshift.io/display-name': 'object-detection',
            },
        },
        'stringData':{
            'AWS_ACCESS_KEY_ID': 'minio',
            'AWS_DEFAULT_REGION': 'us-east-1',
            'AWS_S3_BUCKET': user_id,
            'AWS_S3_ENDPOINT': 'http://minio-service.minio.svc:9000',
            'AWS_SECRET_ACCESS_KEY': 'minio123',
            'type': 'Opaque',
        }
    }
    return aws_connection_object_detection_resource


def _get_allow_from_all_namespaces_resource(user_id):
    allow_from_all_namespaces_resource = {
        'kind': 'NetworkPolicy',
        'apiVersion': 'networking.k8s.io/v1',
        'metadata':{
            'name': 'allow-from-all-namespaces',
            'namespace': user_id,
        },
        'spec':{
            'podSelector': {},
            'ingress': [{'from': [{'namespaceSelector':{}}]}]
        },
        'policyTypes': ['Ingress']
    }
    return allow_from_all_namespaces_resource


def _get_allow_from_ingress_namespace_resource(user_id):
    allow_from_ingress_namespace_resource = {
        'kind': 'NetworkPolicy',
        'apiVersion': 'networking.k8s.io/v1',
        'metadata':{
            'name': 'allow-from-ingress-namespace',
            'namespace': user_id,
        },
        'spec':{
            'podSelector': {},
            'ingress': [{
                'from': [{
                    'namespaceSelector': {
                        'matchLabels': {
                            'network-policy': 'global'
                        }
                    }
                }]
            }],
            'policyTypes': ['Ingress'],
        }
    }
    return allow_from_ingress_namespace_resource


def _get_pvc_development_resource(user_id):
    pvc_development_resource = {
        'kind': 'PersistentVolumeClaim',
        'apiVersion': 'v1',
        'metadata':{
            'annotations':{
                'openshift.io/description': '',
                'openshift.io/display-name': 'development',
            },
            'name': 'development',
            'namespace': user_id,
            'finalizers': ['kubernetes.io/pvc-protection'],
            'labels':{
                'opendatahub.io/dashboard': 'true'
            },
        },
        'spec':{
            'accessModes': ['ReadWriteOnce'],
            'resources':{
                'requests':{
                    'storage': '20Gi'
                }
            },
            'volumeMode': 'Filesystem'
        }
    }
    return pvc_development_resource


def _get_pipelines_definition_resource(user_id):
    pipelines_definition_resource = {
        'apiVersion': 'datasciencepipelinesapplications.opendatahub.io/v1alpha1',
        'kind': 'DataSciencePipelinesApplication',
        'metadata':{
            'finalizers':['datasciencepipelinesapplications.opendatahub.io/finalizer'],
            'name': 'pipelines-definition',
            'namespace': user_id,
        },
        'spec':{
            'apiServer':{
                'stripEOF': True,
                'dbConfigConMaxLifetimeSec': 120,
                'applyTektonCustomResource': True,
                'deploy': True,
                'enableSamplePipeline': False,
                'autoUpdatePipelineDefaultVersion': True,
                'archiveLogs': False,
                'terminateStatus': 'Cancelled',
                'enableOauth': True,
                'trackArtifacts': True,
                'collectMetrics': True,
                'injectDefaultScript': True,
            },
            'database':{
                'mariaDB':{
                    'deploy': True,
                    'pipelineDBName': 'mlpipeline',
                    'pvcSize': '10Gi',
                    'username': 'mlpipeline',
                }
            },
            'objectStorage':{
                'externalStorage':{
                    'bucket': 'object-detection-pipelines',
                    'host': 'minio-service.minio.svc:9000',
                    'port': '',
                    's3CredentialsSecret':{
                        'accessKey': 'AWS_ACCESS_KEY_ID',
                        'secretKey': 'AWS_SECRET_ACCESS_KEY',
                        'secretName': 'aws-connection-pipelines',
                    },
                    'scheme': 'http',
                    'secure': False,
                }
            },
            'persistenceAgent':{
                'deploy': True,
                'numWorkers': 2
            },
            'scheduledWorkflow':{
                'cronScheduleTimezone': 'UTC',
                'deploy': True,
            }
        }
    }
    return pipelines_definition_resource


def _get_ovms_resource(user_id):
    ovms_resource = {
        'apiVersion': 'serving.kserve.io/v1alpha1',
        'kind': 'ServingRuntime',
        'metadata':{
            'annotations':{
                'enable-auth': 'false',
                'enable-route': 'true',
                'opendatahub.io/disable-gpu': 'true',
                'opendatahub.io/template-display-name': 'OpenVINO Model Server',
                'opendatahub.io/template-name': 'ovms',
                'openshift.io/display-name': 'OVMS',
            },
            'name': 'ovms',
            'namespace': user_id,
            'labels':{
                'name': 'ovms',
                'opendatahub.io/dashboard': 'true',
            }
        },
        'spec': {
            'builtInAdapter': {
                'memBufferBytes': 134217728,
                'modelLoadingTimeoutMillis': 90000,
                'runtimeManagementPort': 8888,
                'serverType': 'ovms',
            },
            'containers': [{
                'args': [
                    '--port=8001',
                    '--rest_port=8888',
                    '--config_path=/models/model_config_list.json',
                    '--file_system_poll_wait_seconds=0',
                    '--grpc_bind_address=127.0.0.1',
                    '--rest_bind_address=127.0.0.1'
                ],
                'image': 'quay.io/opendatahub/openvino_model_server@sha256:20dbfbaf53d1afbd47c612d953984238cb0e207972ed544a5ea662c2404f276d',
                'name': 'ovms',
                'resources':{
                    'limits':{
                        'cpu': '2',
                        'memory': '8Gi',
                    },
                    'requests':{
                        'cpu': '1',
                        'memory': '4Gi',
                    }
                }
            }],
            'grpcDataEndpoint': 'port:8001',
            'grpcEndpoint': 'port:8085',
            'multiModel': True,
            'protocolVersions': ['grpc-v1'],
            'replicas': 1,
            'supportedModelFormats':
                [{
                    'autoSelect': True,
                    'name': 'openvino_ir',
                    'version': 'opset1',
                },{
                    'autoSelect': True,
                    'name': 'onnx',
                    'version': '1',
                },{
                    'autoSelect': True,
                    'name': 'tensorflow',
                    'version': '2',
                }]
        }
    }
    return ovms_resource


def _get_offline_scoring_pvc_resource(user_id):
    offline_scoring_pvc_resource = {
        'kind': 'PersistentVolumeClaim',
        'apiVersion': 'v1',
        'metadata': {
            'name': 'offline-scoring-pvc',
            'namespace': user_id,
        },
        'spec': {
            'accessModes': ['ReadWriteOnce'],
            'resources': {
                'requests': {
                    'storage': '10Gi'
                }
            },
            'volumeMode': 'Filesystem'
        }
    }
    return offline_scoring_pvc_resource


def _get_object_detection_training_pvc_resource(user_id):
    object_detection_training_pvc_resource = {
        'kind': 'PersistentVolumeClaim',
        'apiVersion': 'v1',
        'metadata': {
            'name': 'object-detection-training-pvc',
            'namespace': user_id,
        },
        'spec': {
            'accessModes': ['ReadWriteOnce'],
            'resources':{
                'requests': {
                    'storage': '10Gi'
                }
            },
            'volumeMode': 'Filesystem'
        }
    }
    return object_detection_training_pvc_resource


if __name__ == '__main__':
    main()
