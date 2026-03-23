FROM public.ecr.aws/amazonlinux/amazonlinux:2023

ENV PIP_BREAK_SYSTEM_PACKAGES=1

# Install Node.js 20 and Python 3.13 via RPM
RUN dnf -y update \
   && dnf -y install \
   curl-minimal \
   gcc-c++ \
   glibc-langpack-en \
   httpd \
   make \
   python3.13 \
   python3.13-pip \
   tar \
   gzip \
   nginx \
   && curl -fsSL https://rpm.nodesource.com/setup_20.x | bash - \
   && dnf -y install nodejs \
   && dnf clean all

RUN ln -sf /usr/bin/python3.13 /usr/bin/python3 \
   && ln -sf /usr/bin/python3.13 /usr/bin/python \
   && python3 --version

RUN python3 -m pip install --upgrade pip "setuptools>=78.1.1" wheel

# Update npm at system prefix (/usr) so bundled dependencies under
# /usr/lib/node_modules/npm (including tar) are also updated.
RUN set -eux; \
   npm install -g npm@latest --prefix /usr; \
   npm install -g tar@7.5.11 --prefix /usr; \
   rm -rf /usr/lib/node_modules/npm/node_modules/tar; \
   cp -a /usr/lib/node_modules/tar /usr/lib/node_modules/npm/node_modules/tar;

RUN mkdir -p /app/client

WORKDIR /app/client

COPY client/package.json /app/client/

RUN npm install

COPY client /app/client/

# Environment variables
ARG NEXT_PUBLIC_API_BASE_URL=localhost:8080
ENV NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL}

ARG NEXT_PUBLIC_BASE_URL=localhost
ENV NEXT_PUBLIC_BASE_URL=${NEXT_PUBLIC_BASE_URL}

ARG NEXT_PUBLIC_VERSION=local
ENV NEXT_PUBLIC_VERSION=${NEXT_PUBLIC_VERSION}

ARG GOOGLE_MAPS_API_KEY=none
ENV NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=${GOOGLE_MAPS_API_KEY}

RUN npm run build

EXPOSE 80
EXPOSE 443

CMD npm run start