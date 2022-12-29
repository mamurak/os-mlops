FROM quay.io/opendatahub/notebooks:jupyter-pytorch-ubi8-python-3.8-pr-30

ENV OPENCV_VERSION=4.6.0
ENV DLIB_VERSION=19.24

USER 0

##########################################
# Install various dependencies for build #
##########################################

RUN yum install -y yum-utils && \
    /usr/bin/crb enable && \
    yum install -y https://download.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm && \
    yum install -y https://download1.rpmfusion.org/free/el/rpmfusion-free-release-8.noarch.rpm && \
    yum install -y https://download1.rpmfusion.org/nonfree/el/rpmfusion-nonfree-release-8.noarch.rpm && \
    INSTALL_PKGS="libsndfile ffmpeg ffmpeg-devel" && \
    yum install -y --setopt=tsflags=nodocs $INSTALL_PKGS && \
    rpm -V $INSTALL_PKGS && \
    yum -y clean all --enablerepo='*' && \
    rm -rf /var/cache/dnf

# Install needed packages to build
RUN INSTALL_PKGS="epel-release git gcc gcc-c++ cmake qt5-qtbase-devel \
    gtk2-devel libpng-devel jasper-devel OpenEXR-devel libwebp-devel \
    libjpeg-turbo-devel libtiff-devel tbb-devel libv4l-devel \
    eigen3-devel freeglut-devel mesa-libGL mesa-libGL-devel \
    boost boost-thread boost-devel gstreamer1-plugins-base \
    gstreamer1-plugins-base-devel hdf5  hdf5-devel openblas openblas-devel \
    lapack lapack-devel" && \
    yum install -y --setopt=tsflags=nodocs $INSTALL_PKGS && \
    #rpm -V $INSTALL_PKGS && \
    yum -y clean all --enablerepo='*' && \
    rm -rf /var/cache/dnf && \
    pip install --no-cache-dir numpy==1.24.1

RUN wget https://developer.download.nvidia.com/compute/cuda/11.8.0/local_installers/cuda-repo-rhel8-11-8-local-11.8.0_520.61.05-1.x86_64.rpm && \
    rpm -i cuda-repo-rhel8-11-8-local-11.8.0_520.61.05-1.x86_64.rpm && \
    yum clean all && \
    yum -y module install nvidia-driver:latest-dkms && \
    yum -y install cuda libcudnn8 && \
    rm -rf /var/cache/dnf && \
    ldconfig /usr/local/cuda/lib64 && \
    unset PROMPT_COMMAND

ENV PATH=$PATH:/usr/local/cuda/bin
ENV LD_LIBRARY_PATH=/usr/local/cuda/lib64

#########################################
## Build OpenCV and Contrib from source #
#########################################

# Build OpenCV
RUN mkdir -p /tmp/opencv_build && cd /tmp/opencv_build && \
    git clone --depth 1 --branch ${OPENCV_VERSION} https://github.com/opencv/opencv.git && \
    git clone --depth 1 --branch ${OPENCV_VERSION} https://github.com/opencv/opencv_contrib.git && \
    mkdir -p /tmp/opencv_build/opencv/build

WORKDIR /tmp/opencv_build/opencv/build

RUN cmake3 -D CMAKE_BUILD_TYPE=RELEASE \
    -D CMAKE_INSTALL_PREFIX=/opt/opencv \
    -D BUILD_opencv_python2=OFF \
    -D BUILD_opencv_python3=ON \
    -D INSTALL_C_EXAMPLES=OFF \
    -D INSTALL_PYTHON_EXAMPLES=OFF \
    -D OPENCV_GENERATE_PKGCONFIG=ON \
    -D WITH_CUDA=ON \
    -D CUDA_TOOLKIT_ROOT_DIR=/usr/local/cuda \
    -D CUDA_BIN_PATH=/usr/local/cuda/bin \
    -D CUDA_CUDART_LIBRARY=/usr/local/cuda/lib64/libcudart.so \
    -D WITH_CUDNN=ON \
    -D WITH_CUBLAS=ON \
    -D WITH_TBB=ON \
    -D OPENCV_DNN_CUDA=ON \
    -D BUILD_OPENCV_DNN=ON \
    -D OPENCV_ENABLE_NONFREE=OFF \
    -D CUDA_ARCH_BIN=6.0,6.1,7.0,7.5,8.0,8.6 \
    -D OPENCV_EXTRA_MODULES_PATH=/tmp/opencv_build/opencv_contrib/modules \
    -D BUILD_EXAMPLES=OFF \
    -D BUILD_LIBPROTOBUF_FROM_SOURCES=ON \
    -D INSTALL_TESTS=OFF .. && \
    make && \
    make install


## Link OpenCV, and include it in the Python path
RUN ln -s /opt/opencv/lib64/pkgconfig/opencv4.pc /usr/share/pkgconfig/ && \
    ldconfig && \
    ln -s /opt/opencv/lib/python3.8/site-packages/cv2 /opt/app-root/lib/python3.8/site-packages/cv2 && \
    fix-permissions /opt/app-root

##
# DLIB & Face recognition
##

RUN wget http://dlib.net/files/dlib-${DLIB_VERSION}.tar.bz2 && \
    tar xvf dlib* && \
    rm *.tar.bz2 && \
    cd dlib-${DLIB_VERSION} && \
    sed -i 's,forward_algo = forward_best_algo;,//forward_algo = forward_best_algo;,g' dlib/cuda/cudnn_dlibapi.cpp && \
    mkdir build && \
    cd build && \
    cmake .. -DDLIB_USE_CUDA=1 && \
    cmake --build . -- -j 5 && \
    python setup.py install && \
    pip install face_recognition

USER 1001
