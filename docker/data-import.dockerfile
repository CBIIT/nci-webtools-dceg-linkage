FROM public.ecr.aws/amazonlinux/amazonlinux:2023

# install dependencies
RUN dnf -y update \
    && dnf -y install \
    bzip2 \
    bzip2-devel \
    fontconfig \
    gcc \
    glibc-langpack-en \
    httpd \
    httpd-devel \
    libcurl-devel \
    ncurses-devel \
    openssl-devel \
    python3 \
    python3-devel \
    python3-pip \
    python3-setuptools \
    python3-wheel \
    tar \
    xz-devel \
    zlib-devel \
    && dnf clean all

# install htslib
ENV HTSLIB_VERSION=1.16

RUN cd /tmp \
    && curl -L https://github.com/samtools/htslib/releases/download/${HTSLIB_VERSION}/htslib-${HTSLIB_VERSION}.tar.bz2 | tar -xj \
    && pushd htslib-${HTSLIB_VERSION} \
    && ./configure \
    && make \
    && make install \
    && popd \
    && rm -rf htslib-${HTSLIB_VERSION}

ENV CPATH=$CPATH:/usr/include/httpd/:/usr/include/apr-1/

ENV LDLINK_HOME=/opt/ldlink

ENV PYTHONPATH=${LDLINK_HOME}:${PYTHONPATH}

ENV PYTHONUNBUFFERED=1

RUN mkdir -p ${LDLINK_HOME}

WORKDIR ${LDLINK_HOME}

COPY server/requirements.txt .

RUN python3 -m pip install -r requirements.txt

COPY server/ .

CMD ["python3", "LDtrait_data.py"]