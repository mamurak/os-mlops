# Object Detection Helm Chart

This chart deploys:
- the OpenShift AI operator,
- Minio as the S3 storage backend,
- the object detection application based on RHOAI Model Serving.

## Prerequisites

- An OpenShift cluster with internet access. This chart was tested on OCP 4.14.
- Cluster admin access.
- The RHOAI operator is not installed.

If you don't have Helm installed yet, you can use this recipe:
```
sudo su -
curl -fsSL -o get_
helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 && \
sed -i 's/\/local//' get_helm.sh && \
chmod 700 get_helm.sh && \
bash get_helm.sh && \
su lab-user && \
cd ~
```

## Installation

1. Clone this repository and navigate to this folder:
```
git clone https://github.com/mamurak/os-mlops.git
cd os-mlops/manifests/object-detection-workshop/od-app-chart
```

2. Create the RHOAI operator namespace:
```
oc new-project redhat-ods-operator
```

3. Install the chart:
```
helm install od-app .
```

Installation will take a couple of minutes. The app is ready once the `modelmesh` pod in the `object-detection` namespace is up and running.

## Usage

Call the app from a device with a camera, e.g. your laptop or smart phone. The app URL is provided by the frontend route:
```
oc get route object-detection-app -n object-detection
```

## Deinstallation

1. Delete the Helm chart:

```
helm delete od-app
```

2. Delete the data science cluster CR:

```
oc delete datasciencecluster rhods
```

3. Delete the operator namespace:

```
oc delete project redhat-ods-operator
```

## To dos

- Extract the RHOAI operator into a separate Helm chart. Allows to bundle the operator namespace into the chart, which is currently not possible for some reason.
- Change update policy in operator to `Manual` to minimize the risk of automatic breaking upgrades.