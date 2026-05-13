# Minimal RBAC + User Groups (Phase 0)

## Context / Goal

We need a minimal, extensible access-control foundation that goes beyond `owner vs user` without introducing full org/tenant RBAC yet.

Immediate use cases:
- Invite a user to a room with “open access to all controls”
- Share a story with a set of users (co-authoring and/or viewing)
- Share a demo with a set of users

Constraints:
- Object creators are **not** system admins, but **can manage access** to their objects (within system constraints).
- System constraints still apply: `is_superuser` accounts must be able to access everything.
- Per-object rule complexity (room/story/repo specific constraints) comes later; this phase provides primitives.

Non-goals (for this phase):
- Org/tenant hierarchy, SCIM, SSO
- Complex policy language (ABAC), attribute conditions
- Email-based invites / pending invites (requires identity lifecycle decisions)

---

## Proposed Primitives

### 1) User Groups

User-owned groups used as “share targets”.

Tables:
- `user_groups`
  - `id` (UUID PK)
  - `owner_id` (FK → `user.id`) — who can manage the group
  - `name` (string) — unique per owner (`(owner_id, name)` unique)
  - `created_at`
- `user_group_memberships`
  - `id` (UUID PK)
  - `group_id` (FK → `user_groups.id`)
  - `user_id` (FK → `user.id`)
  - `role` (`member` | `manager`) — optional, defaults `member`
  - `created_at`
  - unique: `(group_id, user_id)`

### 2) Object Access Grants (ACL-style, minimal)

Single generalized table that grants a role to a *subject* (user or group) for a *resource*.

Table:
- `access_grants`
  - `id` (UUID PK)
  - `resource_type` (string) — e.g. `story`, `demo_session` (room can be added later)
  - `resource_id` (UUID)
  - `subject_type` (`user` | `group`)
  - `subject_id` (UUID)
  - `role` (`viewer` | `editor` | `manager`)
  - `granted_by_user_id` (FK → `user.id`)
  - `created_at`
  - unique: `(resource_type, resource_id, subject_type, subject_id)`
  - indexes:
    - `(resource_type, resource_id)`
    - `(subject_type, subject_id)`

Role semantics (comparative “levels”):
- `viewer`: read/view/use
- `editor`: modify content/config (but not necessarily share-management)
- `manager`: manage shares (grant/revoke), and generally “all object controls”

Superuser semantics:
- `user.is_superuser == True` bypasses all checks (always allowed).

Ownership semantics:
- If the resource has an `owner_id` and `owner_id == current_user.id`, treat as `manager`.

---

## Authorization API (Backend Internal)

Create a small service module that centralizes access checks:

- `has_access(session, *, user, resource_type, resource_id, min_role) -> bool`
- `require_access(...) -> None` (raises `HTTPException(403, ...)`)
- `list_effective_roles(...)` (optional; for UI later)

Implementation notes:
- Checks:
  1) `is_superuser` → allow
  2) owner check via resource registry → allow
  3) direct user grant
  4) group grants where `user` is a member of the group
- `resource_type` to model lookup implemented via a small registry:
  - `"story" -> Story (owner_id)`
  - `"demo_session" -> DemoSession (user_id)`
  - Future: `"room" -> Room` (or keep room’s event-sourced model separate)

---

## Minimal Integrations (Phase 0)

### Stories

Update story authoring routes to allow shared access:
- Read operations require `viewer`
- Edit operations require `editor`
- Share-management endpoints require `manager`

### DemoSession

Share target is a specific `DemoSession` (not the template config).

Mutation rules:
- `GET /demos/sessions/{id}` requires `viewer`
- Updates/deletes remain owner/superuser-only in this phase
- Convenience: granting a `demo_session` to a user also invites them to the backing room as a `member` participant (so room auth works)

### Rooms (superuser constraint)

Room membership is event-sourced today and does not currently consider superusers.

Minimal fix:
- Update the room authorization helpers (`check_room_membership`, `check_room_owner`) to short-circuit to **True** if the calling user is a superuser.

---

## External API (Endpoints)

### Groups
- `POST /groups` create group
- `GET /groups` list groups owned by current user
- `DELETE /groups/{group_id}` delete owned group
- `GET /groups/{group_id}/members`
- `POST /groups/{group_id}/members` add member (owner/manager only)
- `DELETE /groups/{group_id}/members/{user_id}` remove member

### Access Grants (generic)
- `GET /access/{resource_type}/{resource_id}` list grants (manager only)
- `POST /access/{resource_type}/{resource_id}` grant role to `user_id` or `group_id` (manager only)
- `DELETE /access/{resource_type}/{resource_id}` revoke grant (manager only)

---

## Alembic / DB Migration

Add an Alembic revision that creates:
- `user_groups`
- `user_group_memberships`
- `access_grants`

---

## Tests (Minimal)

- Groups:
  - Owner can create and manage membership
  - Non-owner cannot modify group
- Access grants:
  - Story: owner grants `viewer` to user → user can `GET /stories/{id}`
  - DemoSession: owner grants `viewer` to user → user can `GET /demos/sessions/{id}` and access the backing room
- Rooms:
  - Superuser can access room endpoints even without membership (at least one representative route)

---

## Files (Expected Touch List)

- `backend/app/models.py` (add new tables + public schemas)
- `backend/app/api/routes/` (new `groups.py`, new `access.py`)
- `backend/app/api/main.py` (router wiring)
- `backend/app/services/` (new `access_control.py` or similar)
- `backend/app/api/routes/demos.py` (demo session access check)
- `backend/app/crud.py` (room superuser bypass in membership helpers)
- `backend/app/tests/` (new tests for the primitives + integrations)
- `backend/app/alembic/versions/` (new migration)
