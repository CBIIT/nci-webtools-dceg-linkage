FROM public.ecr.aws/amazonlinux/amazonlinux:2023

RUN dnf -y update \
   && dnf -y install \
   curl-minimal \
   gcc-c++ \
   httpd \
   make \
   tar \
   gzip \
   nginx \
   && dnf -y install nodejs24 \
   && dnf clean all

       # Restrict Python 3.9 to root only (security mitigation)
RUN chmod 700 /usr/bin/python3.9 

# Patch npm's bundled tar without replacing the distro-managed npm/npx binaries.
RUN set -eux; \
    npm_root="$(npm root -g)"; \
    npm_tar_dir="${npm_root}/npm/node_modules/tar"; \
    npm install --prefix /tmp/npm-tar-patch --install-strategy=nested --ignore-scripts --no-audit --no-fund tar@7.5.11; \
    rm -rf "${npm_tar_dir}"; \
    cp -a /tmp/npm-tar-patch/node_modules/tar "${npm_tar_dir}"; \
    rm -rf /tmp/npm-tar-patch; \
    test "$(node -p "require('${npm_tar_dir}/package.json').version")" = "7.5.11"


#RUN rm -f /usr/bin/python3.9 || true

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