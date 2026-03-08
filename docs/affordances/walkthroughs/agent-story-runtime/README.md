# Agent -> Story Runtime Walkthroughs

Status: `partial`
Scope: executable walkthroughs for validating how agents and shared story runtime interact in a room

## Purpose

These walkthroughs operationalize
[agent-story-runtime.md](/home/josep/dog/docs/affordances/journeys/agent-story-runtime.md)
into evidence-oriented review scripts.

This set is intentionally split between:
- satisfiable behavior we can validate now
- unsatisfied claims that should be treated as wiring gaps or missing contracts

## Walkthrough Set

| Walkthrough | Document | Readiness |
| --- | --- | --- |
| Add agents to a story-backed room and trigger story-aware replies | [01-story-aware-agent-replies.md](/home/josep/dog/docs/affordances/walkthroughs/agent-story-runtime/01-story-aware-agent-replies.md) | `ready-ish` |
| Compare coordinator and specialist responses to the same story step | [02-coordinator-vs-specialists.md](/home/josep/dog/docs/affordances/walkthroughs/agent-story-runtime/02-coordinator-vs-specialists.md) | `ready-ish` |
| Validate unsatisfied claims: runtime mutation and auto-trigger gaps | [03-unsatisfied-claims.md](/home/josep/dog/docs/affordances/walkthroughs/agent-story-runtime/03-unsatisfied-claims.md) | `ready-ish` |

## Common Prerequisites

- frontend is running
- backend is running
- you can access a room with `storyRuntime`
- you can add agents to that room
- the room has an attached story and active runtime

## Common Caveats

- room owners are still the visible runtime mutators in current UI
- backend prompt construction includes story runtime, but frontend does not yet expose that payload directly
- agents are triggered by user messages in verified code; automatic triggers on runtime transitions are not verified
