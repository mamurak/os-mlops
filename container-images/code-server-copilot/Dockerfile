FROM quay.io/opendatahub/workbench-images:base-ubi9-python-3.11-20250101-8487113

ARG CODESERVER_VERSION=v4.96.2
ARG OS_MLOPS_ARTIFACTS_VERSION_TAG=1.6.0

LABEL name="odh-notebook-code-server-ubi9-python-3.11" \
      summary="code-server image with python 3.11 based on UBI 9" \
      description="code-server image with python 3.11 based on UBI9" \
      io.k8s.display-name="code-server image with python 3.11 based on UBI9" \
      io.k8s.description="code-server image with python 3.11 based on UBI9" \
      authoritative-source-url="https://github.com/opendatahub-io/notebooks" \
      io.openshift.build.commit.ref="main" \
      io.openshift.build.source-location="https://github.com/opendatahub-io/notebooks/tree/main/codeserver/ubi9-python-3.11" \
      io.openshift.build.image="quay.io/opendatahub/workbench-images:codeserver-ubi9-python-3.11"

USER 0

WORKDIR /opt/app-root/bin

# Install usefull packages from Pipfile.lock
COPY Pipfile.lock ./

# Install packages and cleanup
RUN echo "Installing softwares and packages" && \
    micropipenv install && \
    rm -f ./Pipfile.lock && \
    # Fix permissions to support pip in Openshift environments \
    chmod -R g+w /opt/app-root/lib/python3.11/site-packages && \
    fix-permissions /opt/app-root -P && \
    # Install usefull OS packages
    dnf install -y jq git-lfs libsndfile && \
    dnf clean all && \
    rm -rf /var/cache/yum && \
    # Install code-server
    yum install -y "https://github.com/coder/code-server/releases/download/${CODESERVER_VERSION}/code-server-${CODESERVER_VERSION/v/}-amd64.rpm" && \
    yum -y clean all --enablerepo='*' && \
    # Change ownership of relevant directories
    chmod -R g+w /opt/app-root/lib/python3.11/site-packages && \
    fix-permissions /opt/app-root -P

COPY --chown=1001:0 utils/ utils/

