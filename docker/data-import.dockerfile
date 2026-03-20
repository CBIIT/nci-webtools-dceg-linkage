FROM public.ecr.aws/amazonlinux/amazonlinux:2023 AS builder

ENV PYTHON_VERSION=3.13.10
ENV PYTHON_SHA256=de5930852e95ba8c17b56548e04648470356ac47f7506014664f8f510d7bd61b
ENV HTSLIB_VERSION=1.16

ENV CPATH=/usr/include/httpd/:/usr/include/apr-1/
ENV LDLINK_HOME=/opt/ldlink
ENV PYTHONPATH=${LDLINK_HOME}
ENV PYTHONUNBUFFERED=1

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
    && echo "${PYTHON_SHA256}  Python-${PYTHON_VERSION}.tgz" | sha256sum -c - \
    && tar -xzf "Python-${PYTHON_VERSION}.tgz" \
    && cd "Python-${PYTHON_VERSION}" \
    && ./configure --enable-shared --with-ensurepip=install \
    && make -j"$(nproc)" \
    && make altinstall \
    && echo "/usr/local/lib" > /etc/ld.so.conf.d/python-local.conf \
    && ldconfig \
    && ln -sf /usr/local/bin/python3.13 /usr/bin/python3 \
    && ln -sf /usr/local/bin/python3.13 /usr/bin/python \
    && python3 --version \
    && rm -rf "/tmp/Python-${PYTHON_VERSION}" "/tmp/Python-${PYTHON_VERSION}.tgz"

# Upgrade setuptools/wheel using Python 3.13.10
RUN python3 -m pip install --upgrade pip "setuptools>=78.1.1" wheel

RUN cd /tmp \
    && curl -L https://github.com/samtools/htslib/releases/download/${HTSLIB_VERSION}/htslib-${HTSLIB_VERSION}.tar.bz2 | tar -xj \
    && pushd htslib-${HTSLIB_VERSION} \
    && ./configure \
    && make \
    && make install \
    && popd \
    && rm -rf htslib-${HTSLIB_VERSION}

RUN mkdir -p ${LDLINK_HOME}

WORKDIR ${LDLINK_HOME}

COPY server/requirements.txt .

# Install setuptools and wheel first for building packages
RUN python3 -m pip install --no-cache-dir "setuptools>=78.1.1" wheel

# Install pybedtools and pysam separately with --no-build-isolation to use system setuptools
RUN python3 -m pip install --no-cache-dir --no-build-isolation pybedtools==0.12.0 pysam==0.23.3

# Install remaining requirements
RUN python3 -m pip install --no-cache-dir -r requirements.txt

COPY server/ .

FROM public.ecr.aws/amazonlinux/amazonlinux:2023

ENV PYTHON_VERSION=3.13.10
ENV HTSLIB_VERSION=1.16

ENV CPATH=/usr/include/httpd/:/usr/include/apr-1/
ENV LDLINK_HOME=/opt/ldlink
ENV PYTHONPATH=${LDLINK_HOME}
ENV PYTHONUNBUFFERED=1

# Install runtime dependencies before removing distro Python packages.
# Build tooling and *-devel packages are only needed in the builder stage.
RUN dnf -y update && \
    dnf -y install \
    curl-minimal \
    fontconfig \
    glibc-langpack-en \
    httpd \
    tar \
    && dnf clean all

COPY --from=builder /usr/local /usr/local
COPY --from=builder /opt/ldlink /opt/ldlink

# Remove distro Python packages to avoid scanner findings and keep only Python 3.13.
RUN for pkg in $(rpm -qa | grep -E '^python3(-|$)|^python-srpm-macros'); do rpm -e --nodeps "$pkg" || true; done \
    && rm -f /usr/bin/python3.9 || true \
    && rm -rf /usr/lib64/python3.9 /usr/lib/python3.9 \
    && ln -sf /usr/local/bin/python3.13 /usr/bin/python3 \
    && ln -sf /usr/local/bin/python3.13 /usr/bin/python \
    && echo "/usr/local/lib" > /etc/ld.so.conf.d/python-local.conf \
    && ldconfig \
    && python3 --version

WORKDIR ${LDLINK_HOME}

CMD ["python3", "LDtrait_data.py"]