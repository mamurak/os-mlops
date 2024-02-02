from os import environ
from pprint import pprint
from time import sleep

from codeflare_sdk.cluster.cluster import Cluster, ClusterConfiguration
from codeflare_sdk.cluster.auth import TokenAuthentication
from codeflare_sdk.job.jobs import DDPJobDefinition


def submit_training_job(server_url='', token=''):
    auth = cluster_login(server_url, token)
    cluster = create_cluster()
    job = submit_job(cluster)
    wait_for_completion(job)
    clean_up(cluster, auth)


def cluster_login(server_url, token):
    server_url = server_url or environ.get('OCP_API_SERVER_URL')
    token = token or environ.get('OCP_TOKEN')

    print(f'logging into cluster at {server_url}')

    auth = TokenAuthentication(
        token=token, server=server_url, skip_tls=True
    )
    auth.login()

    print('login successful')
    return auth


def create_cluster():
    print('creating framework cluster')

    cluster = Cluster(
        ClusterConfiguration(
            name='llamafinetunelora',
            namespace='default',
            image='quay.io/project-codeflare/ray:latest-py39-cu118',
            num_workers=1,
            min_cpus=4,
            max_cpus=4,
            min_memory=96,
            max_memory=96,
            num_gpus=4,
            instascale=False,
        )
    )

    cluster_running = cluster.status()[1]

    if not cluster_running:
        cluster.up()
        print('booting cluster')

        cluster.wait_ready()
        print('cluster is online')

    print('cluster details:\n')
    cluster.details()

    return cluster


def submit_job(cluster):
    print('creating and submitting job')

    jobdef = DDPJobDefinition(
        name="llamafinetunelora",
        script="finetune.py",
        scheduler_args={"requirements": "requirements.txt"},
    )
    job = jobdef.submit(cluster)

    print('job submitted')

    return job


def wait_for_completion(job):
    print('awaiting job completion')

    job_finished = False
    while not job_finished:
        sleep(5)
        job_finished = job.status().is_terminal()
        print(f'job is finished: {job_finished}')

    print(f'job finished with status: {job.status()}')

    print('job logs:\n')
    pprint(job.logs())

    return


def clean_up(cluster, auth):
    print('shutting down cluster and logging out')

    cluster.down()
    auth.logout()

    print('cleanup complete')
    return


if __name__ == '__main__':
    submit_training_job()