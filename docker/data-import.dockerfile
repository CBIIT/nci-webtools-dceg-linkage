FROM public.ecr.aws/amazonlinux/amazonlinux:2023

ENV LDLINK_HOME=/opt/ldlink
ENV PYTHONPATH=${LDLINK_HOME}
ENV PYTHONUNBUFFERED=1
ENV PIP_BREAK_SYSTEM_PACKAGES=1

# Install only the runtime packages needed by LDtrait_data.py.
RUN dnf -y update && \
    dnf -y install \
    python3.13 \
    python3.13-pip \
    && dnf clean all

# Upgrade setuptools/wheel using Python 3.13
RUN python3.13 -m pip install --upgrade pip "setuptools>=78.1.1" wheel

RUN mkdir -p ${LDLINK_HOME}/ldlink-bin \
    && ln -sf /usr/bin/python3.13 ${LDLINK_HOME}/ldlink-bin/python3

WORKDIR ${LDLINK_HOME}

RUN python3.13 -m pip install --no-cache-dir \
    boto3==1.42.39 \
    pymongo==4.18.3 \
    python-dateutil==2.8.2 \
    python-dotenv==1.1.1 \
    requests==2.33.1

# pip is not needed at runtime: drop it (and the distro's older copy), plus the distro Python 3.9.
RUN rpm -e --nodeps python3.13-pip python3 python3-libs \
    && python3.13 -m pip uninstall -y pip

COPY server/ .

CMD python3.13 LDtrait_data.py