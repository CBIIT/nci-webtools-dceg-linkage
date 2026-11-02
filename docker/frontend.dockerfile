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

# Patch npm's bundled tar without replacing the distro-managed npm/npx binaries.
RUN set -eux; \
    npm_root="$(npm root -g)"; \
    npm_tar_dir="${npm_root}/npm/node_modules/tar"; \
    npm install --prefix /tmp/npm-tar-patch --install-strategy=nested --ignore-scripts --no-audit --no-fund tar@7.5.11; \
    rm -rf "${npm_tar_dir}"; \
    cp -a /tmp/npm-tar-patch/node_modules/tar "${npm_tar_dir}"; \
    rm -rf /tmp/npm-tar-patch; \
    test "$(node -p "require('${npm_tar_dir}/package.json').version")" = "7.5.11"

# Patch vulnerable packages bundled with the distro's npm (CVE-2026-102278, CVE-2026-118764,
# CVE-2026-118773, CVE-2026-104844, CVE-2026-101910/101911/101912/101913).
RUN set -eux; \
    npm_modules="$(npm root -g)/npm/node_modules"; \
    for spec in brace-expansion@5.0.12 minimatch@11.0.1 glob@14.0.2 postcss-selector-parser@7.1.6 ip-address@10.7.1; do \
        name="${spec%@*}"; version="${spec##*@}"; \
        npm install --prefix "/tmp/npm-patch-${name}" --install-strategy=nested --ignore-scripts --no-audit --no-fund "${spec}"; \
        rm -rf "${npm_modules}/${name}"; \
        cp -a "/tmp/npm-patch-${name}/node_modules/${name}" "${npm_modules}/${name}"; \
        rm -rf "/tmp/npm-patch-${name}"; \
        test "$(node -p "require('${npm_modules}/${name}/package.json').version")" = "${version}"; \
    done; \
    npm --version

RUN mkdir -p /app/client

WORKDIR /app/client

COPY client/package.json client/package-lock.json /app/client/

RUN npm ci

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

# Remove the distro Python 3.9 (CVE-2025-12781); it is only needed by dnf, which is not used past this point.
RUN rpm -e --nodeps python3 python3-libs

EXPOSE 80
EXPOSE 443

CMD npm run start