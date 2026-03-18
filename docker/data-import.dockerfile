FROM public.ecr.aws/amazonlinux/amazonlinux:2023

ENV PYTHON_VERSION=3.13.10

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
    readline-devel \
    sqlite-devel \
    tar \
    xz-devel \
    zlib-devel \
    make \
    && dnf clean all

# Install exact CPython version
RUN cd /tmp \
    && curl -fsSLO "https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tgz" \
    && tar -xzf "Python-${PYTHON_VERSION}.tgz" \
    && cd "Python-${PYTHON_VERSION}" \
    && ./configure --enable-optimizations --enable-shared --with-ensurepip=install \
    && make -j"$(nproc)" \
    && make altinstall \
    && echo "/usr/local/lib" > /etc/ld.so.conf.d/python-local.conf \
    && ldconfig \
    && ln -sf /usr/local/bin/python3.13 /usr/bin/python3 \
    && ln -sf /usr/local/bin/python3.13 /usr/bin/python \
    && python3 --version \
    && rm -rf "/tmp/Python-${PYTHON_VERSION}" "/tmp/Python-${PYTHON_VERSION}.tgz"

# Remove legacy system Python 3.9 binary so scanners don't flag unused interpreter
RUN rm -f /usr/bin/python3.9 || true
# Restrict Python 3.9 to root only (security mitigation)
#RUN chmod 700 /usr/bin/python3.9 


# Upgrade setuptools/wheel using Python 3.13.10
RUN python3 -m pip install --upgrade pip "setuptools>=78.1.1" "tornado>=6.5.5" wheel

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
RUN python3 -m pip install --no-cache-dir "setuptools>=78.1.1" "tornado>=6.5.5" wheel

# Install pybedtools and pysam separately with --no-build-isolation to use system setuptools
RUN python3 -m pip install --no-cache-dir --no-build-isolation pybedtools pysam==0.23.3

# Install remaining requirements
RUN python3 -m pip install -r requirements.txt

COPY server/ .

CMD ["python3", "LDtrait_data.py"]