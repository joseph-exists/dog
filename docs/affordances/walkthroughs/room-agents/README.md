# Room + Agents Walkthroughs

Status: `partial`
Scope: executable operator and user walkthroughs for room-based agent runtime

## Purpose

These walkthroughs turn the higher-level
[room-agents.md](/home/josep/dog/docs/affordances/journeys/room-agents.md)
journey into concrete, repeatable scripts.

Each walkthrough is intended to be executable by a product reviewer, QA
operator, or engineer working from the frontend and current runtime.

## Walkthrough Set

| Walkthrough | Document | Readiness |
| --- | --- | --- |
| Add one agent to a room | [01-single-agent-room.md](/home/josep/dog/docs/affordances/walkthroughs/room-agents/01-single-agent-room.md) | `ready-ish` |
| Add multiple agents to one room | [02-multi-agent-room.md](/home/josep/dog/docs/affordances/walkthroughs/room-agents/02-multi-agent-room.md) | `ready-ish` |
| Validate AG-UI in chat and `A2UI` | [03-ag-ui-workflow.md](/home/josep/dog/docs/affordances/walkthroughs/room-agents/03-ag-ui-workflow.md) | `ready-ish` |
| Validate mention-based and coordinator orchestration | [04-a2a-orchestration.md](/home/josep/dog/docs/affordances/walkthroughs/room-agents/04-a2a-orchestration.md) | `partial` |
| Validate mixed-provider agents in one room | [05-mixed-provider-room.md](/home/josep/dog/docs/affordances/walkthroughs/room-agents/05-mixed-provider-room.md) | `partial` |

## Common Prerequisites

- frontend is running
- backend is running
- you can sign in with a user that can create rooms and manage room
  participants
- at least one room can be created or opened

## Important Runtime Caveats

- room participant management is owner-oriented today
- `A2A` and `AG-UI` capabilities may depend on runtime/route-level enablement
  outside obvious room UI controls
- provider diversity is configured on agents, but not strongly surfaced in room
  participant UI
- `agent_internal` traces may require debug/internal-message visibility to make
  hidden orchestration steps visible
