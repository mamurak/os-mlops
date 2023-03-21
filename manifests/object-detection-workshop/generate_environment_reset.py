def get_overall_deletion_query(n_users, start_user=1, exclude_users=None):
    overall_deletion_query = ''
    for index in range(start_user, n_users+1):
        if exclude_users and index in exclude_users:
            continue
        overall_deletion_query += f'{get_deletion_query(f"user{index}")}\n'
    overall_deletion_query += 'oc status'
    with open('generated_removal_query.txt', 'w') as outputfile:
        outputfile.write(overall_deletion_query)


def get_deletion_query(user_id):
    bucket_finalizer_removal_query = _get_finalizer_removal_query(
        namespace=user_id,
        kind_list=['ObjectBucketClaim', 'ConfigMap', 'Secret'],
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
        f'{bucket_class_finalizer_removal_query}\n'
        f'oc delete BucketClass {user_id} -n openshift-storage --wait=false && \n'
        f'{namespace_store_finalizer_removal_query}\n'
        f'oc delete NamespaceStore {user_id} -n openshift-storage --wait=false && \n'
        f'{bucket_finalizer_removal_query}\n'
        f'oc delete project {user_id} && \n'
        f'{pvc_finalizer_removal_query}\n'
        f'oc delete PersistentVolumeClaim {user_id} -n redhat-ods-applications --wait=false &&'
    )
    return deletion_query


def _get_finalizer_removal_query(namespace, kind_list, resource_id_list, finalizer):
    removal_query = ''
    for resource_id in resource_id_list:
        for kind in kind_list:
            removal_query += (
                f'oc patch {kind} {resource_id} -n {namespace} --type=json '
                f'-p \'[{{"op": "remove", "path": "/metadata/finalizers", "value": "{finalizer}"}}]\' && '
            )
    return removal_query


if __name__ == '__main__':
    get_overall_deletion_query(15)
