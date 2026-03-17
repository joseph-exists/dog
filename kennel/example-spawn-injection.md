
```python
async def _inject_workspace(name: str, workspace_config: dict):
    """
    Called after lxc-start — injects user-specific config.
    workspace_config comes from your backend (user identity,
    repo to clone, env vars, SSH keys etc.)
    """
    cmds = [
        # Inject SSH public key
        f"mkdir -p /home/dev/.ssh && echo '{workspace_config['ssh_pubkey']}' "
        f"> /home/dev/.ssh/authorized_keys && chmod 600 /home/dev/.ssh/authorized_keys",

        # Set git identity
        f"git config --global user.email '{workspace_config['email']}'",
        f"git config --global user.name '{workspace_config['name']}'",

        # Clone their repo
        f"git clone {workspace_config['repo_url']} /home/dev/workspace",

        # Inject any platform env vars
        f"echo '{workspace_config['env_vars']}' >> /home/dev/.bashrc",
    ]
    for cmd in cmds:
        subprocess.run(
            ["lxc-attach", "-n", name, "--", "bash", "-c", cmd],
            timeout=30
        )
```