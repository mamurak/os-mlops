from argparse import ArgumentParser


def main():
    arguments = _read_arguments()
    end_user = arguments.end_user
    start_user = arguments.start_user
    exclude_users = arguments.exclude_users
    output_file_path = arguments.output_file_path
    overall_deletion_query = get_overall_deletion_query(
        end_user=end_user, start_user=start_user, exclude_users=exclude_users
    )
    with open(output_file_path, 'w') as outputfile:
        outputfile.write(overall_deletion_query)


def _read_arguments():
    parser = ArgumentParser()
    parser.add_argument('--end_user', type=int)
    parser.add_argument('--start_user', type=int, default=1)
    parser.add_argument('--exclude_users') # TODO: define type
    parser.add_argument('--output_file_path', default='removal_query.txt')
    arguments = parser.parse_args()
    return arguments


def get_overall_deletion_query(end_user, start_user=1, exclude_users=None):
    overall_deletion_query = ''
    for index in range(start_user, end_user+1):
        if exclude_users and index in exclude_users:
            continue
        overall_deletion_query += f'{_get_deletion_query(f"user-{index}")}\n'
    overall_deletion_query += 'oc status'
    return overall_deletion_query


def _get_deletion_query(user_id):
    bucket_finalizer_removal_query = _get_finalizer_removal_query(
        namespace=user_id,
        kind_list=['ConfigMap', 'Secret', 'ObjectBucketClaim'],
        resource_id_list=[user_id, f'{user_id}-single'],
        finalizer='objectbucket.io/finalizer'
    )
    bucket_class_finalizer_removal_query = _get_finalizer_removal_query(
        namespace='openshift-storage',
        kind_list=['BucketClass'],
        resource_id_list=[user_id],
        finalizer='noobaa.io/finalizer'
    )
    pvc_finalizer_removal_query = _get_finalizer_removal_query(
        namespace='redhat-ods-applications',
        kind_list=['PersistentVolumeClaim'],
        resource_id_list=[user_id],
        finalizer='kubernetes.io/pvc-protection'
    )
    namespace_store_finalizer_removal_query = _get_finalizer_removal_query(
        namespace='openshift-storage',
        kind_list=['NamespaceStore'],
        resource_id_list=[user_id],
        finalizer='noobaa.io/finalizer'
    )
    deletion_query = (
        f'{bucket_finalizer_removal_query}'
        f'oc delete project {user_id} && \n'
        f'{bucket_class_finalizer_removal_query}'
        f'oc delete BucketClass {user_id} -n openshift-storage --wait=false && \n'
        f'{namespace_store_finalizer_removal_query}'
        f'oc delete NamespaceStore {user_id} -n openshift-storage --wait=false && \n'
        f'{pvc_finalizer_removal_query}'
        f'oc delete PersistentVolumeClaim {user_id} -n redhat-ods-applications --wait=false &&'
    )
    return deletion_query


def _get_finalizer_removal_query(namespace, kind_list, resource_id_list, finalizer):
    removal_query = ''
    for resource_id in resource_id_list:
        for kind in kind_list:
            removal_query += (
                f'oc patch {kind} {resource_id} -n {namespace} --type=json '
                f'-p \'[{{"op": "remove", "path": "/metadata/finalizers", "value": "{finalizer}"}}]\' && \n'
            )
    return removal_query


if __name__ == '__main__':
    main()
