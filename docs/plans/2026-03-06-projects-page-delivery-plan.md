# Projects Page Delivery Plan

## Context

Projects now exist as collaboration containers with:
- membership via `access_grants` (`resource_type="project"`)
- attachments via `project_resources`
- inherited access from project membership to attached resources

Users now need a first-class UI to:
1. find their projects
2. visualize project composition (users/groups/resources)
3. manage membership and attachments

## Recommendation

Use **Page constructs as the container**, with a **Projects-specific composition**.


Best path:
- build a `Projects` feature route that uses the same compositional patterns as Page/Demo (`blocks`, `panels`, `registry`, editor hooks)
- keep domain-specific blocks/panels for project management
- preserve a clear `Project` domain boundary

## Why This Approach

1. Reuses existing composability primitives (`Page` blocks/panels) 
2. Keeps future flexibility: project pages can evolve independently from agent/demos routes.
3. Aligns with current backend: project APIs already exist and are generic.
4. Reduces risk of access-control regressions by centralizing project authorization in project-specific APIs.

## Critical Backend Gap To Address First

Current `GET /pages/{entity_type}/{entity_id}` returns data without entity-level access checks.

Before exposing project pages to collaborators:
1. Add authorization in pages routes for `entity_type="project"` using `require_access(..., resource_type="project", minimum_role="viewer")`.
2. For page updates on project entities, require `editor` (or owner-only, per policy).
3. Keep owner checks for non-project entities unchanged.

Without this, project page layouts can leak.

## Product Surface

### Routes

- `GET /projects` => Projects Index page (discover + quick actions)
- `GET /projects/{projectId}` => Project Workspace page (manage project)

Optional later:
- `GET /projects/{projectId}/activity`
- `GET /projects/{projectId}/insights`

### Page Composition

For `projects/{projectId}` define a project composition profile with blocks:
- `project.header` (name, description, owner, timestamps)
- `project.members` (users/groups, roles, invite/revoke actions)
- `project.resources` (attached resources grouped by type)
- `project.add_resource` (search/select attach flow)
- `project.permissions_preview` (effective access preview by user/group)

For `/projects` index:
- `projects.grid` (cards with counts and quick actions)
- `projects.filters` (owner/shared, resource type, membership type)
- `projects.create` (create project dialog/form)

## API Plan

Use existing APIs first:
- `/projects` CRUD
- `/projects/{id}/resources` list/add/remove
- `/access/project/{id}` list/upsert/revoke grants
- `/groups` endpoints for share targets

Add only if needed after first UI pass:
- batch attach/detach endpoint
- “search attachable resources” endpoint across story/demo/repo

## Frontend Implementation Plan

## Phase 1: Functional Project Management (no page layout editing)

*REQUIREMENT: USE EXPORTED CLIENT SERVICES, TYPES, AND SCHEMAS from frontend/src/client - ProjectsService exists! Page operations, types, schemas exist.

1. Add `ProjectsService` + hooks:
   - `useProjectsList`
   - `useProject`
   - `useProjectResources`
   - `useProjectAccessGrants`
2. Create pages:
   - `frontend/src/routes/projects/index.tsx`
   - `frontend/src/routes/projects/$projectId.tsx`
3. Implement management UI with existing table/card primitives:
   - list projects
   - create/edit/delete project
   - add/remove resource associations
   - grant/revoke project membership (user/group)

Success criteria:
- owner can fully manage project composition
- collaborator with project viewer can see project and resources
- collaborator cannot mutate if policy disallows

## Phase 2: Page-Construct Integration (customizable project workspace)

1. Introduce project page entity:
   - `entity_type="project"`
   - `entity_id=<project_id>`
2. Add project block registry entries:
   - reusable block renderers for members/resources/actions
3. Add `usePageEditor("project", projectId)` to project workspace
4. Allow project owner to customize layout (later optionally collaborators with editor role)

Success criteria:
- project workspace layout persists
- default template exists for new projects
- auth guards prevent unauthorized page read/write

## Phase 3: Advanced UX

1. Effective access visualization (why user can access resource)
2. Bulk attach/detach flows
3. Saved filters and quick views
4. Optional room-convenience handler (explicit toggle; default remains off)

## Permission Matrix (UI + API)

- Project owner / superuser:
  - full project CRUD
  - manage memberships and attachments
  - edit project page layout
- Project editor (if enabled later):
  - mutate project composition if policy allows
  - edit project page layout (optional)
- Project viewer:
  - read project details and attached resources
  - no mutation
- Room membership:
  - unchanged; still required for room operations

## Test Plan

## Backend

1. Pages auth:
   - viewer can read `project` page
   - non-member denied
   - non-editor denied for layout writes
2. Project APIs:
   - owner can attach/detach resources
   - viewer cannot mutate
3. Inheritance:
   - project viewer can read attached story/demo_session
   - still blocked on room operations without room membership

## Frontend E2E / Integration

1. Projects index loads owned + shared projects
2. Project detail reflects membership and resource changes
3. Unauthorized actions are hidden/blocked
4. Project page layout persists after refresh 


