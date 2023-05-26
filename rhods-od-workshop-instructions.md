# Object Detection with RHODS: Workshop Manual

Follow this guide to prepare the guided version of the [Object Detection with RHODS](http://mamurak.github.io) workshop.

## Prerequisites

* OpenShift Container Platform 4.10 or above,
* Red Hat OpenShift Data Science 1.21 or above,
* OpenShift Pipelines 1.17 or above,
* OpenShift Data Foundation.
* Data Science Pipelines (follow the [deployment guide](rhods-data-science-pipelines.md) for reference.)

## Preparation

- Review `manifests/object-detection-workshop/cluster-manifest.yaml`. Update the S3 credentials in the `aws-s3-secret`. Deploy te manifest as cluster admin.
- To prepare the users, run `/manifests/object-detection-workshop/generate_user_manifests.py`:
    - `python3 generate_user_manifests.py --user_count [USER_COUNT]`
- Deploy the generated `user_manifest.yaml` as cluster admin.
- Ensure all users can authenticate through OpenShift.

Follow the workshop guide as one of the provisioned users to validate the correct setup.

## Clean up

After running the workshop, clean up the environment as follows:
- Run `manifests/object-detection-workshop/generate_environment_reset.py`:
    - `python3 generate_environment_reset.py --end_user [USER_COUNT]`
- Run the generated statement in `removal_query.txt` as cluster admin.
