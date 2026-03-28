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

apt-get update && apt-get install -y \
  ripgrep \
  fd-find

su - dev -c "
  mkdir -p \$HOME/.config/codex
  cat > \$HOME/.config/codex/kennel-runtime-note.txt << 'EOF'
This flavour is the scaffold for a prebaked Codex runtime image.
Install and version-pin the Codex CLI/runtime here once the packaging source
and authentication flow are finalized.
EOF
"

apt-get clean && rm -rf /var/lib/apt/lists/*
