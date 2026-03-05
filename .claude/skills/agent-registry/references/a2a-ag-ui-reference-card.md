# A2A + AG-UI Reference Card

Audience: Product Owners, GTM, Users  
Scope: Existing functionality only (current shipped behavior)

## What This Enables

- Multi-agent collaboration in Rooms.
- Agent-to-agent handoff through `@mentions` and tool-based assistance.
- Structured agent UI components (cards, tables, buttons, progress, etc.).
- Real-time token streaming during agent responses.

## Access Points

- Room list: `/rooms`
- Room workspace: `/r/{room_id}`
- Core room panels:
  - `Chat`
  - `Participants`
  - `Agent UI` (`a2ui`)
  - optional `Debug` (for internal visibility/testing)

## How Users Use It (Quick Flow)

1. Open or create a Room.
2. Add agents from the Participants panel (or party picker in Chat).
3. Send a prompt in Chat.
4. Trigger agents by:
   - participation mode (`always`/`on_mention`/`manual`)
   - explicit `@AgentName` mention
5. Watch streamed response text in Chat.
6. Interact with AG-UI buttons/components when present.
7. Use Agent UI panel to view structured components grouped by agent.

## Participation Modes (Current)

- `always`: responds to each room message.
- `on_mention`: responds when explicitly mentioned.
- `manual`: responds only when explicitly invoked by app flow/tooling.

## A2A Behavior (Current)

- Agents can trigger other agents via `@mentions` in responses.
- Agents can request another agent via a structured assistance tool.
- Internal agent messages are supported for audit/debug (`agent_internal` sender type).
- Coordinator pattern is supported (`is_coordinator`) and can run first.

## AG-UI Behavior (Current)

- Agents can emit structured UI components plus fallback text.
- Supported components include: `card`, `list`, `table`, `progress`, `action_buttons`, `code`, `quote`, `alert`, `collapsible`, `tabs`, `divider`.
- Action button clicks are sent back to backend (`/rooms/{room_id}/ui-action`) and re-invoke the originating agent.

## GTM Talking Points

- “Human + multiple agents in one room, with real-time outputs.”
- “Structured outputs, not just plain text chat.”
- “Supports specialist-agent routing and coordinator-led orchestration.”
- “Built on evented room architecture with streaming UX.”

## Product Owner Checklist

- Ensure room participants include the intended agents.
- Set participation modes intentionally by role/use case.
- Use coordinator only where orchestration is required.
- Validate AG-UI component usefulness and fallback readability.
- Confirm permissions and ownership expectations per room flow.

## Current Limitations (Short List)

- AG-UI actions re-invoke the originating agent; no standalone client-side action graph yet.
- Internal agent messages may be hidden by default in standard user views.
- A2A chaining has depth/guardrails; not an open-ended recursive graph.
- Room WebSocket currently accepts `message.send`; other writes use REST endpoints.
- Behavior quality depends on configured model/provider and prompt quality per agent.

## Success Criteria for Demos

- User asks one task, at least two agents contribute.
- One handoff via `@mention` or tool-based assistance is visible.
- At least one AG-UI component renders and is actionable.
- Streaming response feels live and coherent.

---

## Additive Review Comments (Code/Implementation)

- `AG-UI` component support in code includes `page_layout_preview` in addition to the listed set (`backend/app/services/agent_tools.py`), so the card is currently a curated subset.
- `@mention` parsing supports both `@AgentSlug` and `@"Agent Name"` forms, with slug matching that also allows hyphenated names (`backend/app/services/a2a_orchestrator.py`).
- `manual` participation agents are explicitly skipped for mention-triggered A2A chaining (`backend/app/services/a2a_orchestrator.py`), which aligns with the current participation-mode description.
- A2A depth is concretely capped at `2` in current implementation (`DEFAULT_MAX_A2A_DEPTH = 2`) and enforced in both mention orchestration and tool-based assistance (`backend/app/services/a2a_orchestrator.py`, `backend/app/services/agent_tools.py`).
- Coordinator behavior is correctly represented; implementation notes indicate multiple coordinators are allowed (though atypical), and they execute before regular agents (`backend/app/services/agent_runner.py`).
- AG-UI button actions are routed through `POST /rooms/{room_id}/ui-action`; backend verifies the source message is from an agent, reconstructs `[UI Action: ...]`, and invokes that originating agent (`backend/app/api/routes/rooms.py`).
- Internal A2A messages are persisted as `room_message.agent_internal` / `sender_type="agent_internal"` and intended for filtering in normal user views (`backend/app/services/event_emitter.py`, `backend/app/crud.py`).
- Room WebSocket write handling currently accepts `message.send`; other write interactions are handled via REST routes (`backend/app/api/routes/websocket.py`, `backend/app/api/routes/rooms.py`).

## Additive Review Questions

- Should this card explicitly call out `page_layout_preview` as supported, or keep it intentionally excluded for product/GTM simplicity?
- Should we add a short “UI Action Payload” note (`source_message_id`, `component_id`, `action`) so product and GTM can describe button-action traceability correctly?
- Should we explicitly document that `/ui-action` returns acceptance immediately and the resulting agent response arrives asynchronously over the normal stream?
- Should we add a one-liner that `manual` agents are still invocable via explicit API/UI paths even though mention-based triggers skip them?
- Should GTM copy keep “single coordinator recommended” language while noting multi-coordinator execution is technically supported?
