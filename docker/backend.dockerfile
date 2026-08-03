FROM public.ecr.aws/amazonlinux/amazonlinux:2023

ENV HTSLIB_VERSION=1.21
ENV PHANTOMJS_VERSION=2.1.1
ENV GECKODRIVER_VERSION=0.37.1
ENV DISPLAY=:99

ENV CPATH=/usr/include/httpd/:/usr/include/apr-1/
ENV LDLINK_HOME=/opt/ldlink
ENV LDLINK_HEALTHCHECK_PORT=8080
ENV LDLINK_HEALTHCHECK_PATH=/LDlinkRest/ping
ENV PYTHONPATH=${LDLINK_HOME}
ENV PIP_BREAK_SYSTEM_PACKAGES=1
ENV HOME=/usr/share/httpd
ENV TMPDIR=/tmp
ENV XDG_CACHE_HOME=/usr/share/httpd/.cache
ENV XDG_CONFIG_HOME=/usr/share/httpd/.config
ENV XDG_RUNTIME_DIR=/tmp/runtime-bokeh
ENV MOZ_HEADLESS=1
ENV MOZ_DISABLE_CONTENT_SANDBOX=1
ENV MOZ_DISABLE_GMP_SANDBOX=1
ENV MOZ_DISABLE_RDD_SANDBOX=1
ENV MOZ_DISABLE_SOCKET_PROCESS_SANDBOX=1

# Install required build/runtime dependencies
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
    libcap \
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
    firefox \
    shadow-utils \
    xorg-x11-server-Xvfb \
    make \
    && dnf clean all



RUN chmod 700 /usr/bin/python3.9
# Upgrade setuptools/wheel using Python 3.13.10
RUN python3.13 -m pip install --upgrade pip "setuptools>=78.1.1" wheel

RUN cd /tmp \
    && curl -L https://github.com/samtools/htslib/releases/download/${HTSLIB_VERSION}/htslib-${HTSLIB_VERSION}.tar.bz2 | tar -xj \
    && pushd htslib-${HTSLIB_VERSION} \
    && ./configure \
    && make \
    && make install \
    && popd \
    && rm -rf htslib-${HTSLIB_VERSION}

# Work around PhantomJS/OpenSSL config incompatibility on AL2023.
ENV OPENSSL_CONF=/dev/null

#RUN cd /tmp \
#    && curl -L https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-${PHANTOMJS_VERSION}-linux-x86_64.tar.bz2 | tar -xj \
#    && mv phantomjs-${PHANTOMJS_VERSION}-linux-x86_64/bin/phantomjs /usr/local/bin/phantomjs \
#    && rm -rf phantomjs-${PHANTOMJS_VERSION}-linux-x86_64
RUN cd /tmp \
    && curl -L https://github.com/Medium/phantomjs/releases/download/v${PHANTOMJS_VERSION}/phantomjs-${PHANTOMJS_VERSION}-linux-x86_64.tar.bz2 -o phantomjs.tar.bz2 \
    && tar -xjf phantomjs.tar.bz2 \
    && mv phantomjs-${PHANTOMJS_VERSION}-linux-x86_64/bin/phantomjs /usr/local/bin/phantomjs \
    && rm -rf phantomjs-${PHANTOMJS_VERSION}-linux-x86_64 phantomjs.tar.bz2

RUN ARCH=$(uname -m) && \
    if [ "$ARCH" = "x86_64" ]; then \
    GD_ARCH="linux64"; \
    elif [ "$ARCH" = "aarch64" ]; then \
    GD_ARCH="linux-aarch64"; \
    else \
    echo "Unsupported architecture: $ARCH"; exit 1; \
    fi && \
    cd /tmp && \
    curl -L "https://github.com/mozilla/geckodriver/releases/download/v${GECKODRIVER_VERSION}/geckodriver-v${GECKODRIVER_VERSION}-$GD_ARCH.tar.gz" -o geckodriver.tar.gz && \
    tar -xzf geckodriver.tar.gz && \
    mv geckodriver /usr/local/bin/ && \
    chmod +x /usr/local/bin/geckodriver && \
    ln -s /usr/local/bin/geckodriver /usr/bin/geckodriver && \
    rm geckodriver.tar.gz

RUN mkdir -p ${LDLINK_HOME}/apache-bin \
    && ln -sf /usr/bin/python3.13 ${LDLINK_HOME}/apache-bin/python3

RUN groupadd --gid 1000 bokeh \
    && useradd --uid 1000 --gid 1000 --home-dir /usr/share/httpd --shell /sbin/nologin bokeh

WORKDIR ${LDLINK_HOME}

COPY server/requirements.txt .

# Install pybedtools and pysam separately with --no-build-isolation to use system setuptools
RUN python3.13 -m pip install --no-cache-dir --no-build-isolation pybedtools==0.12.0 pysam==0.23.3

RUN python3.13 -m pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /var/cache/fontconfig \
    && chown -R bokeh:bokeh /var/cache/fontconfig

RUN setcap 'cap_net_bind_service=+ep' /usr/sbin/httpd

COPY server/ .
COPY --chown=apache:apache docker/wsgi.conf /etc/httpd/conf.d/wsgi.conf

RUN chown -R bokeh:bokeh ${LDLINK_HOME}

RUN mkdir -p /usr/share/httpd/.cache/selenium /usr/share/httpd/.config /usr/share/httpd/.mozilla /tmp/runtime-bokeh /local/content/analysistools_efs/ldlink/tmp \
    && chown -R bokeh:bokeh /usr/share/httpd/.cache /usr/share/httpd/.config /usr/share/httpd/.mozilla /tmp/runtime-bokeh /local/content/analysistools_efs/ldlink/tmp \
    && chmod 700 /tmp/runtime-bokeh

EXPOSE 80

EXPOSE 8080

USER bokeh

CMD PATH=${LDLINK_HOME}/apache-bin:$PATH flask --app bokehExport run & \
    PATH=${LDLINK_HOME}/apache-bin:$PATH mod_wsgi-express start-server ${LDLINK_HOME}/LDlink.wsgi \
    --httpd-executable=/usr/sbin/httpd \
    --modules-directory /etc/httpd/modules/ \
    --include-file /etc/httpd/conf.d/wsgi.conf \
    --user apache \
    --group apache \
    --compress-responses \
    --trust-proxy-header X-Forwarded-For \
    --log-to-terminal \
    --access-log \
    --access-log-format "%h %{X-Forwarded-For}i %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-Agent}i\"" combined \
    --port 80 \
    --working-directory ${LDLINK_HOME} \
    --header-buffer-size 50000000 \
    --response-buffer-size 50000000 \
    --limit-request-body 5368709120 \
    --max-clients 200 \
    --initial-workers 1 \
    --socket-timeout 9000 \
    --queue-timeout 9000 \
    --shutdown-timeout 9000 \
    --graceful-timeout 9000 \
    --connect-timeout 9000 \
    --request-timeout 9000 \
    --send-buffer-size 50000000 \
    --receive-buffer-size 50000000 \
    --processes $(((1 + `nproc`) / 2)) \
    --threads 1