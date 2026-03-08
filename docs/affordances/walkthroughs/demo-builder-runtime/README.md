# Demo Builder -> Demo Runtime Walkthroughs

Status: `partial`
Scope: executable walkthroughs for taking an authored demo composition into resolved live runtime

## Purpose

These walkthroughs turn the higher-level
[demo-builder-runtime.md](/home/josep/dog/docs/affordances/journeys/demo-builder-runtime.md)
journey into repeatable scripts for product review, QA, and engineering
validation.

The most important concept carried through this set is the handoff boundary:
- `demo-builder` is the authoring and preview surface
- `/demo/$slug` is the authoritative saved-runtime target
- some capabilities become fully testable only after save and resolved session creation

## Walkthrough Set

| Walkthrough | Document | Readiness |
| --- | --- | --- |
| Create a demo from a template and resolve setup requirements | [01-template-to-save.md](/home/josep/dog/docs/affordances/walkthroughs/demo-builder-runtime/01-template-to-save.md) | `ready-ish` |
| Build a story-coupled demo assembly | [02-story-coupled-demo.md](/home/josep/dog/docs/affordances/walkthroughs/demo-builder-runtime/02-story-coupled-demo.md) | `ready-ish` |
| Configure click-to-chat interaction from block to panel | [03-click-to-chat.md](/home/josep/dog/docs/affordances/walkthroughs/demo-builder-runtime/03-click-to-chat.md) | `ready-ish` |
| Preview, save, and open the resolved demo runtime | [04-preview-save-open.md](/home/josep/dog/docs/affordances/walkthroughs/demo-builder-runtime/04-preview-save-open.md) | `ready-ish` |
| Operate a live demo runtime with layout, participants, and runtime-only actions | [05-live-runtime-operations.md](/home/josep/dog/docs/affordances/walkthroughs/demo-builder-runtime/05-live-runtime-operations.md) | `partial` |

## Common Prerequisites

- frontend is running
- backend is running
- you can sign in as a user who can access demo builder and save demo configs
- at least one story exists if you want to validate story-coupled panels
- room-backed runtime services are available for resolved demos

## Common Runtime Caveats

- builder preview and resolved runtime are related but not identical
- some interactions require a saved config and resolved slug-backed session
- canvas/tesser actions depend on async worker availability
- participant and agent operations depend on room/runtime permissions
