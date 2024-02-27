from os import environ
from pprint import pprint
from time import sleep

from codeflare_sdk.cluster.cluster import Cluster, ClusterConfiguration
from codeflare_sdk.cluster.auth import TokenAuthentication
from codeflare_sdk.job.jobs import DDPJobDefinition


model_id = environ.get('hf_model_id', 'Trelis/Llama-2-7b-chat-hf-sharded-bf16')


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
            image='quay.io/mmurakam/runtimes:finetuning-ray-runtime-v0.2.1',
            num_workers=1,
            min_cpus=2,  # 4 for llama-2
            max_cpus=2,  # 4 for llama-2
            min_memory=8,  # 96 for Llama-2
            max_memory=8,  # 96 for Llama-2
            num_gpus=1,
            instascale=False,
        )
    )

    cluster_running = cluster.status()[1]

    #if not cluster_running:
    #    cluster.up()
    #    print('booting cluster')

    #    cluster.wait_ready()
    #    print('cluster is online')

    print('cluster details:\n')
    cluster.details()

    return cluster


def submit_job(cluster):
    print('creating and submitting job')

    jobdef = DDPJobDefinition(
        name="llamafinetunelora",
        script="finetune.py"
        # scheduler_args={"requirements": "requirements.txt"},
    )
    job = jobdef.submit(cluster)

    print('job submitted')

    return job


def wait_for_completion(job):
    print('awaiting job completion')

    job_finished = False
    while not job_finished:
        sleep(5)
        try:
            job_status = job.status()
            job_finished = job.status().is_terminal()
            print(f'job is finished: {job_finished}')
        except Exception as e:
            print(f'An error occurred while checking job status: {e}')
    try:
        job_status = job.status()
        print(f'job finished with status: {job_status}')
        print('job logs:\n')
        pprint(job.logs())
    except Exception as e:
        print(f'An error occurred while fetching job logs or status: {e}')
        raise

    if job.status().state._name_ == 'FAILED':
        raise Exception('Job failed!')
    return


def clean_up(cluster, auth):
    print('shutting down cluster and logging out')

    # cluster.down()
    auth.logout()

    print('cleanup complete')
    return


if __name__ == '__main__':
    submit_training_job()