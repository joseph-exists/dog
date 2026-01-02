<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# i understand in-world travel now with the example above, but we will also need reader undo.  Let's create a specification for a relatively simple implementation that calls out which design patterns would be most useful - including creational, structural, and behavioral.  No code within the specification, but designed with an understanding that this would be implemented with a relatively common n-tier architecture.

A simple, robust “reader undo” design is to treat each reader choice as an immutable domain event (Command/Event Sourcing style), then implement Undo/Redo by moving a cursor backward/forward through that event stream and rebuilding the current read-state from events (optionally with snapshots for speed). This aligns well with established undo/redo approaches using Command and/or Memento patterns, and it fits cleanly into an n-tier setup with controllers → application services → domain model → repositories/unit-of-work.[^1][^2][^3][^4]

## Scope and assumptions

- Undo/redo is **per-reader per-story-run** (a “playthrough session”), not a global rewrite of the authored story.[^2]
- “Undo” means *reader undo* (rewind and choose differently), not in-world travel; the system must preserve causality by discarding or branching future events after an undo if the reader makes a new choice.[^2]
- Architecture: standard n-tier separation (presentation/API, application/service, domain, data access), with repositories mediating persistence and a unit-of-work coordinating atomic writes.[^3][^4]


## Conceptual model (domain)

**Core entities**

- **StoryDefinition**: immutable authored graph/net + assets + validation metadata (versioned).
- **PlaythroughSession**: reader’s run instance, bound to a StoryDefinition version.
- **EventLog**: ordered list of domain events for the session (append-only).[^2]
- **SessionCursor**: integer index pointing at the “current” event (supports undo/redo by moving the cursor).[^2]
- **DerivedReadState** (projection): current location, time, character states, inventory, flags, etc., computed from events (and/or from snapshots).[^2]

**Domain events (examples)**

- `ChoiceMade(scene_id, choice_id)`
- `StateMutated(delta)` (optional: more explicit events like `ItemAcquired(item_id)`)
- `TimeAdvanced(amount)`
- `CheckpointCreated(checkpoint_id)` (if supporting explicit reader bookmarks)


## Key workflows (user-visible)

### Make a choice

1. Validate that the choice is currently available for the reader’s DerivedReadState.
2. Append `ChoiceMade` to EventLog at cursor position; if cursor is not at end, truncate future (or create a branch, see below).[^2]
3. Advance cursor and update DerivedReadState projection.[^1][^2]

### Undo

1. Move SessionCursor back by 1 (or back to prior “decision event” if supporting multi-step atomic choices).[^2]
2. Recompute DerivedReadState by replaying events up to cursor (or load last snapshot ≤ cursor, then replay remainder).[^2]

### Redo

1. If no divergence occurred, move cursor forward by 1 and recompute/incrementally apply.[^2]
2. If divergence occurred (new choice after undo), redo stack is empty for the current branch (classic editor semantics).[^2]

## Recommended design patterns

### Creational patterns

- **Factory Method / Abstract Factory** for constructing StoryRuntime objects from StoryDefinition versions (e.g., create the correct “rule evaluator” for a story’s schema/version).[^4]
- **Builder** for assembling DerivedReadState projections from an event stream + optional snapshots (helps keep replay logic configurable: “strict replay”, “fast replay with snapshots”, “debug replay”).[^2]


### Structural patterns

- **Repository** for `StoryDefinitionRepository`, `SessionRepository`, `EventLogRepository`, `SnapshotRepository`, hiding persistence concerns from the domain/service layer.[^3]
- **Unit of Work** to commit “append event + update cursor + update snapshot pointers” atomically.[^3]
- **Facade** as an Application Service API: `PlaythroughService.make_choice()`, `undo()`, `redo()`, `get_current_view()`, shielding controllers/UI from internal event/snapshot mechanics.[^4]


### Behavioral patterns

