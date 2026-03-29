# kennel/provision/05-claude-code.sh
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

if ! id -u dev >/dev/null 2>&1; then
  echo "Expected workspace user 'dev' to exist before applying 05-claude-code.sh" >&2
  exit 1
fi

# Prebaked Claude Code runtime image.
# Anthropic's current documented standard install path is npm-based, while a
# native installer also exists. We use npm here because Node is already part of
# the dev flavour and the version can be pinned deterministically during rebuild.
CLAUDE_CODE_VERSION="${CLAUDE_CODE_VERSION:-2.1.86}"

apt-get update && apt-get install -y \
  ripgrep \
  fd-find

su - dev -c "
  set -euo pipefail
  export NVM_DIR=\$HOME/.nvm
  . \$NVM_DIR/nvm.sh
  nvm use default >/dev/null
  npm install -g @anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}
  mkdir -p \$HOME/.claude
  cat > \$HOME/.claude/kennel-runtime-note.txt << 'EOF'
This flavour preinstalls Claude Code for kennel-managed agent runtimes.
The remote-control runtime requires Claude account authentication and a
supported subscription. Run claude auth or use the appropriate enterprise
provider configuration before starting remote-control sessions.
EOF
"

CLAUDE_BIN="$(su - dev -c '
  set -euo pipefail
  export NVM_DIR=$HOME/.nvm
  . $NVM_DIR/nvm.sh
  nvm use default >/dev/null
  command -v claude
')"
ln -sf "$CLAUDE_BIN" /usr/local/bin/claude

apt-get clean && rm -rf /var/lib/apt/lists/*
