# Room + Agents

Status: `complete`
Primary persona: `room owner / operator`
Priority: `P0`


Last reviewed: `2026-03-06`


## Summary

`Room + Agents` is the most important current multi-agent collaboration journey
in the product. A room can contain multiple human users plus multiple agents,
with agent metadata surfaced in participants, agent responses streamed into
chat, AG-UI components rendered inline or in a dedicated `A2UI` panel, and
agent-to-agent triggers occurring through mention-based or tool-based
orchestration paths.

This journey document focuses on:
- adding one or many agents to a room
- running mixed-provider agents in the same room
- observing coordinator-driven orchestration
- observing A2A and AG-UI outcomes in chat and `A2UI`
- identifying where tooling is runtime-gated rather than guaranteed by the UI

## Summary Of What Is Frontend-Visible Today

| Capability | Frontend-visible status | Notes |
| --- | --- | --- |
| Add one agent to room | `verified-ish` | participant panel quick-add exists |
| Add multiple agents to room | `verified-ish` | chat header party-picker exists for owners |
| View agent metadata in room | `partial` | mode and coordinator badges visible; provider badge is not shown in room panel |
| Mixed-provider agents in same room | `partial` | room can host multiple agents; provider diversity is configured on agents, not surfaced strongly in room UI |
| Coordinator agent behavior | `partial` | coordinator badge visible; execution ordering is backend/runtime behavior |
| Mention-based A2A | `partial` | user-visible via follow-on agent messages; internal messages can be exposed in debug mode |
| Tool-based A2A | `partial` | runtime support exists behind tool enablement; not clearly toggleable in room UI |
| AG-UI inline in chat | `verified-ish` | agent UI components render inside messages |
| AG-UI in dedicated panel | `verified-ish` | `A2UI` panel aggregates UI components by agent |
| Agent tooling visibility | `stub/partial` | tooling is configured on agent records but is not deeply explorable from room UI |

## Role And State Matrix

| Dimension | Values | Notes |
| --- | --- | --- |
| Room role | `owner`, `member` | owner manages participants and room-level choices |
| Agent mode | `always`, `on_mention`, `manual` | surfaced in participant badges when metadata resolves |
| Agent coordination | `is_coordinator=true/false` | coordinator badge is shown in participants |
| Agent provider | per-agent provider type | configured on agent, not prominently surfaced in room UI |
| Tool flags | `enable_a2a_tool`, `enable_ag_ui_tool` | runtime-gated; may be enabled outside direct room UI |
| Internal visibility | `includeInternalMessages=true/false` | debug-style visibility of `agent_internal` messages |

## Core Use Cases

## Use Case: Add Agents To A Room

Status: `ready`
Primary persona: `room owner`
Priority: `P0`

### User Goal

Populate a room with one or more agents that can respond in the conversation.

### Entry Points

- `/r/$roomId`
- participant panel header quick-add
- chat header multi-agent picker

### Preconditions

- room exists and user can open it
- user is room owner to manage participants
- at least one visible agent exists in the library

### Primary Affordances

- `AgentQuickAdd` in participants
- `AgentPartyPicker` in chat header

### Main Success Path

1. Open a room as owner.
2. Use quick-add to add one agent, or use the party picker to add several.
3. Confirm the agent appears under participants.
4. Send a room message and observe responses based on each agent's participation mode.

### Outcomes

- agents appear as room participants
- room chat can now include agent messages
- participant badges show coordinator and participation-mode hints when available

### Empty, Error, And Blocked States

- Empty: room has no agents yet
- Error: participant mutation fails and toast error is shown
- Blocked: non-owners should not have manage affordances

## Use Case: Run Mixed-Provider Agents In One Room

Status: `ready`
Primary persona: `operator`
Priority: `P1`

### User Goal

Place agents backed by different providers/models in the same room and observe
them collaborating within the shared conversation.

### Entry Points

- `/agents` and `/agent/$agentId` for creation/config
- `/r/$roomId` for runtime collaboration

### Preconditions

- multiple personal or system agents exist
- those agents are configured against valid provider/model combinations
- room owner can add them to the same room

### Primary Affordances

- create/edit agent forms with provider/model selection
- room participant add flows

### Main Success Path

1. Create or clone multiple agents that use different provider/model setups.
2. Add them to one room.
3. Send a prompt broad enough to trigger more than one agent or route through a coordinator.
4. Observe each agent responding in the shared room stream.

