# kennel/provision/02-cuda.sh
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

# ── CUDA Toolkit ──────────────────────────────────────────────────────────────
apt-get update && apt-get install -y --no-install-recommends \
  gnupg2 \
  ca-certificates \
  wget

wget -qO /tmp/cuda-keyring.deb \
  https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2404/x86_64/cuda-keyring_1.1-1_all.deb
dpkg -i /tmp/cuda-keyring.deb
rm /tmp/cuda-keyring.deb

apt-get update && apt-get install -y --no-install-recommends \
  cuda-toolkit-12-8 \
  libcudnn9-cuda-12 \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# ── Library paths ─────────────────────────────────────────────────────────────
cat > /etc/ld.so.conf.d/cuda-wsl.conf << 'EOF'
/usr/local/cuda/lib64
/usr/lib/wsl/lib
EOF
ldconfig

# ── CUDA environment — system-wide via /etc/profile.d ────────────────────────
# Using profile.d rather than /etc/environment so it's sourced as a shell
# script and PATH concatenation works correctly across overlay layers.
cat > /etc/profile.d/cuda.sh << 'EOF'
export CUDA_HOME=/usr/local/cuda
export PATH=/usr/local/cuda/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/cuda/lib64:/usr/lib/wsl/lib:${LD_LIBRARY_PATH:-}
EOF
chmod +x /etc/profile.d/cuda.sh

# ── PyTorch ───────────────────────────────────────────────────────────────────
# Explicitly reconstruct the dev user's PATH from known install locations
# rather than relying on login shell to source it from parent overlay layers.
DEV_HOME=/home/dev
DEV_USER=dev

# Paths that 01-dev.sh wrote into the parent (base-dev) layer
PIPX_BIN="$DEV_HOME/.local/bin"
NVM_DIR="$DEV_HOME/.nvm"
UV_BIN="$PIPX_BIN/uv"

# Verify uv is reachable before proceeding
if [ ! -f "$UV_BIN" ]; then
  echo "ERROR: uv not found at $UV_BIN"
  echo "Contents of $PIPX_BIN:"
  ls -la "$PIPX_BIN" 2>/dev/null || echo "(directory missing)"
  echo "Overlay layer contents of /home/dev:"
  ls -la "$DEV_HOME"
  exit 1
fi

su - "$DEV_USER" -c "
  set -euo pipefail

  # Explicitly source profile.d so CUDA paths are available
  source /etc/profile.d/cuda.sh

  # Reconstruct PATH from known locations in parent layers
  export PATH=\"$PIPX_BIN:\$HOME/.nvm/versions/node/\$(ls \$HOME/.nvm/versions/node/ 2>/dev/null | tail -1)/bin:\$PATH\"

  echo '[cuda] using uv:' \$(which uv)
  echo '[cuda] CUDA_HOME:' \$CUDA_HOME

  # Create torch venv
  uv venv $DEV_HOME/.venvs/torch --python 3.12

  # Install PyTorch with CUDA 12.8 wheels
  uv pip install \
    --python $DEV_HOME/.venvs/torch/bin/python \
    torch torchvision torchaudio \
    --index-url https://download.pytorch.org/whl/cu128

  echo '[cuda] torch install complete'
"

# ── Activate torch venv by default for dev user ───────────────────────────────
# Append to .bashrc only if not already present
grep -q 'venvs/torch' "$DEV_HOME/.bashrc" 2>/dev/null || \
  echo 'source /home/dev/.venvs/torch/bin/activate' >> "$DEV_HOME/.bashrc"

# ── Smoke test: import only, no GPU device needed at provision time ───────────
su - "$DEV_USER" -c "
  source /home/dev/.venvs/torch/bin/activate
  python -c 'import torch; print(f\"torch {torch.__version__} installed OK\")'
"

# ── nvidia-smi symlink from WSL2 lib mount ────────────────────────────────────
ln -sf /usr/lib/wsl/lib/nvidia-smi /usr/local/bin/nvidia-smi

echo '02-cuda.sh complete'