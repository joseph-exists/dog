# Walkthrough: Compare Coordinator And Specialist Responses To The Same Story Step

Status: `ready-ish`
Persona: `orchestrator designer`
Goal: verify that multiple agents can react to the same shared story step, with coordinator-first execution

## Preconditions

- a story-backed room is running shared `storyRuntime`
- the room has one coordinator-capable agent and at least one additional agent

## Steps

1. Open `/r/$roomId`.
2. Confirm the room shows the current story node and available choices.
3. Confirm the relevant agents are active in the room.
4. Send a message asking for guidance about the current story situation.
5. Observe the order and content of the returning agent messages.
6. Compare whether one response acts like orchestration while another acts like specialization.

## Expected Result

- multiple agents can respond to the same shared story step
- coordinator-first execution is supported by backend selection logic
- user can compare those replies in room chat/debug surfaces

## Evidence

- coordinators run first:
  [agent_runner.py](/home/josep/dog/backend/app/services/agent_runner.py):355,
  [agent_runner.py](/home/josep/dog/backend/app/services/agent_runner.py):395
- prompt includes other agents in room:
  [agent_prompt.py](/home/josep/dog/backend/app/services/agent_prompt.py):75
- agent responses are visible in room stream/UI:
  [useRoomStream.ts](/home/josep/dog/frontend/src/hooks/useRoomStream.ts):237,
  [RoomDebugPanel.tsx](/home/josep/dog/frontend/src/components/Room/panels/RoomDebugPanel.tsx):507

## Limit

This walkthrough validates shared-step, multi-agent response behavior. It does
not by itself prove sophisticated orchestration policies unless the specific
agent prompts/configurations already encode them.
