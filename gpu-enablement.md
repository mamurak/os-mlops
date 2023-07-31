# Quickstart: Enabling GPU usage on OpenShift

To quickly enable your Nvidia GPUs in your OpenShift cluster for usage, for instance for RHODS, follow the following steps:
1. Install the _Node Feature Discovery Operator_ through OperatorHub (Red Hat item).
2. After installing the operator, view the operator details and select _Create instance_ in the `NodeFeatureDiscovery` tile. In the configuration form view, scroll down and select _Create_ to apply the default configuration.
3. Install the _NVIDIA GPU Operator_ through the OperatorHub.
4. After installing the operator, view the operator details and select _Create instance_ in the `ClusterPolicy` view. In the configuration form view, scroll down and select _Create_ to apply the default configuration.

This will kick off scanning and labeling of your worker nodes with respect to the available GPUs. This process should take around 5-10 minutes. You can verify it by inspecting the labels of your GPU-enabled worker node (navigate to `Compute` -> `Nodes` -> [one of your workers with GPUs] -> `YAML`). Once the `nvidia.com/gpu.count` label shows up with a non-zero value, the GPUs are ready for use.

As a final verification in RHODS, use the `nvidia-smi` notebook in the `notebooks` folder within a CUDA-enabled workbench.

## References
- [List of supported GPUs and OpenShift versions](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/platform-support.html)
- [Enabling the GPU dashboard](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/openshift/enable-gpu-op-dashboard.html)
- [Documentation of the NVIDIA GPU Operator](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/openshift/contents.html)
- [Recipes for time slicing and autoscaling with GPUs](https://ai-on-openshift.io/odh-rhods/nvidia-gpus/)