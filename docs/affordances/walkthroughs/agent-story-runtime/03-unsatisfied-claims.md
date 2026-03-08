# Walkthrough: Validate Unsatisfied Claims About Runtime Mutation And Auto-Triggering

Status: `ready-ish`
Persona: `systems reviewer`
Goal: explicitly confirm which desired agent-story interactions are not yet supported by verifiable evidence

## Claims Under Review

1. Agents can directly advance or reset shared `storyRuntime`.
2. Story runtime changes automatically trigger agents without a user message.
3. Frontend exposes the exact story-runtime payload sent to agents.

## Validation Procedure

1. Inspect the visible room runtime controls and note who can mutate runtime.
2. Inspect the known runtime mutation path in frontend/backend code.
3. Inspect the known agent trigger path in backend room messaging code.
4. Inspect the room debug UI for any exact story-runtime prompt payload display.

## Expected Result

The current evidence should lead to these conclusions:
- direct agent mutation of shared runtime is not verified
- automatic trigger on runtime transition is not verified
- exact runtime-to-agent prompt payload is not surfaced in current frontend UI

## Evidence

- runtime mutation path is user-facing:
  [useRoomRuntime.ts](/home/josep/dog/frontend/src/hooks/useRoomRuntime.ts):106,
  [room_runtime.py](/home/josep/dog/backend/app/api/routes/room_runtime.py):45
- room owners are explicitly handled for runtime writes:
  [useRoomRuntime.ts](/home/josep/dog/frontend/src/hooks/useRoomRuntime.ts):50
- agent trigger path is tied to user room messages:
  [rooms.py](/home/josep/dog/backend/app/api/routes/rooms.py):365
- runtime events currently invalidate UI state only:
  [useRoomStream.ts](/home/josep/dog/frontend/src/hooks/useRoomStream.ts):59,
  [useRoomStream.ts](/home/josep/dog/frontend/src/hooks/useRoomStream.ts):264
- debug panel shows message-context preview, not full prompt/runtime payload:
  [RoomDebugPanel.tsx](/home/josep/dog/frontend/src/components/Room/panels/RoomDebugPanel.tsx):122

## Interpretation

If these claims are desired product behaviors, they should be tracked as one of:
- hidden but already implemented elsewhere
- mis-wired in current frontend/backend integration
- missing backend contracts entirely
