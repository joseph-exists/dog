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
pip3 install --break-system-packages uv pipx
pipx ensurepath

# Node via nvm (user-level, more flexible than apt node)
su - dev -c "
  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
  source ~/.nvm/nvm.sh
  nvm install --lts
  nvm alias default node
"

# Your platform agent — the kennel-side component that
# handles workspace init, git clone on spawn, etc.
curl -fsSL https://your-platform/kennel-agent/install.sh | bash

apt-get clean && rm -rf /var/lib/apt/lists/*