- **Command pattern** to represent each undoable user action as an object/message with `execute` semantics and (optionally) `undo` semantics; even if undo is implemented via cursor rewind+replay, “Command” is still useful as the application-layer request model.[^1]
- **Memento pattern** (snapshots) to store occasional captures of DerivedReadState so replay is fast; undo becomes “restore previous memento” + small replay, rather than full replay.[^5][^2]
- **Observer / Pub-Sub** for projecting events into read models (UI view, analytics, progress metrics) without coupling the core playthrough logic to those concerns.[^4]


## Branching after undo (two acceptable semantics)

### Option A: “truncate future” (simplest; typical editor)

After undo, if the reader makes a new choice, delete events after cursor and append new events (redo history disappears). This matches common undo/redo stacks discussed in memento/command approaches.[^2]

### Option B: “explicit branches” (richer; supports exploring alternatives)

Keep future events but move them onto a named branch: event log becomes a tree (or DAG) with a “current head pointer”. This supports “compare two paths” and is closer to version-control semantics for interactive narrative.[^2]

## N-tier responsibilities (high level)

- **Presentation/API layer**: authentication, request validation, session routing, returns “current scene + available choices + UI diff”.[^4]
- **Application layer (services)**: transaction boundaries, calls repositories, enforces “truncate/branch on divergence”, emits domain events.[^3]
- **Domain layer**: Story rules (guards), state transition semantics, invariants (e.g., inventory cannot go negative), event definitions.[^2]
- **Data access layer**: repositories + unit-of-work implementation, event log storage, snapshot storage, indexing.[^3]

Question to lock the spec: should Undo operate at the granularity of **every micro-event** (e.g., “time advanced” is undoable) or at the granularity of a **reader turn** (one click = one undo step)?
<span style="display:none">[^10][^11][^12][^13][^14][^15][^16][^17][^18][^19][^20][^6][^7][^8][^9]</span>

<div align="center">⁂</div>

[^1]: https://stackoverflow.com/questions/3250104/fast-undo-redo-with-memento-command-pattern

[^2]: https://dev.to/npbee/command-based-undo-for-js-apps-34d6

[^3]: https://learn.microsoft.com/en-us/aspnet/mvc/overview/older-versions/getting-started-with-ef-5-using-mvc-4/implementing-the-repository-and-unit-of-work-patterns-in-an-asp-net-mvc-application

[^4]: https://stackify.com/n-tier-architecture/

[^5]: https://blog.postsharp.net/memento

[^6]: https://www.reddit.com/r/cpp/comments/ut7e2e/image_undoredo_implementation/

[^7]: https://www.linkedin.com/posts/djokic-stefan_memento-design-pattern-activity-7383783971819524096-P2Cn

[^8]: https://pmc.ncbi.nlm.nih.gov/articles/PMC7342081/

[^9]: https://stackoverflow.com/questions/12080339/n-tier-architecture-with-service-layer-business-layer-and-entity-framework

[^10]: https://blog.codeminer42.com/how-to-avoid-losing-your-app-state/

[^11]: https://www.mat.umk.pl/~folco/rpneditor

[^12]: https://www.reddit.com/r/dotnet/comments/17g22r4/what_is_the_difference_between_repository_and/

[^13]: https://github.com/vandekeiser/cmd-pattern

[^14]: https://arxiv.org/abs/1804.04607

[^15]: https://www.sciencedirect.com/science/article/pii/S0167642317302204

[^16]: https://ui.adsabs.harvard.edu/abs/arXiv:2101.07066

[^17]: https://devleader.substack.com/p/unit-of-work-pattern-in-c-for-clean-40f

[^18]: https://fi.episciences.org/9073

[^19]: https://github.com/khaledfmohamed/NTier-Repository-pattern-Unit-of-Work

[^20]: https://www.semanticscholar.org/paper/Reversible-Computation-in-Petri-Nets-Philippou-Psara/af18f007f3eb6e89a8102fd3b0e27b35d5c946ca

