# kennel/provision/04-hermes.sh
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

if ! id -u dev >/dev/null 2>&1; then
  echo "Expected workspace user 'dev' to exist before applying 04-hermes.sh" >&2
  exit 1
fi

# Scaffold for a prebaked Hermes runtime image.
# This layer is intentionally conservative until the Hermes packaging,
# authentication, and long-running service contract are finalized.

apt-get update && apt-get install -y \
  ripgrep \
  fd-find

su - dev -c "
  mkdir -p \$HOME/.config/hermes
  cat > \$HOME/.config/hermes/kennel-runtime-note.txt << 'EOF'
This flavour is the scaffold for a prebaked Hermes runtime image.
Install and version-pin the Hermes runtime here once its distribution and
service launch contract are finalized.
EOF
"

apt-get clean && rm -rf /var/lib/apt/lists/*
