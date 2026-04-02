#!/bin/bash
set -e

BASE_NAME="base-noble"
BASE_MARKER="/var/lib/lxc/.base-noble-snap0-ready"
LXC_BRIDGE="lxcbr0"
LXC_SUBNET="10.0.3.0/24"
LXC_GATEWAY="10.0.3.1"
DNSMASQ_PIDFILE="/run/dnsmasq-${LXC_BRIDGE}.pid"
DNSMASQ_LEASEFILE="/run/dnsmasq-${LXC_BRIDGE}.leases"
GITTIN_PROXY_LISTEN_HOST="${KENNEL_GITTIN_PROXY_LISTEN_HOST:-${LXC_GATEWAY}}"
GITTIN_PROXY_LISTEN_PORT="${KENNEL_GITTIN_PROXY_LISTEN_PORT:-3000}"
GITTIN_PROXY_TARGET_HOST="${KENNEL_GITTIN_PROXY_TARGET_HOST:-gittin}"
GITTIN_PROXY_TARGET_PORT="${KENNEL_GITTIN_PROXY_TARGET_PORT:-3000}"
GITTIN_PROXY_PIDFILE="/run/kennel-gittin-proxy.pid"

# Set up lxcbr0 if not present
if ! ip link show "${LXC_BRIDGE}" &>/dev/null; then
  ip link add "${LXC_BRIDGE}" type bridge
  ip addr add "${LXC_GATEWAY}/24" dev "${LXC_BRIDGE}"
  ip link set "${LXC_BRIDGE}" up
  echo "${LXC_BRIDGE} bridge initialized"
fi

# Enable IP forwarding for container networking
echo 1 > /proc/sys/net/ipv4/ip_forward

if ! iptables -t nat -C POSTROUTING -s "${LXC_SUBNET}" ! -d "${LXC_SUBNET}" -j MASQUERADE &>/dev/null; then
  iptables -t nat -A POSTROUTING -s "${LXC_SUBNET}" ! -d "${LXC_SUBNET}" -j MASQUERADE
fi

if [[ ! -f "${DNSMASQ_PIDFILE}" ]] || ! kill -0 "$(cat "${DNSMASQ_PIDFILE}")" &>/dev/null; then
  dnsmasq \
    --interface="${LXC_BRIDGE}" \
    --bind-interfaces \
    --dhcp-range=10.0.3.2,10.0.3.254,255.255.255.0,1h \
    --dhcp-option=3,"${LXC_GATEWAY}" \
    --dhcp-option=6,"${LXC_GATEWAY}",1.1.1.1,8.8.8.8 \
    --pid-file="${DNSMASQ_PIDFILE}" \
    --dhcp-leasefile="${DNSMASQ_LEASEFILE}"
fi

if [[ ! -f "${GITTIN_PROXY_PIDFILE}" ]] || ! kill -0 "$(cat "${GITTIN_PROXY_PIDFILE}")" &>/dev/null; then
  socat \
    TCP-LISTEN:"${GITTIN_PROXY_LISTEN_PORT}",bind="${GITTIN_PROXY_LISTEN_HOST}",fork,reuseaddr \
    TCP:"${GITTIN_PROXY_TARGET_HOST}":"${GITTIN_PROXY_TARGET_PORT}" &
  echo $! > "${GITTIN_PROXY_PIDFILE}"
fi

bootstrap_base_container() {
  if [[ -f "${BASE_MARKER}" ]]; then
    echo "kennel base container already provisioned"
    return
  fi

  echo "bootstrapping ${BASE_NAME}"

  if [[ ! -f "/var/lib/lxc/${BASE_NAME}/config" ]]; then
    lxc-create -n "${BASE_NAME}" -t download -- -d ubuntu -r noble -a amd64
  fi

  lxc-start -n "${BASE_NAME}"
  sleep 5
  lxc-attach -n "${BASE_NAME}" -- bash -s < /opt/kennel/provision/00-base.sh
  lxc-stop -n "${BASE_NAME}"

  if ! lxc-snapshot -L -n "${BASE_NAME}" | grep -q "snap0"; then
    lxc-snapshot -n "${BASE_NAME}" -c snap0
  fi

  touch "${BASE_MARKER}"
  echo "${BASE_NAME} bootstrap complete"
}

bootstrap_base_container

exec .venv/bin/uvicorn server:app --host 0.0.0.0 --port 8090
