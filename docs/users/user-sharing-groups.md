**Implemented Phase 0 minimal RBAC + groups + sharing (with your constraints).**

- New DB models: `UserGroup`, `UserGroupMembership`, `AccessGrant` in `backend/app/models.py:1`.
- New access-check services:
  - Async: `backend/app/services/access_control.py:1`
  - Sync (for story authoring routes): `backend/app/services/access_control_sync.py:1`
- New CRUD:
  - `backend/app/crud_groups.py:1`
  - `backend/app/crud_access.py:1` (enforces **owner/superuser-only** share-management; blocks assigning `manager` role)
- New API routes:
  - Groups: `backend/app/api/routes/groups.py:1` (`/groups/...`)
  - Grants: `backend/app/api/routes/access.py:1` (`/access/{resource_type}/{resource_id}`)
  - Wired in: `backend/app/api/main.py:1`
- Integrations:
  - Stories / nodes / choices now honor grants (`viewer` for read, `editor` for writes) in `backend/app/api/routes/stories.py:1`, `backend/app/api/routes/storynodes.py:1`, `backend/app/api/routes/node_choices.py:1`.
  - DemoSession sharing enabled: non-owners can `GET /demos/sessions/{id}` if granted `viewer` in `backend/app/api/routes/demos.py:1`.
  - Sharing a `demo_session` **to a user** also invites them to the backing room as `member` (and revoke removes them) in `backend/app/crud_access.py:1`.
  - Room auth helpers now treat `is_superuser` as always allowed in `backend/app/crud.py:1`.
- Alembic migration added: `backend/app/alembic/versions/f2c1d0e9a8b7_add_user_groups_and_access_grants.py:1` (and `alembic heads` now shows `f2c1d0e9a8b7` as the head).
- Minimal API tests added: `backend/app/tests/api/routes/test_access_groups_phase0.py:1` (couldn’t run here because this environment is missing `pytest_asyncio`, though it’s listed in `backend/pyproject.toml`).

**How to use (API)**
- Grant story view (default): `POST /api/v1/access/story/{story_id}` body `{ "subject_type":"user", "subject_id":"<uuid>", "role":"viewer" }`
- Upgrade to co-author: same endpoint with `"role":"editor"`.
- Share a demo session: `POST /api/v1/access/demo_session/{demo_session_id}` (same body). This also invites the user to the backing room as a participant.

If you want, I can add a tiny “resource_type registry” doc for supported values (`story`, `demo_session`) and/or add group-based demo-session sharing semantics (right now group grants work for access checks, but only direct-user demo-session grants trigger room invites).