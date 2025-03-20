# Instructlab on OpenShift AI Workshop

## Setting up the environment

### Requirements

- OpenShift Container Platform (tested with 4.15)
    - 2 GPU instances, each with 20+ GB VRAM
    - drivers are installed, nodes tainted
- Red Hat OpenShift AI (tested with 2.18) with enabled components:
    - dashboard
    - workbenches
    - single-model serving
- Helm on bastion host / jumpbox, installable via `helm_install.sh`.

### Setup

#### Configure environment
1. Remove role binding `self-provisioner`.
2. Edit notebook sizes within ODH dashboard config as indicated in `odh-dashboard-config.yaml`.

#### Deploy Helm chart
1. Update `values.yaml` based on user count and cluster domain URL.
2. Deploy user projects with Helm: `helm install ilab-workshop .`

#### Set up authentication
1. Open `generate_htpasswd.ipynb`, update `number_of_participants`, run it.
2. Add generated htpasswd content to secret `htpasswd-secret` in namespace `openshift-config`.

#### Deploy language models
1. In namespace `llm`, deploy Granite via connection `granite`, using parameter `--max-model-len=2048`.
2. In namespace `llm`, deploy tuned finance model.

## Running the workshop

#### 1. Logging in

1. Receive your credentials using the workshop URL:
    - URL of the `username-distribution` route in namespace `username-distribution`,
    - password `ilab`.
2. Navigate to the RHOAI dashboard and your project.

#### 2. Explore base model

Inside your project
1. create a workbench using the AnythingLLM image.
2. Inside the workbench configure AnythingLLM:
    - LLM provider `Generic OpenAI`,
    - Base URL: inference endpoint URL of the Granite model, e.g. `https://granite-base.apps.[CLUSTER-DOMAIN-URL]/v1` (don't forget the `/v1` suffix),
    - Chat model name: model name of the Granite model deployment,
    - token context window 4096,
    - User Setup: "Just me" / "No",
    - Skip Survey,
    - create and navigate to workspace,
3. Test the base Granite model:
    - ask `What is the opening deposit amount for the core checking account?`
    - model guesses, will probably not provide correct answer of $100
    - ask `Do transactions that are still processing lower the available balance?`
    - model guesses, will not clearly state "yes".

#### 3. Explore Instructlab taxonomy

Inside your project
1. create a second workbench using the `InstructLab Code Server workbench` image.
2. Inside the workbench open a terminal session and initialize Instructlab:
    - `ilab config init`
    - `ilab config show`, review configuration.
3. Clone the workshop repository: `git clone https://github.com/mamurak/ilab-finance.git`
4. Review `ilab-finance/source_docs/core_checking.md`.
5. Review `ilab-finance/sample_qna/qna_empty.yaml`.
6. Review `ilab-finance/sample_qna/qna_part.yaml` and finish it.
7. Review the sample taxonomy under `ilab-finance/taxonomy`.

Skipping synthetic data generation and model alignment (or demo it on dedicated RHEL AI instance).

#### 4. Explore tuned model

1. Open the AnythingLLM workbench.
2. Reconfigure the model endpoint:
    - select `Open settings` in the bottom left corner,
    - select `AI Providers` -> `LLM`,
    - update `Base URL` and `Chat Model Name` based on tuned model deployment,
    - select `Save changes` and `Back to workspaces` (bottom left corner).
3. Enter workspace and create new thread.
4. Test the tuned model:
    - ask `What is the opening deposit amount for the core checking account?`
    - model reliable answers $100,
    - ask `Do transactions that are still processing lower the available balance?`
    - model reliably answers "yes".