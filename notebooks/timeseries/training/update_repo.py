from os import environ

from git import GitCommandError, Repo
from yaml import safe_dump


repo_url = environ.get('REPO_URL')
git_token = environ.get('GIT_TOKEN')
model_object_name_file_path = 'model_object_name'
repository_path = './repository'


def update_manifest_repository():
    model_object_name = _read_model_object_name()
    repository = _clone_repository()
    inference_service_manifest_path = _update_manifest(model_object_name)
    _commit_and_push(
        repository, inference_service_manifest_path, model_object_name
    )


def _read_model_object_name():
    print(f'Reading model object name from {model_object_name_file_path}')
    with open(model_object_name_file_path, 'r') as inputfile:
        model_object_name = inputfile.read()
    return model_object_name


def _clone_repository():
    print(f'Checking out repo at {repo_url}')
    repo_url_auth = (
        f'https://none:{git_token}@{repo_url.lstrip("https://")}'
    )
    try:
        repository = Repo.clone_from(repo_url_auth, repository_path)
    except GitCommandError as error:
        print(f'Git clone failed: {error}\nChecking out local repository.')
        repository = Repo(repository_path)

    with repository.config_writer() as git_config:
        git_config.set_value('user', 'name', 'pipeline-runner')

    return repository


def _update_manifest(model_object_name):
    print(f'Updating manifest for {model_object_name}')
    inference_service_manifest_path = (
        f'{repository_path}/manifests/inference-service.yaml'
    )

    manifest = _get_manifest(model_object_name)

    print(f'Writing updated Inference Service CR: {manifest}')
    print(f'to path {inference_service_manifest_path}')

    with open(inference_service_manifest_path, 'w') as outputfile:
        safe_dump(manifest, outputfile)

    return inference_service_manifest_path


def _commit_and_push(
        repository, inference_service_manifest_path, model_object_name):

    commit_path = inference_service_manifest_path.lstrip(repository_path)
    print('Committing and pushing changes.')
    repository.index.add(commit_path)
    repository.index.commit(
        f'Preparing deployment of model {model_object_name}'
        f'in staging environment.'
    )
    repository.remotes.origin.push()


def _get_manifest(model_path):
    manifest = {
        'apiVersion': 'serving.kserve.io/v1beta1',
        'kind': 'InferenceService',
        'metadata': {
            'name': 'inference-service',
            'labels': {
                'name': 'inference-service',
                'opendatahub.io/dashboard': 'true',
            },
            'annotations': {
                'openshift.io/display-name': 'inference-service',
                'serving.kserve.io/deploymentMode': 'ModelMesh',
            },
        },
        'spec': {
            'predictor': {
                'model': {
                    'modelFormat': {
                        'name': 'sklearn',
                        'version': '0',
                    },
                    'name': '',
                    'resources': None,
                    'runtime': 'ml-server',
                    'storage': {
                        'key': 'aws-connection-user-bucket',
                        'path': model_path
                    }
                }
            }
        }
    }
    return manifest


if __name__ == '__main__':
    update_manifest_repository()