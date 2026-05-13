# Documentation Guide

The documentation tree mixes current references, feature walkthroughs, implementation plans, and older design history. Start with this file, then follow the folder that matches the system you are changing.

## Current References

- `affordances/`: affordance schemas, surface mappings, runtime walkthroughs, and demo-builder flows.
- `agent-services/`: coordinator/orchestrator and agent service references.
- `architecture/`: room context, story state, and tool exposure architecture notes.
- `demos/`: demo builder, theming, and rendering references.
- `shadow/`: shadow repo/versioning design and implementation notes.
- `Story/` and `CYOA/`: story state schema, branching, and choose-your-own-adventure system history.
- `users/`: sharing and group documentation.
- `user-ui-customization/`: room/page panel customization notes.

## Exploratory Or Historical Areas

- `unsort/`: useful notes that have not been promoted into the current structure.
- `archived/`: retained history.
- `determinants-exploration/`: research and product semantics exploration.
- phase-named files: work logs and migration plans; verify against code before treating them as current truth.

## Repo-Level Docs

- `../README.md`: project overview and quick start.
- `../development.md`: local development workflow.
- `../deployment.md`: deployment and Traefik notes.
- `../backend/README.md`: backend-specific workflow.
- `../frontend/README.md`: frontend-specific workflow.
- `../tesser/README.md`: Tesserax rendering library and export service.
- `../kennel/README.md`: runtime environment service notes.

When updating docs, prefer linking to the current owner folder instead of copying long implementation details into multiple places.
