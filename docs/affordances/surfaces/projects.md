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
- `/projects`
- `/projects/{id}/resources`
- `/access/project/{id}`

Last reviewed: `2026-03-06`
Reviewer: `Codex`

## Summary

Projects are collaboration containers for grouping resources and access. The
current frontend exposes project discovery, creation, detail management,
resource attachment, access grant management, and a hosted page/workspace shell.

Primary user intents:
- discover owned and shared projects
- create and organize a project
- attach resources and manage access

Key integrations:
- `Story`
- `Demos`
- `Repos`
- `Room`
- `Page`

## Available High-Level Use Cases

| Use case | Status | Notes |
| --- | --- | --- |
| Discover owned and shared projects | `verified-ish` | list page exists and loads project cards |
| Create a project | `verified-ish` | dialog on `/projects` |
| Open a project workspace | `verified-ish` | detail page route exists |
| Edit project metadata | `partial` | settings flow exists; permission behavior should be verified end to end |
| Delete a project | `partial` | destructive action exists on detail page |
| Attach a resource to a project | `partial` | attachable list and manual entry exist |
| Detach a resource from a project | `partial` | detach button exists |
| Grant group or user access to a project | `partial` | grant UI exists for managers/owners |
| Revoke project access | `partial` | revoke action exists |
| View project workspace layout | `partial` | hosted via `PageShell`; depends on page existence and auth |

## Walkthrough Candidates

- Create project, then attach visible resources
- Open project as viewer and inspect associated resources
- Initialize or open project workspace layout

## Open Questions And Gaps

- exact collaborator experience needs validation
- page auth for project entities was flagged as a backend concern in planning
- resource attachment UX is UUID-oriented and not yet walkthrough-polished
