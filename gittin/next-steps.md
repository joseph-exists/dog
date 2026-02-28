## Review

The original note was directionally right, but it mixed upstream Docker docs with local implementation decisions. The important local constraints are:

- Keep bind-mounted storage under the repo, especially `./volumes/shadows`
- Add a real web UI that can sit behind HTTPS
- Preserve optional SSH access for Git operations
- Avoid breaking backend shadow flows while repo provisioning is still unfinished

## Implemented

The current `gittin` implementation now does this:

- builds from `gogs/gogs:next-latest`
- stores repositories in `./volumes/shadows` mounted at `/data/git`
- stores Gogs state in `./gittin/data`
- stores SSH material in `./gittin/ssh`
- exposes the Gogs web app on container port `3000`
- enables the builtin Gogs SSH server on container port `2222`
- routes production web traffic through Traefik at `https://git.${DOMAIN}`
- exposes local dev ports at `http://localhost:3001` and `localhost:2222`

## First-run flow

On first start, [`entrypoint.sh`](/home/josep/dog/gittin/entrypoint.sh) writes a starter `app.ini` only if one does not already exist. That config leaves `INSTALL_LOCK = false`, so the web installer can create the first admin user and save the final settings persistently.

## Remaining work

The old SSH shell auto-created missing bare repos on first access. Gogs does not do that. The backend also no longer has a live Forgejo/Gogs repo creation path. Because of that, Compose now defaults `SHADOW_REPO_URL_TEMPLATE` to empty so shadow versioning stays local-only until remote repo provisioning is implemented.

The next implementation slice should be:

1. Create a deterministic shadow repo naming scheme inside Gogs.
2. Add a provisioning path that creates repos before the worker tries to clone or push.
3. Decide whether backend sync should use HTTPS tokens or SSH deploy keys.
4. Re-enable `SHADOW_REPO_URL_TEMPLATE` once repo provisioning is wired and tested.

## Follow-on

User-visible repo groundwork is now the next active track:

1. Provision repos under the `dog` org via a dedicated service account.
2. Support multiple repos per user by using one repo record UUID per repo.
3. Name repos as `dog/{slug}-{short_id}` where `short_id` is derived from the repo record UUID.
