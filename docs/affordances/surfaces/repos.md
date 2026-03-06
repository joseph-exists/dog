# Repos

Status: `partial`
Primary routes:
- `/repos`
- `/repo/$repoId`

Primary files:
- `/home/josep/dog/frontend/src/routes/_layout/repos.tsx`
- `/home/josep/dog/frontend/src/routes/_layout/repo.$repoId.tsx`
- `/home/josep/dog/frontend/src/components/Repo/index.ts`

Related backend/services:
- `UserReposService`
- repo content and capability endpoints behind repo hooks

Last reviewed: `2026-03-06`
Reviewer: `Codex`

## Summary

Repos are shell-driven viewer workspaces with import, browsing, and panel-layout
customization affordances. They also intersect strongly with Room via repo
co-working panels.

Primary user intents:
- discover accessible repositories
- browse repo content
- customize repo workspace layout

Key integrations:
- `Room`
- `Projects`

## Available High-Level Use Cases

| Use case | Status | Notes |
| --- | --- | --- |
| Discover accessible repositories | `verified-ish` | repo overview panel on `/repos` |
| Import a repository | `partial` | import dialog exists; full flow not mapped here |
| Open repository detail workspace | `verified-ish` | route exists |
| Browse repo content with panels | `verified-ish` | panel renderer and layout exist |
| Change repo layout mode or panel arrangement | `verified-ish` | quick layout and layout editor dialogs exist |
| Save and reuse user layout presets | `verified-ish` | local preset persistence exists |
| Reset layout to preset baseline | `verified-ish` | reset action exists |

## Walkthrough Candidates

- Import repo, open detail workspace, browse files
- Customize repo layout and save a preset
- Use repo in a room co-working scenario

## Open Questions And Gaps

- repo sharing/manage-access is still conceptually ahead of explicit API backing
- walkthrough should branch on viewer-ready capabilities
