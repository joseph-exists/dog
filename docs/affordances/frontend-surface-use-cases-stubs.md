# Frontend Surface Use Cases And Walkthrough Index

Status: `partial`
Scope:
- `Repos`
- `Projects`
- `Demos`
- `Story`
- `Room`
- `Agents`

Purpose:
- act as the index for split surface and journey documents
- preserve a high-level map of current documentation status
- point reviewers toward the next walkthrough-ready areas

Last reviewed: `2026-03-06`

## Method

This index is based on current frontend routes, shells, dialogs, hooks, and
service wiring. Surface-specific detail now lives in dedicated documents using
[frontend-walkthrough-template.md](/home/josep/dog/docs/affordances/frontend-walkthrough-template.md).

## Surface Documents

| Surface | Document |
| --- | --- |
| `Projects` | [projects.md](/home/josep/dog/docs/affordances/surfaces/projects.md) |
| `Repos` | [repos.md](/home/josep/dog/docs/affordances/surfaces/repos.md) |
| `Demos` | [demos.md](/home/josep/dog/docs/affordances/surfaces/demos.md) |
| `Story` | [story.md](/home/josep/dog/docs/affordances/surfaces/story.md) |
| `Room` | [room.md](/home/josep/dog/docs/affordances/surfaces/room.md) |
| `Agents` | [agents.md](/home/josep/dog/docs/affordances/surfaces/agents.md) |

## Journey Documents

| Journey | Document |
| --- | --- |
| `Room + Agents` | [room-agents.md](/home/josep/dog/docs/affordances/journeys/room-agents.md) |
| `Story -> Room Runtime` | [story-room-runtime.md](/home/josep/dog/docs/affordances/journeys/story-room-runtime.md) |

## Walkthrough Sets

| Walkthrough Set | Document |
| --- | --- |
| `Room + Agents` | [README.md](/home/josep/dog/docs/affordances/walkthroughs/room-agents/README.md) |
| `Story -> Room Runtime` | [README.md](/home/josep/dog/docs/affordances/walkthroughs/story-room-runtime/README.md) |

## Global Surface Map

| Surface | Primary shape | Current status | Notes |
| --- | --- | --- | --- |
| `Repos` | shell + panel workspace | `partial` | rich viewer and layout affordances are present |
| `Projects` | CRUD + workspace host | `partial` | management flows exist; permission and page-layout semantics need validation |
| `Demos` | library + launch/manage | `partial` | strong library affordances; composition/runtime journeys extend elsewhere |
| `Story` | library + player + edit/room handoff | `partial` | browse/play is clear; authoring needs fuller mapping |
| `Room` | runtime collaboration assemblage | `partial` | highest integration surface, strongest walkthrough potential |
| `Agents` | library + detail + create/clone/edit + room participation | `partial` | creation and cloning are implemented; cross-surface role needs fuller coverage |

## Cross-Surface Intent Categories

These are the top-level user intents the walkthrough set should cover.

| Intent | Candidate surfaces |
| --- | --- |
| Discover and inspect assets | `Repos`, `Demos`, `Story`, `Agents`, `Projects` |
| Create a new working object | `Projects`, `Story`, `Agents`, `Room` |
| Configure or customize a surface | `Repos`, `Projects`, `Agents`, `Room` |
| Launch or enter an interactive session | `Demos`, `Story`, `Room` |
| Assemble related resources into one workspace | `Projects`, `Room`, `Demos` |
| Add or manage agent participation | `Agents`, `Room`, `Demos` |
| Share or gate access | `Projects`, `Repos` future, `Story` future/partial |

## Recommended First Walkthrough Backlog

| Walkthrough | Surfaces | Readiness | Why first |
| --- | --- | --- | --- |
| Create a project and attach resources | `Projects` | `partial` | core organizational model |
| Browse stories and create a room from a published story | `Story`, `Room` | `ready-ish` | clear user value and strong visible affordances |
| Open a room and add agents | `Room`, `Agents` | `ready-ish` | best current agent collaboration path |
| Publish a story and instantiate shared room runtime | `Story`, `Room` | `ready-ish` | core authored-to-runtime handoff |
| Clone a system agent and customize it | `Agents` | `ready-ish` | concise, self-contained lifecycle |
| Browse demos, inspect one, and launch it | `Demos` | `ready-ish` | simple end-user entry path |
| Open repo workspace and save a custom layout preset | `Repos` | `ready-ish` | demonstrates compositional affordances |
| Bind repo panels inside a room for co-working | `Repos`, `Room`, `Agents` | `partial` | high-value integrated journey |

## Open Gaps To Resolve Next

- convert each surface section into its own dedicated document using the template
- verify owner/editor/viewer behavior for `Projects` and `Room`
- map `Story` authoring/edit workflows explicitly
- map `Demo` runtime and builder journeys explicitly
- document `Agents` model settings and alternate creation path
- turn walkthrough sets into QA-ready validation runs with stable seeded fixtures
- decide whether to formalize this inventory as markdown only or also encode it in an affordance registry format
