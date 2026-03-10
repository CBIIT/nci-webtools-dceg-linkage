FROM public.ecr.aws/amazonlinux/amazonlinux:2023

# Install Node.js 20 from NodeSource repository
RUN dnf -y update \
   && dnf -y install \
   gcc-c++ \
   httpd \
   make \
   tar \
   gzip \
   nginx \
   && curl -fsSL https://rpm.nodesource.com/setup_20.x | bash - \
   && dnf -y install nodejs \
   && dnf clean all

# Remove legacy system Python 3.9 binary so scanners don't flag unused interpreter
RUN rm -f /usr/bin/python3.9 || true
# Update npm at system prefix (/usr) so bundled dependencies under
# /usr/lib/node_modules/npm (including tar) are also updated.
RUN npm install -g npm@latest

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
