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

● Excellent question! These are actually two separate systems that both use your Gogs instance (gittin), but for different purposes.

  ★ Insight ─────────────────────────────────────
  Two Gogs Consumers, Two Orgs:
  - Shadow System (shadow org) → Internal entity versioning, background worker
  - User Repo System (dog org) → User-visible repos, synchronous API calls

  They share the same Gogs server but are isolated by organization.
  ─────────────────────────────────────────────────

  Comparison
  ┌───────────────┬────────────────────────────────────────────────┬──────────────────────────────────────────────┐
  │    Aspect     │              shadow_outbox_worker              │              user_repo_service               │
  ├───────────────┼────────────────────────────────────────────────┼──────────────────────────────────────────────┤
  │ Purpose       │ Internal entity snapshots (rooms, agents)      │ User-controlled repositories                 │
  ├───────────────┼────────────────────────────────────────────────┼──────────────────────────────────────────────┤
  │ Gogs Org      │ shadow                                         │ dog                                          │
  ├───────────────┼────────────────────────────────────────────────┼──────────────────────────────────────────────┤
  │ Config Vars   │ SHADOW_GOGS_*                                  │ USER_REPO_GOGS_*                             │
  ├───────────────┼────────────────────────────────────────────────┼──────────────────────────────────────────────┤
  │ Execution     │ Background worker (polls DB)                   │ Synchronous (API request)                    │
  ├───────────────┼────────────────────────────────────────────────┼──────────────────────────────────────────────┤
  │ Workflow      │ Outbox pattern: queue → worker → commit → push │ Direct: API call → provision in Gogs         │
  ├───────────────┼────────────────────────────────────────────────┼──────────────────────────────────────────────┤
  │ Import Source │ Internal snapshots only                        │ Can import from external URLs (GitHub, etc.) │
  └───────────────┴────────────────────────────────────────────────┴──────────────────────────────────────────────┘
  Architecture Diagram

  ┌─────────────────────────────────────────────────────────────────────────┐
  │                           Gogs (gittin:3000)                            │
  │  ┌─────────────────────────────┐   ┌─────────────────────────────────┐  │
  │  │    shadow org               │   │         dog org                 │  │
  │  │  • room-{uuid}              │   │  • user-repo-{slug}-{uuid}      │  │
  │  │  • agent-{uuid}             │   │  • imported-from-github         │  │
  │  │  (internal snapshots)       │   │  (user-visible repos)           │  │
  │  └─────────────────────────────┘   └─────────────────────────────────┘  │
  └─────────────────────────────────────────────────────────────────────────┘
             ▲                                      ▲
             │                                      │
      shadow-outbox-worker                    backend (API)
      (background, async)                   (synchronous)
             ▲                                      ▲
             │                                      │
      ShadowOutboxJob table              POST /api/v1/user-repos/

  Does user_repo_service Need a Worker?

  Currently no - it runs synchronously during API requests. However, looking at the code:

  def clone_user_repo_from_external_source(...):
      # ...
      repo = self.create_user_repo_db_only(...)
      # This blocks the API request while Gogs clones from external URL
      self.ensure_user_repo_remote(session=session, user_repo=repo)

  The _migrate_repo call (line 158) uses Gogs' /api/v1/repos/migrate endpoint which clones from external sources. For large repos, this could
  timeout.

  If you wanted to make user repo imports async, you could follow the same outbox pattern:
  1. Create a UserRepoOutboxJob table
  2. Add a user-repo-worker service
  3. API creates DB record → returns immediately → worker provisions asynchronously

  But that's an enhancement, not required for current functionality.

  Docker Integration for User Repo Service

  The backend service already has the right environment variables:

  # From  .env (already configured)
  USER_REPO_GOGS_TOKEN (hidden)
  USER_REPO_GOGS_ORG=dog
  USER_REPO_GOGS_BASE_URL=http://gittin:3000

  These flow through to the backend container via env_file: .env. No additional Docker changes needed - user repo provisioning works from the
  existing backend service.
