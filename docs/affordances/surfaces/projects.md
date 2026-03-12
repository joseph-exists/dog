# Projects

Status: `partial`
Primary routes:
- `/projects`
- `/project/$projectId`

Primary files:
- `/home/josep/dog/frontend/src/routes/_layout/projects.tsx`
- `/home/josep/dog/frontend/src/routes/_layout/project.$projectId.tsx`
- `/home/josep/dog/frontend/src/hooks/useProjects.ts`
- `/home/josep/dog/frontend/src/services/projectsService.ts`

Related backend/services:
- `/home/josep/dog/backend/app/api/routes/projects.py`
- `/home/josep/dog/backend/app/api/routes/access.py`
- `/home/josep/dog/backend/app/api/routes/persona_groups.py`
- `/home/josep/dog/backend/app/crud_projects.py`
- `/home/josep/dog/backend/app/services/access_control.py`

Last reviewed: `2026-03-10`
Reviewer: `Codex`

## Summary

Projects are user-owned collaboration containers that host resource attachment,
workspace layout, and access allocation. The current prototype now supports
both legacy account/group sharing and persona-mediated sharing.

Primary user intents:
- create and organize a project workspace
- attach resources to a project
- share the project with collaborators
- collaborate through personas and persona groups

Primary object model:
- `Project`
- `ProjectResource`
- `AccessGrant`
- `PersonaGroup`
- `UserPersona`

Key integrations:
- `Page`
- `Story`
- `Demos`
- `Rooms`
- `Repos`
- `Agents` future/partial

## Role And State Matrix

| Dimension | Values | Notes |
| --- | --- | --- |
| User role | `owner`, `editor`, `viewer`, `system` | current frontend primarily exposes management to owner |
| Object state | `created`, `page initialized`, `resources attached`, `shared`, `empty` | these materially change what the user can do |
| Data dependency | `project exists`, `workspace page exists`, `resources available`, `persona exists`, `persona group exists` | several project affordances depend on related objects |
| Source of truth | `crud_projects`, `access_control`, `useProjects`, `project detail route` | persona-mediated visibility is enforced in backend queries now |

## Affordance Inventory

