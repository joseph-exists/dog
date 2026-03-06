# Agents

Status: `partial`
Primary routes:
- `/agents`
- `/agent/$agentId`

Primary files:
- `/home/josep/dog/frontend/src/routes/_layout/agents.tsx`
- `/home/josep/dog/frontend/src/routes/_layout/agent.$agentId.tsx`
- `/home/josep/dog/frontend/src/components/Agents/panels/AgentsGridPanel.tsx`
- `/home/josep/dog/frontend/src/components/Agents/Dialogs/CreateAgentDialog.tsx`
- `/home/josep/dog/frontend/src/components/Agents/Dialogs/AgentCloneButton.tsx`
- `/home/josep/dog/frontend/src/components/Agents/Dialogs/AgentDetailDialog.tsx`

Related backend/services:
- `AgentsService`
- provider/model catalog and prompt builder-related agent config paths

Last reviewed: `2026-03-06`
Reviewer: `Codex`

## Summary

Agents are configurable runtime actors that can be created, cloned, edited, and
added to live collaborative surfaces. The current frontend already exposes a
full personal-agent lifecycle and partial integration with demo and room flows.

Primary user intents:
- browse and inspect agents
- create or clone a personal agent
- add agents into collaborative runtime surfaces

Key integrations:
- `Room`
- `Demos`
- provider/model configuration surfaces

## Available High-Level Use Cases

| Use case | Status | Notes |
| --- | --- | --- |
| Browse agents library | `verified-ish` | grid panel exists |
| Distinguish personal vs system agents | `verified-ish` | split sections in library |
| Create a personal agent | `verified-ish` | create dialog exists |
| Create an “Agentus” variant | `stub` | alternate create dialog exists; separate workflow still needs mapping |
| View agent details | `verified-ish` | detail dialog and full detail page exist |
| Edit a personal agent | `verified-ish` | detail dialog supports edit for personal agents |
| Clone a system agent into a personal agent | `verified-ish` | clone button and create flow exist |
| Delete a personal agent | `verified-ish` | delete action on personal agents |
| Review agent model settings | `partial` | model settings UI exists on detail page area; not yet mapped here |
| Add agent to a room | `verified-ish` | room participant/chat integrations exist |
| Add agent to a demo-backed session | `partial` | demo runtime route includes agent add flows |

## Intersections Matrix

| Agents + Surface | Current intersection | Status | Notes |
| --- | --- | --- | --- |
| `Agents x Room` | agents can be added as participants; chat and party-picker flows exist | `verified-ish` | strongest current agent integration |
| `Agents x Demos` | demo runtime routes can add agents to active sessions | `partial` | needs walkthrough normalization |
| `Agents x Story` | stories can be experienced in rooms where agents also participate | `partial` | intersection is mostly runtime-mediated |
| `Agents x Repos` | repo context can coexist with agent collaboration inside rooms | `partial` | documented indirectly through room repo co-working |
| `Agents x Projects` | projects can attach rooms/repos/stories/demos, which may indirectly include agent workflows | `stub` | no explicit project-agent management surface found yet |

## Walkthrough Candidates

- Create a personal agent from scratch
- Clone a system agent and customize it
- Open room and add one or more agents to collaborate

## Open Questions And Gaps

- no normalized walkthrough yet for “Agentus” creation path
- no dedicated documented journey for agent lifecycle from creation to room/demo use
- project/repo/story intersections are mostly indirect and should be documented as journeys rather than standalone agent pages
