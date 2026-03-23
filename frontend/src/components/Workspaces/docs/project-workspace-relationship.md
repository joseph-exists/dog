# Project And Workspace Relationship Note

## Purpose

This artifact decides the canonical project relationship model for `Workspace`.

The question is not whether workspaces should appear project-bound in the product. They should.

The real question is where that relationship should be authoritative:

- directly on `Workspace`
- through `ProjectResource`
- or through both, with one as source of truth and one as projection

This note recommends one canonical answer for this iteration.

## Current State

Projects already support a generic attachment model through [ProjectResource](/home/josep/dog/backend/app/models.py#L1681) and the related CRUD/routes in:

- [crud_projects.py](/home/josep/dog/backend/app/crud_projects.py)
- [projects.py](/home/josep/dog/backend/app/api/routes/projects.py)

That model currently supports attachments such as:

- `story`
- `demo_session`
- `room`
- `user_repo`
- `agent`

On the frontend, that same attachment model is already reflected in [projectsService.ts](/home/josep/dog/frontend/src/services/projectsService.ts).

By contrast, `Workspace` is currently owner-only and has no project relationship in its model or routes.

## Decision

The canonical project relationship for `Workspace` should be:

- `ProjectResource(resource_type="workspace", resource_id=<workspace_id>)`

Not:

- a direct persisted `project_id` field on `Workspace` as the source of truth

### Why

This is the cleaner decision for the platform we already have:

- projects already own the generic resource graph
- attaching a workspace to a project is semantically the same kind of action as attaching a room or repo
- it keeps relationship management centralized instead of duplicating it across resource models
- it gives us room to support more than one project relationship later if we actually need it
- it avoids turning `Workspace` into a special-case collaboration model too early

In short:

- project membership should remain project-centric
- workspace visibility can still be expressed simply in the workspace contract
- but the authoritative relationship row should live in `project_resources`

## Near-Term Product Shape

Even though `ProjectResource` should be canonical, the workspace API should still project a simple near-term view.

For this iteration, the workspace-facing contract should expose:

- `project_id: string | null`
- `project_summary: { id, name } | null`
- `visibility: "private" | "project" | "shared"`

Important distinction:

- these are projection fields for convenience
- they are not the canonical persistence layer for project linkage

## Recommended Near-Term Constraint

Near term, a workspace should belong to:

- zero projects
- or one project

That should be enforced at the service layer even if the underlying `ProjectResource` model is generic enough to support more later.

### Why zero-or-one first

- it keeps access semantics understandable
- it keeps workspace list/detail UI simple
- it matches the current milestone needs
- it avoids premature design around multi-project compute reuse

So the recommended shape is:

- canonical storage: generic project attachment
- near-term business rule: at most one project attachment for a workspace

## Relationship Semantics

### Private Workspace

- no `ProjectResource` attachment
- `visibility = "private"`
- only owner can manage/use unless separate sharing is introduced

### Project Workspace

- exactly one `ProjectResource(resource_type="workspace")`
- `visibility = "project"`
- project access policy determines who can use the workspace

### Shared Workspace

This should remain a deferred mode for now.

Recommendation:

- do not make `shared` fully real in this iteration unless there is a concrete non-project ACL requirement
- keep the enum value available if useful for forward compatibility, but do not let it force implementation complexity yet

For this milestone, the system can stay coherent with:

- `private`
- `project`

## Service-Layer Implications

### Attach

When associating a workspace with a project:

1. validate project access
2. validate workspace manageability
3. ensure the workspace has no other active project attachment
4. create or confirm the `ProjectResource` row with:
   - `resource_type = "workspace"`
   - `resource_id = workspace.id`
5. update any projected workspace visibility fields if those are persisted

### Detach

When detaching:

1. remove the `ProjectResource` row
2. project workspace state back to `visibility = "private"` unless another sharing model exists

### Querying

Workspace detail and list endpoints should join or look up project attachments and project summaries so the frontend does not need to do separate resource graph assembly for basic screens.

## Proposed API Behavior

### Workspace Detail / List Projection

`WorkspacePublic` should include:

```ts
{
  visibility: "private" | "project"
  project_id: string | null
  project_summary: {
    id: string
    name: string
  } | null
}
```

This is a convenience projection built from `ProjectResource`.

### Recommended Mutation Surface

Preferred near-term mutation paths:

- attach:
  `POST /api/v1/projects/{project_id}/resources`
  with:
  ```json
  {
    "resource_type": "workspace",
    "resource_id": "<workspace_id>"
  }
  ```

- detach:
  `DELETE /api/v1/projects/{project_id}/resources`
  with the same payload

Optional convenience route:

- `PATCH /api/v1/workspaces/{workspace_id}`
  with:
  ```json
  {
    "project_id": "<project_id>"
  }
  ```

If this convenience route exists, it should internally delegate to the same project-resource service logic. It should not create a second relationship mechanism.

## Backend Model Recommendation

### Canonical persistence

Keep canonical project linkage in:

- `project_resources`

### Workspace model

Do not add a required persisted `project_id` field to `Workspace` as the source of truth.

Optional near-term choices:

1. no persisted `project_id`, only response projection
2. nullable denormalized `project_id` for query performance or ergonomics

Recommendation for this iteration:

- do not denormalize yet unless query complexity proves painful

Why:

- the current scale does not justify duplicating source of truth
- denormalization can be added later if list/detail joins become a real problem

## Access Control Recommendation

Once a workspace is attached to a project:

- project membership should be the primary basis for `can_use`
- workspace owner should retain `can_manage`
- project owners should likely gain `can_manage` or at least `can_administer_access`, depending on how operational authority is meant to work

Near-term recommended rule:

- owner always manages
- project members with project viewer+ can use
- project owners can manage attachment and access

This keeps the model understandable without requiring direct workspace ACLs immediately.

## Frontend Recommendation

The frontend should treat project association in two ways:

1. as a simple projected field on workspace list/detail
2. as a project attachment mutation under the hood

That means the `Workspaces` UI can remain simple:

- “Assign to Project”
- “Remove from Project”
- show project badge / summary on workspace cards and detail panels

But the platform still preserves one relationship system instead of two.

## Why Not Direct `Workspace.project_id` As Canonical

It is tempting because it is simple.

But it introduces longer-term problems:

- duplicates the existing project resource graph
- forces special-case logic into workspaces that other resources do not need
- makes future many-to-many or secondary relationships awkward
- splits project association logic between project routes and workspace routes

The direct-field approach is only better if we are certain workspaces will always have a fundamentally different relationship model than the rest of the platform. We do not know that yet, and the existing codebase already suggests the opposite.

## Final Recommendation

For this iteration:

- canonical relationship: `ProjectResource(resource_type="workspace")`
- near-term business rule: at most one project per workspace
- workspace API should project `project_id` and `project_summary` for convenience
- optional workspace convenience mutations may exist, but they must delegate to project-resource logic

This gives us:

- one relationship system
- a simple product surface
- a reversible path if multi-project or richer sharing becomes necessary later

## Follow-On Implications

This decision should feed back into the workspace domain contract:

- `project_id` should be described as projected or derived, not canonical persistence
- `access_summary` should reflect project-derived access when attached
- `visibility = "project"` should imply the presence of one canonical project attachment

It should also feed into the next artifact:

- room/workspace connectivity will need to treat project attachment as a key part of trust and authorization
