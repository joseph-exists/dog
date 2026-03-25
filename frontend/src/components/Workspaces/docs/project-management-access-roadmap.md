# Project Management And Access Roadmap

## Context

Track 3 is now the main dependency in front of deeper room/workspace trust work.

The platform has already crossed the first threshold:

- `Workspace` can be attached to a project through canonical `ProjectResource` rows
- workspace detail exposes attach/detach through that relationship
- workspace list/detail responses project `project_id`, `project_summary`, and `visibility`
- the backend enforces the near-term zero-or-one rule for `resource_type="workspace"`

That means the next uncertainty is no longer relationship storage. It is access semantics:

- who can see a project-attached workspace
- who can use it
- who can manage it
- which actions remain owner-only versus project-mediated

This roadmap focuses on the narrowest useful implementation sequence for making project-attached workspaces operationally real before we deepen Track 4 descriptors further.

## Scope

This pass should implement:

- project-aware workspace visibility in list/detail APIs
- backend-owned workspace action policy that respects owner and project roles
- clear distinction between use-oriented and manage-oriented workspace capabilities
- frontend consumption of the richer project-aware access semantics
- documentation updates that make the resulting policy legible

This pass should not yet implement:

- direct workspace ACLs outside project access
- full `shared` workspace mode
- broad workspace administration dashboards
- richer descriptor/token issuance beyond what Track 4 already supports
- multi-project workspace membership

## Current Implementation Status

Already complete:

- canonical relationship remains `ProjectResource(resource_type="workspace", resource_id=<workspace_id>)`
- attach/detach flows exist through project-resource mutations
- zero-or-one project attachment for a workspace is enforced in the backend
- workspace responses project simple convenience fields for project context
- Track 4 descriptor authorization can already use shared-project attachment as a trust path

What is still missing:

- workspace list/detail access is now project-aware for visibility and retrieval
- shared access uses the existing access-control path rather than a workspace-specific side channel
- owner and project-derived visibility now flow through the same `resource_type="workspace"` access evaluation
- project membership is now the basis for use-oriented workspace actions in the current slice
- allowed actions are not yet role-aware beyond owner lifecycle state
- frontend workspace service and main detail/list surfaces now distinguish “can use” from “can manage”
- the remaining gap is broader UI follow-through rather than service-model ambiguity

## Design Intent

Track 3 should make a project-attached workspace behave like shared platform infrastructure without overcomplicating the first policy pass.

The key principle is:

- project attachment controls shared visibility and use
- workspace ownership still anchors management authority

That yields a simple near-term model:

- owner always manages
- project members can use
- project owners can manage attachment and shared administrative actions

If later research shows that use/manage boundaries need to be split more finely, this pass should still leave us in a shape where that extension is straightforward.

## Recommended Policy Model

### Visibility

Near-term visibility should follow these rules:

- private workspace:
  - no project attachment
  - visible only to owner

- project workspace:
  - one project attachment
  - visible to authorized project members

### Use Authority

Near-term “use” should cover:

- view workspace detail
- request terminal
- discover services
- request room/workspace connection descriptors

Recommended rule:

- owner can always use
- project members with `viewer` or higher can use

### Management Authority

Near-term “manage” should cover:

- stop workspace
- start workspace
- destroy workspace
- assign to project
- remove from project

Recommended rule:

- owner can always manage
- project owner can manage project attachment semantics
- owner remains the only actor for destructive runtime operations in this slice unless we intentionally broaden that later

That keeps the first pass conservative while still making project attachment real for collaboration.

## API Contract Direction

### Query Behavior

Workspace list/detail APIs should no longer be owner-only in the presence of project attachment.

Recommended behavior:

- include owned workspaces
- include project-attached workspaces where the current user has project access
- continue projecting:
  - `visibility`
  - `project_id`
  - `project_summary`
  - `allowed_actions`

### Allowed Actions

Track 1 introduced backend-owned `allowed_actions`.

Track 3 should refine those actions so they become actor-aware.

Near-term action surface should distinguish:

- use actions:
  - `request_terminal`
  - `discover_services`

- manage actions:
  - `start`
  - `stop`
  - `destroy`
  - optional future `manage_project_attachment`

Recommendation:

- do not overexpand the action enum immediately
- first make the existing actions role-aware
- only add a new action name if the frontend clearly needs it for a real affordance

### Optional Projection Additions

If needed for frontend clarity, add projected booleans or summaries such as:

```ts
access_summary: {
  can_use: boolean
  can_manage_runtime: boolean
  can_manage_project_attachment: boolean
  project_role: "viewer" | "editor" | "owner" | null
}
```

Recommendation:

- only add this if `allowed_actions` plus current workspace projection proves too indirect for the UI
- otherwise keep the response smaller in this pass

## Implementation Plan

### Step 1: Backend Workspace Visibility

Make workspace list/detail queries project-aware rather than owner-only.

Files:

