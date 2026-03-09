FROM public.ecr.aws/amazonlinux/amazonlinux:2023

# install dependencies
RUN dnf -y update && \
    dnf -y install \
    python3.13 \
    python3.13-devel \
    python3.13-pip \
    python3.13-setuptools \
    python3.13-wheel \
    bzip2 \
    bzip2-devel \
    fontconfig \
    gcc \
    g++ \
    git \
    glibc-langpack-en \
    httpd \
    httpd-devel \
    libcurl-devel \
    ncurses-devel \
    openssl-devel \
    tar \
    xz-devel \
    zlib-devel \
    make \
    && dnf clean all

# Restrict Python 3.9 to root only (security mitigation)
RUN chmod 700 /usr/bin/python3.9 

# create python symlinks and upgrade setuptools/wheel using Python 3.13
RUN ln -sf /usr/bin/python3.13 /usr/bin/python3 && \
    ln -sf /usr/bin/python3.13 /usr/bin/python && \
    python3 -m pip install --upgrade "setuptools>=78.1.1" wheel

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

# Install setuptools and wheel first for building packages
RUN python3 -m pip install --no-cache-dir "setuptools>=78.1.1" wheel

# Install pybedtools and pysam separately with --no-build-isolation to use system setuptools
RUN python3 -m pip install --no-cache-dir --no-build-isolation pybedtools pysam==0.23.3

# Install remaining requirements
RUN python3 -m pip install -r requirements.txt

COPY server/ .

CMD ["python3", "LDtrait_data.py"]