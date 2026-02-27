# gittin (local SSH Git server)

This service exposes bare Git repos over SSH and stores them in `./volumes/shadows`.

## Behavior
- SSH user: `git`
- Repo root in container: `/repos`
- Shadow URL template: `ssh://git@gittin/repos/{entity_type}/{entity_id}.git`
- Missing repos are auto-created as bare repos on first access.

## Local key flow
- On first start, `gittin` generates `/ssh/id_ed25519` and `/ssh/id_ed25519.pub`.
- The public key is installed as the server's `authorized_keys`.
- Backend mounts the same `./gittin/ssh` directory at `/root/.ssh` and uses that key for clone/fetch/push.

This is intended for local development only.
