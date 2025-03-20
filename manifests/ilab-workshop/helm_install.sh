curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
sed -i 's/\/local//' get_helm.sh
chmod 700 get_helm.sh
bash get_helm.sh