# Story -> Room Runtime Walkthroughs

Status: `partial`
Scope: executable walkthroughs for authored story handoff into shared room runtime

## Purpose

These walkthroughs turn the higher-level
[story-room-runtime.md](/home/josep/dog/docs/affordances/journeys/story-room-runtime.md)
journey into repeatable scripts for product review, QA, and engineering
validation.

The most important concept carried through this set is the runtime boundary:
- `StoryEditor`, `StoryPreview`, and standalone story play are local authoring or
  local runtime surfaces
- room `storyRuntime` is the authoritative shared runtime
- room `storyPlayer` is local-only and should never be mistaken for shared room
  progression

## Walkthrough Set

| Walkthrough | Document | Readiness |
| --- | --- | --- |
| Publish story and create a room from it | [01-publish-and-create-room.md](/home/josep/dog/docs/affordances/walkthroughs/story-room-runtime/01-publish-and-create-room.md) | `ready-ish` |
| Start shared room runtime | [02-start-room-runtime.md](/home/josep/dog/docs/affordances/walkthroughs/story-room-runtime/02-start-room-runtime.md) | `ready-ish` |
| Advance, rewind, and reset shared runtime | [03-advance-rewind-reset.md](/home/josep/dog/docs/affordances/walkthroughs/story-room-runtime/03-advance-rewind-reset.md) | `ready-ish` |
| Compare shared `storyRuntime` with local-only `storyPlayer` | [04-runtime-vs-local-player.md](/home/josep/dog/docs/affordances/walkthroughs/story-room-runtime/04-runtime-vs-local-player.md) | `ready-ish` |
| Edit attached story from room while keeping runtime semantics straight | [05-room-story-editor.md](/home/josep/dog/docs/affordances/walkthroughs/story-room-runtime/05-room-story-editor.md) | `partial` |

## Common Prerequisites

- frontend is running
- backend is running
- you can sign in as a user who can edit stories and create rooms
- at least one story can be created and edited
- you can own or manage the room used for runtime validation

## Common Runtime Caveats

- room runtime writes are owner-oriented today
- a room can expose multiple story-related panels with different semantics
- `storyPlayer` inside a room is local-only even when `storyRuntime` is present
- in-room `storyEditor` is an authoring panel, not the shared runtime itself
