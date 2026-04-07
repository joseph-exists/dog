# kennel/provision/04-hermes.sh
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

if ! id -u dev >/dev/null 2>&1; then
  echo "Expected workspace user 'dev' to exist before applying 04-hermes.sh" >&2
  exit 1
fi

# Prebaked Hermes Agent runtime image.
# Installs Hermes using the installer path validated in provisioned dev envs.
apt-get update && apt-get install -y ca-certificates curl

su - dev -c "
  set -euo pipefail
  export PATH=\$HOME/.local/bin:\$PATH
  curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash --skip-setup
  mkdir -p \$HOME/.config/hermes
  cat > \$HOME/.config/hermes/kennel-runtime-note.txt << 'EOF'
This flavour preinstalls Hermes Agent for kennel-managed agent runtimes.
Runtime launch/auth behavior can still be configured during workspace inject.
EOF
"

if su - dev -c 'export PATH=$HOME/.local/bin:$PATH && command -v hermes >/dev/null 2>&1'; then
  HERMES_BIN="$(su - dev -c 'export PATH=$HOME/.local/bin:$PATH && command -v hermes')"
  ln -sf "$HERMES_BIN" /usr/local/bin/hermes
elif su - dev -c 'export PATH=$HOME/.local/bin:$PATH && command -v hermes-agent >/dev/null 2>&1'; then
  HERMES_BIN="$(su - dev -c 'export PATH=$HOME/.local/bin:$PATH && command -v hermes-agent')"
  ln -sf "$HERMES_BIN" /usr/local/bin/hermes-agent
fi

apt-get clean && rm -rf /var/lib/apt/lists/*
