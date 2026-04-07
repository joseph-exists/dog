# kennel/provision/06-hermes-agent-dev.sh
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

if ! id -u dev >/dev/null 2>&1; then
  echo "Expected workspace user 'dev' to exist before applying 06-hermes-agent-dev.sh" >&2
  exit 1
fi

REPO_URL="${HERMES_AGENT_REPO_URL:-https://github.com/NousResearch/hermes-agent.git}"
REPO_DIR="${HERMES_AGENT_REPO_DIR:-/home/dev/hermes-agent}"
REPO_BRANCH="${HERMES_AGENT_REPO_BRANCH:-main}"

# Prepare a dev-focused Hermes Agent workspace with editable dependencies.
su - dev -c "
  set -euo pipefail
  export PATH=\$HOME/.local/bin:\$PATH

  if [ ! -d \"$REPO_DIR/.git\" ]; then
    git clone \"$REPO_URL\" \"$REPO_DIR\"
  fi

  cd \"$REPO_DIR\"
  git fetch --all --tags --prune
  git checkout \"$REPO_BRANCH\"
  git pull --ff-only origin \"$REPO_BRANCH\"

  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH=\$HOME/.local/bin:\$PATH

  uv venv venv --python 3.11
  . venv/bin/activate
  uv pip install -e '.[all,dev]'
  python -m pytest tests/ -q
"