### Outcomes

- a single room can host multiple agent configs regardless of provider diversity
- provider variance is operational, even though the room UI does not make it very explicit

### Important Current Limitation


# todo: fix participantPanel: clone from Demos -> Rooms
The room frontend does not prominently show provider badges or provider-grouped
state inside participants. Multi-provider support is therefore mostly a runtime
capability documented by agent configuration and observed in behavior, not a
strongly surfaced room affordance.

## Use Case: Observe Coordinator-Based Orchestration

Status: `ready`
Primary persona: `operator`
Priority: `P1`

### User Goal

Use a coordinator agent to route user messages to specialist agents in the same
room.

### Preconditions

- one room participant agent is configured with `is_coordinator=true`
- specialist agents are also present in the room
- their participation modes allow coordinated execution

### Primary Affordances

- coordinator badge in participants
- chat stream showing sequenced responses
- optional internal-message visibility for deeper debugging

### Main Success Path

1. Add a coordinator agent and several specialists to the room.
2. Send a prompt that should trigger routing behavior.
3. Observe the coordinator respond first.
4. Observe specialist follow-up responses triggered through mentions or orchestration.

### Outcomes

- routing is visible as a pattern in the message stream
- the UI shows which room participant is the coordinator, but not the full orchestration graph

### Caveat

Execution ordering is primarily enforced in backend/runtime orchestration, not
declared by the room UI itself.

## Use Case: Observe Mention-Based A2A

Status: `partial`
Primary persona: `operator`
Priority: `P1`

### User Goal

See one agent trigger another via `@mention` within the same room.

### Preconditions

- multiple agents are in the room
- mentioned agent is active and not in manual-only mode
- A2A depth has not been exceeded

### Main Success Path

## accessible via typer agent-demos: demo4-orchestrator

1. Add a routing or analyzer agent plus one or more specialists.
2. Send a prompt that causes the first agent to mention another agent.
3. Observe a follow-on response from the mentioned agent.
4. Optionally enable internal message visibility to inspect internal trigger traces.

### Outcomes

- user sees chained agent responses in chat
- debug-oriented internal messages can expose hidden A2A triggers

### Caveat

This is visible behavior, but the actual trigger logic lives in the backend
`A2AOrchestrator` with depth limiting and participation-mode checks.

## Use Case: Observe Tool-Based A2A

Status: `Ready`
Primary persona: `operator`
Priority: `P1`

### User Goal

See an agent use a request-for-assistance tool path rather than only mention
chaining.

### Preconditions

- room contains agents configured for the scenario
- runtime path enables `enable_a2a_tool`
- triggering route or orchestration layer passes the tool flag through

### Outcomes

- user may observe specialist consultation effects in the conversation
- the room UI does not currently expose a first-class toggle or indicator that
  tool-based A2A is enabled for this invocation

### Caveat

This is an important walkthrough topic, but currently requires careful wording:
it is a valid runtime capability, not a clearly self-service room UI feature.

## Use Case: Consume AG-UI In Chat And In A2UI

Status: `verified-ish`
Primary persona: `room participant`
Priority: `P0`

### User Goal

Interact with rich UI emitted by agents, both inline in chat and in the
dedicated `A2UI` panel.

### Preconditions

- room has an `a2ui` panel in the current resolved panel set, or agent UI appears inline in chat
- runtime path enables AG-UI tool registration when needed
- agents emit `ui_components`

### Primary Affordances

- inline `AgentUIRenderer` inside room messages
- `A2UI` panel grouping components by agent
- action buttons that post back to the room service

### Main Success Path

1. Add an AG-UI-capable agent to the room.
2. Send a prompt that causes the agent to emit cards, lists, progress, alerts, or action buttons.
3. Observe those components in the message stream.
4. If the room panel set includes `A2UI`, inspect the dedicated panel for grouped agent UI.
5. Click an action button and observe a follow-up agent response.

### Outcomes

- rich UI components render from room messages
- actions are sent back through `sendUIAction`
- follow-up responses arrive in the normal room message stream

## Affordance Inventory