- `/home/josep/dog/backend/app/api/routes/workspaces.py`
- `/home/josep/dog/backend/app/services/workspace_service.py`
- related access-control helpers if needed

Changes:

- list visible workspaces for:
  - owner
  - project members with project access
- allow detail retrieval through the same visibility policy
- preserve owner-only behavior for private workspaces

Important constraint:

- do not duplicate project membership logic locally if existing access-control services can answer it cleanly

Status:

- implemented
- workspace list/detail routes now use backend helpers that permit:
  - owner visibility
  - project-derived viewer visibility for attached workspaces
- the shared access-control registry now recognizes `workspace` as an owner-backed resource type, which keeps project inheritance and owner access on one policy path

### Step 2: Backend Action Policy By Role

Make `allowed_actions` depend on both workspace lifecycle and actor authority.

Files:

- `/home/josep/dog/backend/app/services/workspace_service.py`
- access-control helpers as needed

Changes:

- split current lifecycle-based action policy into:
  - lifecycle eligibility
  - actor authorization
- allow project users to receive use-oriented actions
- keep destructive runtime actions conservative in this slice

Important constraint:

- the same policy should become the basis for both workspace UI and Track 4 trust flows

Status:

- implemented
- `allowed_actions` is now actor-aware rather than workspace-only
- owner and superuser retain the full lifecycle-eligible action set
- project-derived users now receive use-oriented actions:
  - `request_terminal`
  - `discover_services`
- destructive runtime actions remain owner-anchored in this slice
- workspace terminal issuance now respects the same actor-aware policy and returns a policy-shaped `403` when a visible user is not allowed to request terminal access

### Step 3: Frontend Service Alignment

Consume the richer shared-workspace semantics in the frontend service layer.

Files:

- `/home/josep/dog/frontend/src/services/workspaceService.ts`
- `/home/josep/dog/frontend/src/hooks/useWorkspaces.ts`
- `/home/josep/dog/frontend/src/hooks/useWorkspace.ts`

Changes:

- ensure workspace list/detail can render project-visible workspaces that are not owner-owned
- expose any new projected access semantics if added
- avoid frontend guesses about use/manage authority

Status:

- implemented
- frontend workspace view models now derive:
  - `accessLevel`
  - `canUseWorkspace`
  - `canManageRuntime`
  - `canDiscoverServices`
  - `isProjectWorkspace`
- workspace list and detail surfaces now explain shared project access more clearly
- owner-only affordances are now suppressed or disabled where the current slice still keeps management authority narrow, such as project assignment and destructive runtime controls

### Step 4: Frontend Management Surface Alignment

Reflect the policy clearly in workspace list/detail UI.

Files:

- `/home/josep/dog/frontend/src/components/Workspaces/panels/WorkspaceListPanel.tsx`
- `/home/josep/dog/frontend/src/components/Workspaces/panels/WorkspaceDetailsPanel.tsx`
- `/home/josep/dog/frontend/src/components/Workspaces/panels/WorkspaceControlsPanel.tsx`
- `/home/josep/dog/frontend/src/components/Workspaces/panels/WorkspaceProjectPanel.tsx`

Changes:

- distinguish:
  - private workspace
  - project workspace
  - workspace you can use but not manage
- suppress or disable controls based on backend action truth
- keep the language operator-friendly and concrete

Status:

- implemented for the main Track 3 surfaces
- workspace shell copy, controls, terminal, project assignment, list, and detail panels now reflect shared-workspace semantics more cleanly
- owner-only operations are no longer presented with owner-toned copy when the current user only has project-derived use access
- the remaining Track 3 work is now less about core semantic alignment and more about whether we want additional management breadth before returning to Track 4

### Step 5: Documentation And Sequencing Review

Once the policy is implemented:

- update:
  - `/home/josep/dog/frontend/src/components/Workspaces/docs/planning.md`
  - `/home/josep/dog/frontend/src/components/Workspaces/docs/project-workspace-relationship.md`
  - `/home/josep/dog/frontend/src/components/Workspaces/docs/room-workspace-connectivity.md`
- reassess whether the next best move is:
  - remaining Track 3 management semantics
  - or returning to Track 4 for richer descriptor issuance and room/workspace UX

## Recommended Sequence

The recommended execution order for this Track 3 pass is:

1. backend visibility rules
2. backend allowed-action policy by role
3. frontend service alignment
4. frontend UI alignment
5. docs update and sequencing review

Why this order:

- visibility determines which workspaces even exist in the shared product surface
- action policy determines what those users can do once they can see them
- frontend work becomes much cleaner once both truths are explicit

## Definition Of Done

Track 3 should count as materially advanced when:

- a project-attached workspace is visible to authorized project members
- the backend can distinguish use authority from management authority
- workspace UI reflects those semantics without inventing local rules
- Track 4 descriptor work is standing on explicit project-aware access truth rather than inferred relationship presence
