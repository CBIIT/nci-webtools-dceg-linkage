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

# install phantomjs
ENV PHANTOMJS_VERSION=2.1.1

# workaround for phantomjs, use --ignore-ssl-errors=true/yes --web-security=false/no to ignore ssl errors
ENV OPENSSL_CONF=/dev/null

RUN cd /tmp \
    && curl -L https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-${PHANTOMJS_VERSION}-linux-x86_64.tar.bz2 | tar -xj \
    && mv phantomjs-${PHANTOMJS_VERSION}-linux-x86_64/bin/phantomjs /usr/local/bin/phantomjs \
    && rm -rf phantomjs-${PHANTOMJS_VERSION}-linux-x86_64

ENV CPATH=$CPATH:/usr/include/httpd/:/usr/include/apr-1/

ENV LDLINK_HOME=/opt/ldlink

ENV LDLINK_HEALTHCHECK_PORT=8080

ENV LDLINK_HEALTHCHECK_PATH=/LDlinkRest/ping

ENV PYTHONPATH=${LDLINK_HOME}:${PYTHONPATH}

RUN mkdir -p ${LDLINK_HOME}

WORKDIR ${LDLINK_HOME}

COPY server/requirements.txt .

RUN python3 -m pip install -r requirements.txt

COPY server/ .

COPY --chown=apache:apache docker/wsgi.conf /etc/httpd/conf.d/wsgi.conf

RUN chown -R apache:apache ${LDLINK_HOME}

EXPOSE 80

EXPOSE 8080

CMD mod_wsgi-express start-server ${LDLINK_HOME}/LDlink.wsgi \
    --httpd-executable=/usr/sbin/httpd \
    --modules-directory /etc/httpd/modules/ \
    --include-file /etc/httpd/conf.d/wsgi.conf \
    --user apache \
    --group apache \
    --compress-responses \
    --trust-proxy-header X-Forwarded-For \
    --log-to-terminal \
    --access-log \
    --access-log-format "%h %{X-Forwarded-For}i %l %u %t \"%r\" %>s %b %T \"%{Referer}i\" \"%{User-Agent}i\"" \
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
    --processes $(((1 + `nproc`) / 2)) \
    --threads 1
