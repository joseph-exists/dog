# scripts/init.sh
#!/bin/bash
set -e

# Set up lxcbr0 if not present
if ! ip link show lxcbr0 &>/dev/null; then
  ip link add lxcbr0 type bridge
  ip addr add 10.0.3.1/24 dev lxcbr0
  ip link set lxcbr0 up
  echo "lxcbr0 bridge initialized"
fi

# Enable IP forwarding for container networking
echo 1 > /proc/sys/net/ipv4/ip_forward

exec .venv/bin/uvicorn server:app --host 0.0.0.0 --port 8090