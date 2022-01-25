
FROM quay.io/centos/centos:stream8

RUN dnf -y update \
    && dnf -y install \
    dnf-plugins-core \
    epel-release \
    glibc-langpack-en \
    && dnf config-manager --enable powertools \
    && dnf -y module enable nodejs:13 \
    && dnf -y install \
    gcc-c++ \
    make \
    httpd-devel \
    openssl-devel \
    bzip2 \
    bzip2-devel \
    libcurl-devel \
    zlib-devel \
    xz-devel \
    nodejs \
    python3-pip \
    python3-devel \
    && dnf clean all

RUN mkdir -p /deploy/app /deploy/logs /deploy/app/client/LDlink/tmp

# # install system node dependency for bokeh high quality image exports from svg
# RUN npm install -g phantomjs-prebuilt

WORKDIR /deploy/app

COPY . /deploy/app

# install python packages
RUN pip3 install --no-cache-dir --upgrade -r /deploy/app/requirements.txt

# install htslib
RUN cd /tmp \
    && curl https://github.com/samtools/htslib/releases/download/1.14/htslib-1.14.tar.bz2 --output htslib-1.14.tar.bz2 \
    && tar xjf htslib-1.14.tar.bz2 \
    && cd htslib-1.14 \
    && ./configure --enable-libcurl --prefix=/tmp/htslib-1.14 \
    && make && make install \
    && cd ./bin && mv * /usr/local/bin

# create ncianalysis user
RUN groupadd -g 4004 -o ncianalysis \
    && useradd -m -u 4004 -g 4004 -o -s /bin/bash ncianalysis
RUN chown -R ncianalysis:ncianalysis /deploy

WORKDIR /deploy/app/server

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
