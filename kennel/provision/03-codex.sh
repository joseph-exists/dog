# kennel/provision/03-codex.sh
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

if ! id -u dev >/dev/null 2>&1; then
  echo "Expected workspace user 'dev' to exist before applying 03-codex.sh" >&2
  exit 1
fi

# Scaffold for a prebaked Codex runtime image.
# Keep this layer focused on runtime installation and base machine setup.
# Repo clone, auth material, and launch commands still belong to spawn-time
# injection so ephemeral and persistent workspaces can diverge cleanly.
CODEX_VERSION="${CODEX_VERSION:-0.117.0}"

apt-get update && apt-get install -y \
  ripgrep \
  fd-find

su - dev -c "
  set -euo pipefail
  export NVM_DIR=\$HOME/.nvm
  . \$NVM_DIR/nvm.sh
  nvm use default >/dev/null
  npm install -g @openai/codex@${CODEX_VERSION}
  mkdir -p \$HOME/.config/codex
  mkdir -p \$HOME/.codex
  cat > \$HOME/.config/codex/kennel-runtime-note.txt << 'EOF'
This flavour preinstalls the Codex CLI for kennel-managed agent runtimes.
Use OPENAI_API_KEY for programmatic authentication or run codex login in a
trusted environment when interactive ChatGPT sign-in is acceptable.
EOF
"

CODEX_BIN="$(su - dev -c '
  set -euo pipefail
  export NVM_DIR=$HOME/.nvm
  . $NVM_DIR/nvm.sh
  nvm use default >/dev/null
  command -v codex exec --help
')"
ln -sf "$CODEX_BIN" /usr/local/bin/codex

apt-get clean && rm -rf /var/lib/apt/lists/*
