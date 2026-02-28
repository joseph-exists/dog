# gittin (Gogs service)

`gittin` now boots a persistent Gogs instance instead of the ad hoc SSH-only Git server.

## Storage layout
- Managed repositories: `./volumes/shadows` -> `/data/git`
- Gogs app state: `./gittin/data` -> `/data/gogs`
- SSH host/user material: `./gittin/ssh` -> `/data/ssh`

## Runtime behavior
- Web UI inside container: `3000`
- Builtin SSH server inside container: `2222`
- Local dev ports from [`docker-compose.override.yml`](/home/josep/dog/docker-compose.override.yml): `http://localhost:3001` and `ssh://git@localhost:2222`
- Production web route from [`docker-compose.yml`](/home/josep/dog/docker-compose.yml): `https://git.${DOMAIN}`

## First start
On first boot, [`entrypoint.sh`](/home/josep/dog/gittin/entrypoint.sh) writes `/data/gogs/conf/app.ini` if it does not already exist. The generated config:
- keeps repository data under `/data/git`
- enables the builtin SSH server on port `2222`
- leaves `INSTALL_LOCK = false` so the web installer can create the initial admin account
- allows self-registration by default unless overridden with `GITTIN_DISABLE_REGISTRATION=true`

After the installer runs, Gogs persists its final configuration in `./gittin/data/conf/app.ini` and later restarts reuse it unchanged.

## Current integration status
This replaces the container runtime only. It does not yet recreate the old "auto-create missing repo on first git access" behavior for shadow repos, so backend shadow sync should remain local-only until a repo provisioning path is added.

## Provisioning Notes
- Do not store personal access tokens in this file.
- Keep the `shadow-alpha` PAT in local secrets or `.env`, not in tracked documentation.
- If a token was pasted here previously, rotate it in Gogs and replace it only in local secret storage.
