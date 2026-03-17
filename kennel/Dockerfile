FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

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
RUN chmod +x /opt/kennel/init.sh

CMD ["/opt/kennel/init.sh"]

# Python API server
WORKDIR /opt/kennel
COPY requirements.txt .
RUN python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

COPY src/ .

EXPOSE 8090
# After apt installs, before CMD:

# Pre-fetch ubuntu noble template cache
RUN lxc-create -n base-noble -t ubuntu -- --release noble 2>&1 | tail -5

# Copy and run base provisioning
COPY provision/00-base.sh /opt/kennel/provision/
RUN lxc-start -n base-noble && \
    sleep 5 && \
    lxc-attach -n base-noble -- bash /opt/kennel/provision/00-base.sh && \
    lxc-stop -n base-noble && \
    lxc-snapshot -n base-noble -c snap0

# cgroup mount needed before lxc works inside docker
CMD [".venv/bin/uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8090"]