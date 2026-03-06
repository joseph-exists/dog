# Room

Status: `partial`
Primary routes:
- `/rooms`
- `/r/$roomId`

Primary files:
- `/home/josep/dog/frontend/src/routes/_layout/rooms.tsx`
- `/home/josep/dog/frontend/src/routes/_layout/r.$roomId.tsx`
- `/home/josep/dog/frontend/src/hooks/useRoom.ts`
- `/home/josep/dog/frontend/src/hooks/useRoomPanels.ts`
- `/home/josep/dog/frontend/src/services/roomService.ts`

Related backend/services:
- `RoomsService`
- room message APIs
- room participant APIs
- room runtime/stream orchestration

Last reviewed: `2026-03-06`
Reviewer: `Codex`

## Summary

Room is the richest runtime collaboration surface in the frontend. It combines
message streaming, participants, optional story runtime/editor panels, AG-UI,
repo co-working panels, and per-room or per-user panel composition.

Primary user intents:
- enter a live collaboration room
- message and collaborate with users and agents
- customize the room panel assemblage

Key integrations:
- `Agents`
- `Story`
- `Repos`
- `Page` panel patterns

## Available High-Level Use Cases

| Use case | Status | Notes |
| --- | --- | --- |
| Browse rooms you can access | `verified-ish` | room list page exists |
| Create a room | `partial` | dialog exists on room list and story flows |
| Open room runtime | `verified-ish` | unified room route exists |
| Chat in a room | `verified-ish` | core runtime affordance |
| Add/remove participants | `partial` | hooks and panels exist |
| Add agents to a room | `verified-ish` | multiple quick-add/party-picker integrations exist |
| Use room default panels | `verified-ish` | resolved panel config exists |
| Override room panels per user | `verified-ish` | user override flow supported by hook/service |
| Use repo explorer and file viewer in room | `partial` | implemented and documented in a dedicated user reference |
| Emit shared repo selection/open/ref events | `partial` | runtime support exists |
| Use room context items with repo file context | `partial` | supported in room repo context flow |

## Walkthrough Candidates

- Open room, chat, and add an agent
- Customize panel layout for yourself vs room defaults
- Bind repo explorer and file viewer for co-working

## Open Questions And Gaps

- room walkthroughs should branch cleanly between owner/member/viewer experiences
- repo binding setup remains fairly operator-oriented
- story/editor/debug combinations need a clearer user-level explanation
