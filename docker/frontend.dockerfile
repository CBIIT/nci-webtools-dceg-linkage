FROM public.ecr.aws/amazonlinux/amazonlinux:2023

RUN dnf -y update \
    && dnf -y install httpd \
    && dnf clean all

COPY docker/frontend.conf /etc/httpd/conf.d/frontend.conf

WORKDIR /var/www/html

COPY client .

RUN chown -R apache:apache .

EXPOSE 80
EXPOSE 443

CMD rm -rf /run/httpd/* /tmp/httpd* \
    && exec /usr/sbin/httpd -DFOREGROUND