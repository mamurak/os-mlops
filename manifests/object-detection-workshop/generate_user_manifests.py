import yaml


def generate_overall_manifest(user_count, output_file_path='generated_manifest.yaml'):
    overall_resources = get_overall_resources(user_count)
    generate_manifest(overall_resources, output_file_path)


def get_overall_resources(user_count):
    overall_resources = []
    for index in range(1, user_count+1):
        overall_resources += get_user_resources(f'user{index}')
    return overall_resources


def generate_manifest(resources, output_file_path):
    manifests = [
        yaml.dump(resource) for resource in resources
    ]
    overall_manifest = ''
    for manifest in manifests:
        overall_manifest += manifest
        overall_manifest += '---\n'
    with open(output_file_path, 'w') as outputfile:
        outputfile.write(overall_manifest)


def get_user_resources(user_id):
    user_resources = [
        get_project_resource(user_id),
        get_single_obc_resource(user_id),
        get_namespace_store_resource(user_id),
        get_combined_obc_resource(user_id),
        get_bucket_class_resource(user_id),
        get_role_binding_resource(user_id),
        get_pvc_resource(user_id),
    ]
    return user_resources


def get_project_resource(user_id):
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


def get_single_obc_resource(user_id):
    obc_resource = {
        'apiVersion': 'objectbucket.io/v1alpha1',
        'kind': 'ObjectBucketClaim',
        'metadata': {
            'name': f'{user_id}-single',
            'namespace': user_id,
            'finalizers': ['objectbucket.io/finalizer'],
            'labels': {
                'app': 'noobaa',
                'bucket-provisioner': 'openshift-storage.noobaa.io-obc',
                'noobaa-domain': 'openshift-storage.noobaa.io',
            },
        },
        'spec': {
            'additionalConfig': {
                'bucketclass': 'noobaa-default-bucket-class',
            },
            'bucketName': f'{user_id}-single',
            'generateBucketName': f'{user_id}-single',
            'storageClassName': 'openshift-storage.noobaa.io',
        }
    }
    return obc_resource


def get_namespace_store_resource(user_id):
    namespace_store_resource = {
        'apiVersion': 'noobaa.io/v1alpha1',
        'kind': 'NamespaceStore',
        'metadata': {
            'name': user_id,
            'namespace': 'openshift-storage',
            'finalizers': ['noobaa.io/finalizer'],
            'labels': {'app': 'noobaa'},
        },
        'spec': {
            's3Compatible': {
                'endpoint': 'http://s3.openshift-storage.svc',
                'secret': {
                    'name': f'{user_id}-single',
                    'namespace': user_id,
                },
                'targetBucket': f'{user_id}-single',
            },
            'type': 's3-compatible',
        },
    }
    return namespace_store_resource


def get_bucket_class_resource(user_id):
    bucket_class_resource = {
        'apiVersion': 'noobaa.io/v1alpha1',
        'kind': 'BucketClass',
        'metadata': {
            'name': user_id,
            'namespace': 'openshift-storage',
            'finalizers': ['noobaa.io/finalizer'],
            'labels': {'app': 'noobaa'},
        },
        'spec': {
            'namespacePolicy': {
                'multi': {
                    'readResources': [
                        'aws-s3-data', 'aws-s3-models', user_id,
                    ],
                    'writeResource': user_id,
                },
                'type': 'Multi',
            },
        },
    }
    return bucket_class_resource


def get_combined_obc_resource(user_id):
    combined_obc_resouce = {
        'apiVersion': 'objectbucket.io/v1alpha1',
        'kind': 'ObjectBucketClaim',
        'metadata': {
            'name': user_id,
            'namespace': user_id,
            'finalizers': ['objectbucket.io/finalizer'],
            'labels': {
                'app': 'noobaa',
                'bucket-provisioner': 'openshift-storage.noobaa.io-obc',
                'noobaa-domain': 'openshift-storage.noobaa.io',
            },
        },
        'spec': {
            'additionalConfig': {
                'bucketclass': user_id,
            },
            'bucketName': user_id,
            'generateBucketName': user_id,
            'storageClassName': 'openshift-storage.noobaa.io',
        },
    }
    return combined_obc_resouce


def get_role_binding_resource(user_id):
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


def get_pvc_resource(user_id):
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


if __name__ == '__main__':
    generate_overall_manifest(40)
