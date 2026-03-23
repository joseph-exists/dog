# kennel/provision/01-dev.sh
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

# Build essentials
apt-get update && apt-get install -y \
  build-essential \
  pkg-config \
  libssl-dev \
  libffi-dev

# Python
apt-get install -y python3 python3-pip python3-venv python3-dev
pip3 install --break-system-packages pipx
su - dev -c "pipx ensurepath"
su - dev -c "pipx install uv"

# Node via nvm (user-level, more flexible than apt node)
su - dev -c "
  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
  source ~/.nvm/nvm.sh
  nvm install --lts
  nvm alias default node
"

# Ensure nvm is auto-sourced in ~/.bashrc for subsequent sessions
su - dev -c "
  grep -q 'export NVM_DIR' \$HOME/.bashrc || cat >> \$HOME/.bashrc << 'NVMEOF'

# nvm — node version manager
export NVM_DIR=\"\$HOME/.nvm\"
[ -s \"\$NVM_DIR/nvm.sh\" ] && source \"\$NVM_DIR/nvm.sh\"
[ -s \"\$NVM_DIR/bash_completion\" ] && source \"\$NVM_DIR/bash_completion\"
NVMEOF
"

# Your platform agent — the kennel-side component that
# handles workspace init, git clone on spawn, etc.
# curl -fsSL https://your-platform/kennel-agent/install.sh | bash

apt-get clean && rm -rf /var/lib/apt/lists/*