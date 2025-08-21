FROM public.ecr.aws/amazonlinux/amazonlinux:2023

RUN dnf -y update \
   && dnf -y install \
   gcc-c++ \
   httpd \
   make \
   nodejs \
   npm \
   nginx \
   && dnf clean all

RUN mkdir -p /app/client

WORKDIR /app/client

COPY client/package.json /app/client/

RUN npm install

COPY client /app/client/

ARG NEXT_PUBLIC_BASE_URL=localhost
ENV NEXT_PUBLIC_BASE_URL=${NEXT_PUBLIC_BASE_URL}

ARG GOOGLE_MAPS_API_KEY=none
ENV NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=${GOOGLE_MAPS_API_KEY}
RUN npm run build 

EXPOSE 80
EXPOSE 443

CMD npm run start
