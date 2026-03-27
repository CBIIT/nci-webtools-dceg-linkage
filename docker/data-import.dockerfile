FROM public.ecr.aws/amazonlinux/amazonlinux:2023

ENV HTSLIB_VERSION=1.16

ENV CPATH=/usr/include/httpd/:/usr/include/apr-1/
ENV LDLINK_HOME=/opt/ldlink
ENV PYTHONPATH=${LDLINK_HOME}
ENV PYTHONUNBUFFERED=1
ENV PIP_BREAK_SYSTEM_PACKAGES=1

# install dependencies
RUN dnf -y update && \
    dnf -y install \
    bzip2 \
    bzip2-devel \
    curl-minimal \
    fontconfig \
    gcc \
    g++ \
    git \
    glibc-langpack-en \
    httpd \
    httpd-devel \
    libcurl-devel \
    libffi-devel \
    ncurses-devel \
    openssl-devel \
    python3.13 \
    python3.13-devel \
    python3.13-pip \
    readline-devel \
    sqlite-devel \
    tar \
    xz-devel \
    zlib-devel \
    make \
    && dnf clean all

    # Restrict Python 3.9 to root only (security mitigation)
RUN chmod 700 /usr/bin/python3.9 

# Upgrade setuptools/wheel using Python 3.13
RUN python3.13 -m pip install --upgrade "setuptools>=78.1.1" wheel

RUN cd /tmp \
    && curl -L https://github.com/samtools/htslib/releases/download/${HTSLIB_VERSION}/htslib-${HTSLIB_VERSION}.tar.bz2 | tar -xj \
    && pushd htslib-${HTSLIB_VERSION} \
    && ./configure \
    && make \
    && make install \
    && popd \
    && rm -rf htslib-${HTSLIB_VERSION}

RUN mkdir -p ${LDLINK_HOME}/ldlink-bin \
    && ln -sf /usr/bin/python3.13 ${LDLINK_HOME}/ldlink-bin/python3

WORKDIR ${LDLINK_HOME}

COPY server/requirements.txt .

# Install pybedtools and pysam separately with --no-build-isolation to use system setuptools
RUN python3.13 -m pip install --no-cache-dir --no-build-isolation pybedtools==0.12.0 pysam==0.23.3

# Install remaining requirements
RUN python3.13 -m pip install --no-cache-dir -r requirements.txt

COPY server/ .

CMD ["env", "PATH=/opt/ldlink/ldlink-bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin", "python3", "LDtrait_data.py"]