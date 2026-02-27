#!/bin/sh
set -eu

SSH_DIR=/ssh
GIT_HOME=/home/git

mkdir -p "$SSH_DIR" "$GIT_HOME/.ssh" /repos /var/run/sshd
chown -R git:git "$GIT_HOME" /repos "$SSH_DIR"
# Alpine can mark newly created users as locked; sshd rejects locked users
# even when pubkey auth is configured.
passwd -d git >/dev/null 2>&1 || true

# Create client keypair once and reuse via bind mount (local dev only).
if [ ! -f "$SSH_DIR/id_ed25519" ]; then
  ssh-keygen -t ed25519 -N "" -f "$SSH_DIR/id_ed25519"
fi
chmod 600 "$SSH_DIR/id_ed25519"
chmod 644 "$SSH_DIR/id_ed25519.pub"

cp "$SSH_DIR/id_ed25519.pub" "$GIT_HOME/.ssh/authorized_keys"
chmod 700 "$GIT_HOME/.ssh"
chmod 600 "$GIT_HOME/.ssh/authorized_keys"
chown -R git:git "$GIT_HOME/.ssh"

# Server host keys
ssh-keygen -A

cat > /etc/ssh/sshd_config <<'SSHD_EOF'
Port 22
Protocol 2
HostKey /etc/ssh/ssh_host_rsa_key
HostKey /etc/ssh/ssh_host_ecdsa_key
HostKey /etc/ssh/ssh_host_ed25519_key
UsePAM no
PasswordAuthentication no
PubkeyAuthentication yes
PermitRootLogin no
AllowUsers git
AuthorizedKeysFile .ssh/authorized_keys
StrictModes no
Subsystem sftp /usr/lib/ssh/sftp-server
Match User git
    ForceCommand /usr/local/bin/gittin-shell.sh
SSHD_EOF

echo "[gittin] Ready. Repos root: /repos"
exec /usr/sbin/sshd -D -e