# Download code-server extensions
WORKDIR /tmp
RUN mkdir artefacts && \
    git clone https://github.com/mamurak/os-mlops-artefacts.git artefacts && \
    cd artefacts && \
    git checkout ${OS_MLOPS_ARTIFACTS_VERSION_TAG} && \
    cp code-server-extensions/* /opt/app-root/bin/utils/ && \
    chown -R 1001:0 /opt/app-root/bin/utils/* && \
    chmod -R g+w /opt/app-root/bin/utils/* && \
    cd .. && \
    rm -r artefacts

WORKDIR /opt/app-root/bin

# Create and intall the extensions though build-time on a temporary directory. Later this directory will copied on the `/opt/app-root/src/.local/share/code-server/extensions` via run-code-server.sh file when it starts up.
RUN mkdir -p /opt/app-root/extensions-temp && \
    code-server --install-extension /opt/app-root/bin/utils/GitHub.copilot-1.255.0.vsix --extensions-dir /opt/app-root/extensions-temp && \
    code-server --install-extension /opt/app-root/bin/utils/GitHub.copilot-chat-0.23.2.vsix --extensions-dir /opt/app-root/extensions-temp && \
    code-server --install-extension /opt/app-root/bin/utils/Continue.continue-0.9.250@linux-x64.vsix --extensions-dir /opt/app-root/extensions-temp && \
    mkdir -p /opt/app-root/src/.continue 

# Set up Continue configuration
COPY --chown=1001:0 continue/config.json /opt/app-root/src/.continue/config.json
RUN chmod -R g+w /opt/app-root/src/.continue/*

# Install NGINX to proxy code-server and pass probes check
ENV NGINX_VERSION=1.24 \
    NGINX_SHORT_VER=124 \
    NGINX_CONFIGURATION_PATH=${APP_ROOT}/etc/nginx.d \
    NGINX_CONF_PATH=/etc/nginx/nginx.conf \
    NGINX_DEFAULT_CONF_PATH=${APP_ROOT}/etc/nginx.default.d \
    NGINX_CONTAINER_SCRIPTS_PATH=/usr/share/container-scripts/nginx \
    NGINX_APP_ROOT=${APP_ROOT} \
    NGINX_LOG_PATH=/var/log/nginx \
    NGINX_PERL_MODULE_PATH=${APP_ROOT}/etc/perl

# Modules does not exist
RUN yum install -y https://download.fedoraproject.org/pub/epel/epel-release-latest-9.noarch.rpm && \
    INSTALL_PKGS="bind-utils nginx nginx-mod-stream nginx-mod-http-perl fcgiwrap initscripts chkconfig supervisor" && \
    yum install -y --setopt=tsflags=nodocs $INSTALL_PKGS && \
    rpm -V $INSTALL_PKGS && \
    yum -y clean all --enablerepo='*'

COPY --chown=1001:0 supervisord/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Copy extra files to the image.
COPY nginx/root/ /

# Changing ownership and user rights to support following use-cases:
# 1) running container on OpenShift, whose default security model
#    is to run the container under random UID, but GID=0
# 2) for working root-less container with UID=1001, which does not have
#    to have GID=0
# 3) for default use-case, that is running container directly on operating system,
#    with default UID and GID (1001:0)
# Supported combinations of UID:GID are thus following:
# UID=1001 && GID=0
# UID=<any>&& GID=0
# UID=1001 && GID=<any>
RUN sed -i -f ${NGINX_APP_ROOT}/nginxconf.sed ${NGINX_CONF_PATH} && \
    mkdir -p ${NGINX_APP_ROOT}/etc/nginx.d/ && \
    mkdir -p ${NGINX_APP_ROOT}/etc/nginx.default.d/ && \
    mkdir -p ${NGINX_APP_ROOT}/api/ && \
    mkdir -p ${NGINX_CONTAINER_SCRIPTS_PATH}/nginx-start && \
    mkdir -p ${NGINX_LOG_PATH} && \
    mkdir -p ${NGINX_PERL_MODULE_PATH} && \
    chown -R 1001:0 ${NGINX_CONF_PATH} && \
    chown -R 1001:0 ${NGINX_APP_ROOT}/etc && \
    chown -R 1001:0 ${NGINX_CONTAINER_SCRIPTS_PATH}/nginx-start && \
    chown -R 1001:0 /var/lib/nginx /var/log/nginx /run && \
    chmod    ug+rw  ${NGINX_CONF_PATH} && \
    chmod -R ug+rwX ${NGINX_APP_ROOT}/etc && \
    chmod -R ug+rwX ${NGINX_CONTAINER_SCRIPTS_PATH}/nginx-start && \
    chmod -R ug+rwX /var/lib/nginx /var/log/nginx /run && \
    rpm-file-permissions && \
    # Ensure the temporary directory and target directory have the correct permissions
    mkdir -p /opt/app-root/src/.local/share/code-server/extensions && \
    mkdir -p /opt/app-root/src/.local/share/code-server/coder-logs && \
    chown -R 1001:0 /opt/app-root/src/.local/share/code-server && \
    chown -R 1001:0 /opt/app-root/extensions-temp && \
    chown -R 1001:0 /opt/app-root/src/.config/code-server

## Configure nginx
COPY nginx/serverconf/ /opt/app-root/etc/nginx.default.d/
COPY nginx/httpconf/ /opt/app-root/etc/nginx.d/
COPY nginx/api/ /opt/app-root/api/

# Launcher
COPY --chown=1001:0 run-code-server.sh run-nginx.sh ./

ENV SHELL /bin/bash

ENV PYTHONPATH=/opt/app-root/bin/python3

WORKDIR /opt/app-root/src

USER 1001

CMD ["/opt/app-root/bin/run-code-server.sh"]
