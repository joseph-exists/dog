# kennel/provision/00-base.sh
# Run once inside a freshly created lxc container
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive

apt-get update && apt-get upgrade -y
apt-get install -y \
  ca-certificates \
  curl \
  wget \
  git \
  openssh-server \
  sudo \
  locales \
  tzdata \
  htop \
  less \
  jq \
  unzip \
  iputils-ping \
  dnsutils

# Locale
locale-gen en_US.UTF-8
update-locale LANG=en_US.UTF-8

# SSH — allow root with key only (no password)
sed -i 's/#PermitRootLogin.*/PermitRootLogin prohibit-password/' /etc/ssh/sshd_config
sed -i 's/PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl enable ssh

# Create and normalize the non-root workspace user used by all downstream flavours.
if ! getent group dev >/dev/null 2>&1; then
  groupadd dev
fi
if ! id -u dev >/dev/null 2>&1; then
  useradd -m -g dev -G sudo -s /bin/bash dev
fi
mkdir -p /home/dev
chown dev:dev /home/dev
usermod -d /home/dev -s /bin/bash -a -G sudo dev
echo "dev ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/dev
chmod 0440 /etc/sudoers.d/dev

apt-get clean && rm -rf /var/lib/apt/lists/*