| Affordance | User-visible control | Route or location | Preconditions | Outcome | Evidence |
| --- | --- | --- | --- | --- | --- |
| Add one agent | participant quick-add | room participants panel | owner + visible agents | agent joins room | `/home/josep/dog/frontend/src/components/Room/panels/ParticipantPanel.tsx` |
| Add many agents | party picker | room chat header | owner + visible agents | several agents join room | `/home/josep/dog/frontend/src/components/Room/panels/ChatPanel.tsx` |
| View agent metadata | badges in participants | room participants panel | agent metadata resolves | see coordinator/mode | `/home/josep/dog/frontend/src/components/Room/panels/ParticipantPanel.tsx` |
| Toggle internal messages | debug-style visibility | room/debug chat flows | room supports internal message query | inspect `agent_internal` events | `/home/josep/dog/frontend/src/routes/_layout/r.$roomId.tsx` |
| Render AG-UI inline | buttons/cards/lists in chat | room messages | agent emits UI components | rich UI in chat | `/home/josep/dog/frontend/src/components/Room/RoomMessages/Message.tsx` |
| Render AG-UI in panel | `A2UI` panel | room panel assemblage | `a2ui` panel configured | grouped agent UI view | `/home/josep/dog/frontend/src/components/Room/panels/A2UIPanel.tsx` |

## Tooling, A2A, And AG-UI Notes

### Agent Tooling

- agent records already carry `tool_config`, `deps_config`, `capabilities`, and
  `max_tool_iterations` at the config level
- room users do not currently get a strong runtime-facing tooling inspector in the room UI
- agent tooling is therefore a valid documentation topic, but not yet a strong
  end-user affordance in-room

### A2A

- mention-based A2A is a good walkthrough candidate because users can observe
  it from chat behavior alone
- tool-based A2A is real, but should be documented as runtime-enabled behavior
  that may depend on route-level flag propagation
- the backend depth limit currently defaults to `2`

### AG-UI

- AG-UI is the clearest user-visible advanced capability in this journey
- it appears both inline and in the dedicated `A2UI` panel
- action buttons are the strongest walkthrough anchor because they create a
  visible round-trip from UI interaction back into agent response flow

## Recommended Walkthrough Backlog

| Walkthrough | Readiness | Notes |
| --- | --- | --- |
| Add one agent to a room and chat with it | `ready` | simplest first journey |
| Add multiple agents to one room | `ready` | uses party picker and participant panel |
| Coordinator routes to specialists | `ready` | depends on curated agent setup |
| Mention-based A2A in one room | `ready` | good candidate with demo agents |
| Mixed-provider agents in one room | `ready` | real capability, weakly surfaced in room UI |
| AG-UI card/button workflow in room chat + A2UI | `ready` | strongest advanced visible path |
| Tool-based A2A consultation | `partial` | depends on runtime tool toggles, hidden from view but works |

## Open Questions And Gaps

-  `enable_a2a_tool` and `enable_ag_ui_tool` need to be exposed more directly
- demo/runtime routes need to enable/override these toggles consistently
- provider identity should be surfaced directly in the room participants UI for multi-provider walkthroughs
- a dedicated orchestration/debug panel should be part of the standard room walkthrough set



Primary routes:
- `/rooms`
- `/r/$roomId`
- `/agents`
- `/agent/$agentId`

Primary files:
- `/home/josep/dog/frontend/src/routes/_layout/r.$roomId.tsx`
- `/home/josep/dog/frontend/src/components/Room/panels/ChatPanel.tsx`
- `/home/josep/dog/frontend/src/components/Room/panels/ParticipantPanel.tsx`
- `/home/josep/dog/frontend/src/components/Room/panels/A2UIPanel.tsx`
- `/home/josep/dog/frontend/src/hooks/useRoom.ts`
- `/home/josep/dog/frontend/src/hooks/useAgentUI.ts`
- `/home/josep/dog/frontend/src/components/Room/RoomMessages/Message.tsx`
- `/home/josep/dog/frontend/src/components/Agents/Dialogs/CreateAgentDialog.tsx`
- `/home/josep/dog/frontend/src/components/Agents/Dialogs/AgentCloneButton.tsx`

Related backend/runtime references:
- `/home/josep/dog/backend/app/services/a2a_orchestrator.py`
- `/home/josep/dog/backend/app/services/service-docs/agent-demo-quickstart.md`
- `/home/josep/dog/backend/app/services/service-docs/agent-runner-tool-toggles.md`