# Stage 1 – build the Next.js application
FROM public.ecr.aws/amazonlinux/amazonlinux:2023 AS builder

# Install build tools and Node.js 20 from NodeSource repository
RUN dnf -y update \
   && dnf -y install \
   gcc-c++ \
   make \
   tar \
   gzip \
   && curl -fsSL https://rpm.nodesource.com/setup_20.x | bash - \
   && dnf -y install nodejs \
   && dnf clean all

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

# Environment variables (NEXT_PUBLIC_* are baked into the build output)
ARG NEXT_PUBLIC_API_BASE_URL=localhost:8080
ENV NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL}

ARG NEXT_PUBLIC_BASE_URL=localhost
ENV NEXT_PUBLIC_BASE_URL=${NEXT_PUBLIC_BASE_URL}

ARG NEXT_PUBLIC_VERSION=local
ENV NEXT_PUBLIC_VERSION=${NEXT_PUBLIC_VERSION}

ARG GOOGLE_MAPS_API_KEY=none
ENV NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=${GOOGLE_MAPS_API_KEY}

RUN npm run build

# Stage 2 – runtime image without Python 3.9 RPM packages
FROM public.ecr.aws/amazonlinux/amazonlinux:2023

# Install Node.js 20 (needed for `next start`) and web server packages
RUN dnf -y update \
   && dnf -y install \
   httpd \
   tar \
   gzip \
   nginx \
   && curl -fsSL https://rpm.nodesource.com/setup_20.x | bash - \
   && dnf -y install nodejs \
   && dnf clean all

# Update npm at system prefix (/usr) so bundled dependencies under
# /usr/lib/node_modules/npm (including tar) are also updated.
RUN set -eux; \
   npm install -g npm@latest --prefix /usr; \
   npm install -g tar@7.5.11 --prefix /usr; \
   rm -rf /usr/lib/node_modules/npm/node_modules/tar; \
   cp -a /usr/lib/node_modules/tar /usr/lib/node_modules/npm/node_modules/tar;

# Remove distro Python 3.9 RPM packages to clear scanner findings.
# All dnf operations above are complete, so Python 3.9 is no longer needed.
RUN for pkg in $(rpm -qa | grep -E '^python3(-|$)|^python-srpm-macros'); do rpm -e --nodeps "$pkg" || true; done \
    && rm -f /usr/bin/python3.9 || true \
    && rm -rf /usr/lib64/python3.9 /usr/lib/python3.9

RUN mkdir -p /app/client

WORKDIR /app/client

# Copy only the artifacts needed to run the Next.js server
COPY --from=builder /app/client/package.json /app/client/
COPY --from=builder /app/client/node_modules /app/client/node_modules
COPY --from=builder /app/client/.next /app/client/.next
COPY --from=builder /app/client/public /app/client/public
COPY --from=builder /app/client/next.config.ts /app/client/

# Pass build ARGs through so the runtime container also carries the values
ARG NEXT_PUBLIC_API_BASE_URL=localhost:8080
ENV NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL}

ARG NEXT_PUBLIC_BASE_URL=localhost
ENV NEXT_PUBLIC_BASE_URL=${NEXT_PUBLIC_BASE_URL}

ARG NEXT_PUBLIC_VERSION=local
ENV NEXT_PUBLIC_VERSION=${NEXT_PUBLIC_VERSION}

ARG GOOGLE_MAPS_API_KEY=none
ENV NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=${GOOGLE_MAPS_API_KEY}

EXPOSE 80
EXPOSE 443

CMD npm run start