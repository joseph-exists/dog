# Walkthrough: Add Agents To A Story-Backed Room And Trigger Story-Aware Replies

Status: `ready-ish`
Persona: `operator`
Goal: verify that agents in a story-backed room can respond with awareness of the current story step

## Preconditions

- a room exists with attached story and active shared runtime
- you can see the `Story Runtime` panel
- you can add agents to the room

## Steps

1. Open `/r/$roomId`.
2. Confirm the `Story Runtime` panel shows the current node, choices, and story state.
3. Use participant management to add at least one agent.
4. Send a room message that refers to the current story step, such as asking what to do next.
5. Wait for the agent response in chat.
6. Compare the response against the visible current node, available choices, and story state.

## Expected Result

- the agent responds in room chat
- the response can plausibly reference the current story step or next choices

## Evidence

- shared runtime visible in UI:
  [StoryPanel.tsx](/home/josep/dog/frontend/src/components/Room/panels/StoryPanel/StoryPanel.tsx):143,
  [StoryPanel.tsx](/home/josep/dog/frontend/src/components/Room/panels/StoryPanel/StoryPanel.tsx):151,
  [StoryPanel.tsx](/home/josep/dog/frontend/src/components/Room/panels/StoryPanel/StoryPanel.tsx):165
- agents can be added:
  [AddParticipantDialog.tsx](/home/josep/dog/frontend/src/components/Room/Dialogs/AddParticipantDialog.tsx):55,
  [roomService.ts](/home/josep/dog/frontend/src/services/roomService.ts):936
- user message triggers agents:
  [rooms.py](/home/josep/dog/backend/app/api/routes/rooms.py):365
- backend includes runtime in prompt:
  [context_provider.py](/home/josep/dog/backend/app/services/context_provider.py):183,
  [agent_prompt.py](/home/josep/dog/backend/app/services/agent_prompt.py):42

## Limit

The frontend does not currently show the exact backend prompt payload. This
walkthrough verifies behavior by comparing visible story runtime against visible
agent output, not by inspecting the full serialized prompt.
