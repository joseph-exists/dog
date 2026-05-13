# Projects Container (Workspace) — Plan + Phase 0 Implementation

## Goal

Introduce a `Project` (aka Workspace) object that:
- Holds collaborators (users and/or groups) via existing `access_grants`
- Can attach existing resources (rooms, stories, demo sessions, repos, etc.)
- Enables *inherited access* from a project to its attached resources
- Does **not** automatically grant room membership (rooms remain membership-gated)

Resources can belong to **multiple projects**, one, or none (many-to-many).

## Non-goals (Phase 0)

- Delegated share-management (`manager` role assignment remains blocked)
- Room auto-invite convenience (can be added later as an explicit action/handler)
- Org/tenant hierarchy

## Data Model

### `projects`
- `id` UUID PK
- `owner_id` FK → `user.id` (owner manages settings and sharing)
- `name` string (unique per owner)
- `description` optional
- timestamps

### `project_resources` (many-to-many attachment table)
- `id` UUID PK
- `project_id` FK → `projects.id`
- `resource_type` string (e.g. `story`, `demo_session`, `room`, `shadow_repo`)
- `resource_id` UUID
- timestamps
- unique `(project_id, resource_type, resource_id)`
- indexes for:
  - lookup by `project_id`
  - lookup by `(resource_type, resource_id)` (to resolve project attachments for access checks)

### Membership / sharing

Reuse `access_grants`:
- `resource_type="project"`, `resource_id=<project_id>`
- subject: user/group
- role: `viewer` (default), `editor`
- Phase-0 constraint: only owner/superuser can add/revoke grants (no delegation)

## Authorization Semantics

### Effective access for an attached resource

For resource `R` (non-room):
1) superuser → allow
2) resource owner → `manager`
3) direct grants on `R` (user + group) → best role
4) inherited project grants (user + group) across all projects that attach `R` → best role

Rooms:
- Project grants may allow “discovering” a room exists under a project, but do **not**
  satisfy `check_room_membership()` (existing room route protections stay intact).

## API (Phase 0)

### Projects
- `POST /projects` create project (owner = current user)
- `GET /projects` list projects visible to current user (owned + granted)
- `GET /projects/{project_id}` get project if visible
- `PATCH /projects/{project_id}` owner/superuser only
- `DELETE /projects/{project_id}` owner/superuser only

### Project resources
- `GET /projects/{project_id}/resources` list attachments (requires `viewer` on project)
- `POST /projects/{project_id}/resources` attach a resource (owner/superuser only)
- `DELETE /projects/{project_id}/resources` detach a resource (owner/superuser only)

Access grants reuse existing endpoints:
- `/access/project/{project_id}`

## Implementation Touch List

- `backend/app/models.py` add Project + ProjectResource models and schemas
- `backend/app/services/access_control.py` + sync mirror:
  - add `"project"` to owner registry
  - add “project-derived role” fallback when resource has project attachments
- `backend/app/crud_access.py` ensure owner check works for projects via registry
- `backend/app/crud_projects.py` new CRUD helpers
- `backend/app/api/routes/projects.py` new router
- `backend/app/api/main.py` include router
- `backend/app/alembic/versions/` new migration
- `backend/app/tests/api/routes/` minimal inheritance tests (story + demo_session)

