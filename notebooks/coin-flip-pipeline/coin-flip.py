#!/usr/bin/env python3
# Copyright 2020-2023 The Kubeflow Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# %% [markdown]
# # DSL control structures tutorial
# Shows how to use conditional execution, loops, and exit handlers.

# %%

from kfp.client import Client
from kfp.compiler import Compiler
from kfp.dsl import component, ExitHandler, If, ParallelFor, pipeline


@component
def get_random_int_op(minimum: int, maximum: int) -> int:
    """Generate a random number between minimum and maximum (inclusive)."""
    import random
    result = random.randint(minimum, maximum)
    print(result)
    return result


@component
def flip_coin_op() -> str:
    """Flip a coin and output heads or tails randomly."""
    import random
    result = random.choice(['heads', 'tails'])
    print(result)
    return result


@component
def print_op(message: str):
    """Print a message."""
    print(message)


@component
def fail_op(message: str):
    """Fails."""
    import sys
    print(message)
    sys.exit(1)


# %% [markdown]
# ## Parallel execution
# You can use the `with dsl.ParallelFor(task1.outputs) as items:` context to execute tasks in parallel

# ## Conditional execution
# You can use the `with dsl.Condition(task1.outputs["output_name"] = "value"):` context to execute parts of the pipeline conditionally

# ## Exit handlers
# You can use `with dsl.ExitHandler(exit_task):` context to execute a task when the rest of the pipeline finishes (succeeds or fails)

# %%


@pipeline(
    name='tutorial-control-flows',
    description='Shows how to use dsl.Condition(), dsl.ParallelFor, and dsl.ExitHandler().'
)
def control_flows_pipeline():
    exit_task = print_op(message='Exit handler has worked!')
    with ExitHandler(exit_task):
        fail_op(
            message="Failing the run to demonstrate that exit handler still gets executed."
        )

    flip = flip_coin_op()

    with ParallelFor(['heads', 'tails']) as expected_result:

        with If(flip.output == expected_result):
            random_num_head = get_random_int_op(minimum=0, maximum=9).set_caching_options(False)
            with If(random_num_head.output > 5):
                print_op(
                    message=f'{expected_result} and {random_num_head.output} > 5!'
                ).set_caching_options(False)
            with If(random_num_head.output <= 5):
                print_op(
                    message=f'{expected_result} and {random_num_head.output} <= 5!'
                ).set_caching_options(False)


def submit(pipeline):
    namespace_file_path =\
        '/var/run/secrets/kubernetes.io/serviceaccount/namespace'
    with open(namespace_file_path, 'r') as namespace_file:
        namespace = namespace_file.read()

    kubeflow_endpoint = f'https://ds-pipeline-dspa.{namespace}.svc:8443'

    sa_token_file_path = '/var/run/secrets/kubernetes.io/serviceaccount/token'
    with open(sa_token_file_path, 'r') as token_file:
        bearer_token = token_file.read()

    ssl_ca_cert =\
        '/var/run/secrets/kubernetes.io/serviceaccount/service-ca.crt'

    print(f'Connecting to Data Science Pipelines: {kubeflow_endpoint}')
    client = Client(
        host=kubeflow_endpoint,
        existing_token=bearer_token,
        ssl_ca_cert=ssl_ca_cert
    )
    result = client.create_run_from_pipeline_func(
        pipeline,
        arguments={},
        experiment_name='coin-flip-pipeline',
        enable_caching=False
    )
    print(f'Starting pipeline run with run_id: {result.run_id}')


if __name__ == '__main__':
    # Compiling the pipeline
    Compiler().compile(control_flows_pipeline, __file__ + '.yaml')
    submit(control_flows_pipeline)