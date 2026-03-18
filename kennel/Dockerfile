FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update && apt-get install -y \
    lxc \
    lxc-templates \
    lxc-utils \
    uidmap \
    bridge-utils \
    iproute2 \
    iptables \
    dnsmasq \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# LXC storage and runtime dirs
RUN mkdir -p /var/lib/lxc /var/log/lxc /run/lxc

# LXC default network config
COPY conf/lxc-default.conf /etc/lxc/default.conf
COPY conf/lxc-usernet /etc/lxc/lxc-usernet
COPY scripts/init.sh /opt/kennel/init.sh
COPY provision /opt/kennel/provision
RUN chmod +x /opt/kennel/init.sh

# Python API server
WORKDIR /opt/kennel
COPY requirements.txt .
RUN python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

COPY src/ .

EXPOSE 8090

CMD ["/opt/kennel/init.sh"]
