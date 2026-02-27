#!/bin/sh
set -eu

cmd="${SSH_ORIGINAL_COMMAND:-}"
if [ -z "$cmd" ]; then
  echo "Interactive shell disabled" >&2
  exit 1
fi

verb=$(printf '%s' "$cmd" | awk '{print $1}')
arg=$(printf '%s' "$cmd" | sed -E "s/^[^ ]+ '?([^']+)'?$/\1/")
arg=${arg#/}

case "$verb" in
  git-upload-pack|git-receive-pack|git-upload-archive)
    ;;
  *)
    echo "Unsupported command" >&2
    exit 1
    ;;
esac

case "$arg" in
  repos/*)
    repo_rel=${arg#repos/}
    ;;
  *)
    echo "Repository path must start with repos/" >&2
    exit 1
    ;;
esac

case "$repo_rel" in
  *..*|*//*|""|/*)
    echo "Invalid repository path" >&2
    exit 1
    ;;
esac

repo_path="/repos/$repo_rel"
repo_dir=$(dirname "$repo_path")
mkdir -p "$repo_dir"

if [ ! -d "$repo_path" ]; then
  git init --bare "$repo_path" >/dev/null 2>&1
fi

exec /usr/bin/git-shell -c "$verb '$repo_path'"