| Affordance | User-visible control | Route or location | Preconditions | Outcome | Evidence |
| --- | --- | --- | --- | --- | --- |
| create project | create dialog/button | `/projects` | signed in | project created | [/home/josep/dog/frontend/src/hooks/useProjects.ts](/home/josep/dog/frontend/src/hooks/useProjects.ts#L130) |
| open project workspace | project card/detail route | `/project/$projectId` | project visible to user | workspace detail opens | [/home/josep/dog/frontend/src/routes/_layout/project.$projectId.tsx](/home/josep/dog/frontend/src/routes/_layout/project.$projectId.tsx#L1) |
| edit project metadata | settings tab | `/project/$projectId` | owner | project updated | [/home/josep/dog/frontend/src/routes/_layout/project.$projectId.tsx](/home/josep/dog/frontend/src/routes/_layout/project.$projectId.tsx#L666) |
| delete project | delete button | `/project/$projectId` | owner | project deleted | [/home/josep/dog/frontend/src/routes/_layout/project.$projectId.tsx](/home/josep/dog/frontend/src/routes/_layout/project.$projectId.tsx#L693) |
| attach resource | resource association controls | `/project/$projectId` | owner, attachable resource exists | project resource attached | [/home/josep/dog/frontend/src/routes/_layout/project.$projectId.tsx](/home/josep/dog/frontend/src/routes/_layout/project.$projectId.tsx#L258) |
| detach resource | `Detach` button | `/project/$projectId` | owner, resource attached | resource detached | [/home/josep/dog/frontend/src/routes/_layout/project.$projectId.tsx](/home/josep/dog/frontend/src/routes/_layout/project.$projectId.tsx#L382) |
| grant direct access | access form | `/project/$projectId` | owner, project exists | project grant added | [/home/josep/dog/frontend/src/routes/_layout/project.$projectId.tsx](/home/josep/dog/frontend/src/routes/_layout/project.$projectId.tsx#L489) |
| revoke access | `Revoke` button | `/project/$projectId` | owner, grant exists | project grant removed | [/home/josep/dog/frontend/src/routes/_layout/project.$projectId.tsx](/home/josep/dog/frontend/src/routes/_layout/project.$projectId.tsx#L589) |
| create persona collaboration group | persona group form | `/project/$projectId` | owner, owner persona exists | persona group created | [/home/josep/dog/frontend/src/routes/_layout/project.$projectId.tsx](/home/josep/dog/frontend/src/routes/_layout/project.$projectId.tsx#L609) |
| add persona member to group | member controls | `/project/$projectId` | owner, persona group exists | membership added | [/home/josep/dog/frontend/src/routes/_layout/project.$projectId.tsx](/home/josep/dog/frontend/src/routes/_layout/project.$projectId.tsx#L649) |
| discover collaborator persona | discovery combobox | `/project/$projectId` | owner, published collaborator persona exists | external persona selected without raw UUID entry | [/home/josep/dog/frontend/src/components/UserPage/DiscoverUserPersonaCombobox.tsx](/home/josep/dog/frontend/src/components/UserPage/DiscoverUserPersonaCombobox.tsx#L1) |

## Use Case: Create A Project And Initialize A Workspace

Status: `verified`
Primary persona: `owner`
Priority: `P0`

### User Goal

Create a collaboration container and open its workspace host.

### Entry Points

- `/projects`
- project create dialog

### Preconditions

- must be signed in

### Primary Affordances

- create project action
- project detail route
- hosted page workspace shell

### Main Success Path

1. User creates a project.
2. User opens `/project/$projectId`.
3. Workspace page initializes if missing.
4. User lands in project workspace tabs.

### Alternate Paths

- viewer opens an already shared project in read-only mode

### Outcomes

- project exists
- hosted workspace shell is available

### Empty, Error, and Blocked States

- Empty: no projects on list page
- Error: project unavailable card
- Blocked: unauthenticated users cannot use the route

### Integration Touchpoints

- `PageShell`: workspace host
- `Access`: project visibility gates route usefulness

### Evidence

- [/home/josep/dog/frontend/src/routes/_layout/project.$projectId.tsx](/home/josep/dog/frontend/src/routes/_layout/project.$projectId.tsx#L41)
- [/home/josep/dog/backend/app/crud_projects.py](/home/josep/dog/backend/app/crud_projects.py#L31)

### Walkthrough Readiness

- `ready`

## Use Case: Attach Shared Resources To A Project

Status: `partial`
Primary persona: `owner`
Priority: `P0`

### User Goal

Associate stories, demos, rooms, repos, and other supported resources with a project.

### Entry Points

- `/project/$projectId`
- `Resources` tab

### Preconditions

- project exists
- user is project owner

### Primary Affordances

- quick-pick selector
- resource type filter
- manual resource id input

### Main Success Path

1. Owner opens resource tab.
2. Owner filters attachable resources.
3. Owner attaches a resource.
4. Resource appears in project resource list.

### Alternate Paths

- owner pastes resource UUID directly
- owner detaches existing resource later

### Outcomes

- attached resources become part of the project context
- inherited project access can apply to those resources where supported

### Empty, Error, and Blocked States

- Empty: no attachable resources in current filter
- Error: attach or detach failure
- Blocked: non-owner cannot mutate attachments

### Integration Touchpoints

- `Story`, `Demos`, `Rooms`, `Repos`, `Agents` future
- project-derived resource access

### Evidence

- [/home/josep/dog/frontend/src/routes/_layout/project.$projectId.tsx](/home/josep/dog/frontend/src/routes/_layout/project.$projectId.tsx#L258)
- [/home/josep/dog/frontend/src/services/projectsService.ts](/home/josep/dog/frontend/src/services/projectsService.ts#L173)

### Walkthrough Readiness

- `partial`: the flow is real, but resource selection still mixes polished discovery with fallback UUID entry

## Use Case: Share A Project Through Personas

Status: `partial`
Primary persona: `owner`
Priority: `P0`

### User Goal

Grant project access through `user_persona` and `persona_group` instead of only through raw user accounts.

### Entry Points

- `/project/$projectId`
- `Access` tab

### Preconditions

- project exists
- user is project owner
- relevant personas or persona groups exist

### Primary Affordances

- grant subject type selector
- owned persona selector
- persona group selector
- published collaborator persona discovery

### Main Success Path

1. Owner opens project access tab.
2. Owner chooses `user_persona` or `persona_group`.
3. Owner selects a persona or group.
4. Grant is created.
5. Collaborator gains project visibility through persona-mediated resolution.

### Alternate Paths

- owner still uses legacy `group` or direct `user` grant
- owner pastes persona id directly when needed

### Outcomes

- project access is tied to collaboration identity, not only raw account identity
- persona-mediated access participates in project visibility and inheritance

### Empty, Error, and Blocked States

- Empty: no explicit grants yet
- Error: grant add/revoke failure
- Blocked: owner-only share management in current prototype

### Integration Touchpoints

- `AccessGrant`
- `PersonaGroup`
- user-page authored personas

### Evidence

- [/home/josep/dog/frontend/src/routes/_layout/project.$projectId.tsx](/home/josep/dog/frontend/src/routes/_layout/project.$projectId.tsx#L489)
- [/home/josep/dog/backend/app/crud_projects.py](/home/josep/dog/backend/app/crud_projects.py#L58)

### Walkthrough Readiness

- `partial`: the core mechanism is solid, but the operator-facing explanation of why a collaborator has access is still thinner than the backend model

## Use Case: Create A Persona-Mediated Collaboration Group

Status: `partial`
Primary persona: `owner`
Priority: `P1`

### User Goal

Create a project-relevant persona group and populate it with owned or collaborator personas.

### Entry Points

- `/project/$projectId`
- access tab, persona collaboration group section

### Preconditions

- project exists
- owner has at least one `UserPersona`

### Primary Affordances

- create persona group controls
- owner persona selector
- add member controls
- collaborator persona discovery

### Main Success Path

1. Owner creates a persona group.
2. Owner selects an owner persona for that group.
3. Owner adds persona members.
4. Owner grants the project to that persona group.

### Alternate Paths

- owner adds only their own personas first
- owner manages memberships incrementally over time

### Outcomes

- reusable persona group exists for workspace/project sharing
- the group can power `collaborators` audience logic and project access

### Empty, Error, and Blocked States

- Empty: no persona groups yet
- Error: membership or group creation failure
- Blocked: owner persona is required to create the group

### Integration Touchpoints

- `Persona Groups`
- user-page published persona discovery
- project access grants

### Evidence

- [/home/josep/dog/frontend/src/routes/_layout/project.$projectId.tsx](/home/josep/dog/frontend/src/routes/_layout/project.$projectId.tsx#L609)
- [/home/josep/dog/backend/app/api/routes/persona_groups.py](/home/josep/dog/backend/app/api/routes/persona_groups.py#L1)

### Walkthrough Readiness

- `partial`

## Current Prototype Support Assessment

### Strong For Current Prototype

- persona-mediated project visibility is real
- persona-group based sharing is real
- published collaborator persona discovery is real
- project access can now be described in prototype walkthroughs without hand-waving

### Near-Term Critical Improvements That Unlock Significant Potential

- explain inherited access reasons across project resources and attached surfaces
- define capability-specific inheritance for complex resources like agents
- move from owner-only share management toward richer project collaboration administration if product needs it
- improve resource-specific selection and state explanation so projects feel less UUID-shaped

### Not Yet Load-Bearing Enough For

- final delegated workspace governance model
- nuanced capability inheritance such as `view/use/edit/manage` on attached agents
- full invitation/acceptance lifecycle for persona-group participation

## Cross-Surface Journey: Publish Personas Then Share A Project Through Them

Status: `partial`

### Surfaces Involved

- `User Page`
- `Projects`
- `Persona Groups`

### Trigger

User wants collaboration identity to flow from authored personas into a shared project.

### Journey Steps

1. User publishes one or more personas on `/u/$slug/compose`.
2. User opens `/project/$projectId`.
3. User discovers collaborator personas or creates a persona group.
4. User grants the project to a persona or persona group.
5. Collaborator sees the project and inherits supported resource access through that path.

### Integration Risks

- access explanation is still weaker than the actual resolver
- attached-resource inheritance is generic today and may not be sufficient for agent-specific capability semantics
- current ownership model is still account-owned, not persona-owned

### User Value

This is the clearest prototype expression of persona-mediated collaboration.

### Walkthrough Candidate

`yes`

## Open Questions And Gaps

- should projects gain a first-class membership model rather than inferring membership from grants
- should project owners be able to delegate persona-group management
- how should attached agents express `view/use/edit/manage` capability inheritance
- should persona-mediated project access become the preferred documented path over legacy groups immediately

## Walkthrough Backlog

| Walkthrough | Surface | Persona | Readiness | Notes |
| --- | --- | --- | --- | --- |
| create project and attach resources | `Projects` | `owner` | `ready` | strongest core project flow |
| share project to one collaborator persona | `Projects` | `owner` | `partial` | now much more walkthroughable |
| create persona group and grant project to it | `Projects` | `owner` | `partial` | important prototype unlock |
| open shared project as collaborator | `Projects` | `viewer` | `partial` | needs clearer inherited-access explanation |

