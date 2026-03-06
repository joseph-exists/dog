# Walkthrough 03: Validate AG-UI In Chat And `A2UI`

Status: `ready-ish`
Persona: `operator`

## Goal

Verify that an AG-UI-capable agent can emit rich UI in room chat and that the
same component stream can be inspected in the `A2UI` panel.

## Preconditions

- a room exists
- the room has at least `chat` and ideally `a2ui` panels
- at least one AG-UI-capable agent exists in the room
- runtime path enables AG-UI behavior for that flow

## Recommended Agent Setup

Use an existing AG-UI-focused agent if one exists. If not, the backend reference
guide includes a `UI Showcase Agent` and an `Interactive Assistant` pattern:
- `/home/josep/dog/backend/app/services/service-docs/agent-demo-quickstart.md`

## Steps

1. Open `/r/$roomId`.
2. Confirm the target agent is in participants.
3. Send a prompt likely to produce rich UI, for example:
   `Show me a compact project status with next steps and an action button.`
4. Observe the resulting room message.
5. If the room includes `A2UI`, open that panel.
6. Locate the emitted components grouped under the agent’s name.
7. If the UI contains action buttons, click one.
8. Wait for the follow-up agent response.

## Expected Results

- room chat renders non-text UI components inline
- `A2UI` groups the same or related components by agent
- clicking an action button sends a follow-up UI action through the room service
- the originating agent produces a follow-up response in the normal message stream

## Validation Checklist

- [ ] inline UI appears in chat
- [ ] `A2UI` is not empty when UI components exist
- [ ] action button click results in a new agent response
- [ ] room remains stable if a component fails or is unsupported

## Failure Modes

- no UI appears:
  agent may not emit AG-UI, or runtime may not have AG-UI tool path enabled
- chat shows only plain text:
  same as above, or prompt was not strong enough to induce UI output
- `A2UI` empty while chat has UI:
  panel may not be active, or message query/panel state may be stale

## Evidence

- `/home/josep/dog/frontend/src/components/Room/RoomMessages/Message.tsx`
- `/home/josep/dog/frontend/src/components/Room/panels/A2UIPanel.tsx`
- `/home/josep/dog/frontend/src/hooks/useAgentUI.ts`
