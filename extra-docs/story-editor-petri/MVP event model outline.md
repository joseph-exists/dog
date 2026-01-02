## MVP event model outline (concise)

### Purpose and guarantees

- Events are the **source of truth** for game state; current state is a projection of events along the active timeline.[^1][^2]
- History is a **tree** (branching timelines) with a single active “head”; only the active root→head path is visible to players.[^1]
- Random NPC behavior (AI Agent interaction) is allowed, but any randomness that affects state must be captured in event data (seed or realized outcome) so projections/snapshots are stable for that branch.[^3]


### Streams and identity

- Stream boundary: one event stream per `game_id` (aggregate boundary).[^4][^5]
- Within a game, events form a DAG constrained to a **parent pointer tree**: each event has exactly one `parent_node_id` (except root).[^1]


### Core entities (conceptual)

- `Game`: container for all timelines/state.[^2]
- `Head`: pointer to the active node in the event tree (current reality).[^1]
- `Node`: immutable event record with parent link.[^1]


### Event record (envelope) fields

- `event_id` (UUID)
- `game_id` (stream id)[^4]
- `node_id` (UUID; unique within game)
- `parent_node_id` (nullable for root; otherwise points to prior node on this branch)
- `seq` / `stream_version` (monotonic per game for ordering/optimistic concurrency; still useful even with parent pointers)[^5][^4]
- `event_type` (string, versioned type name recommended, e.g. `cyoa.travel.v1`)[^6]
- `occurred_at` (timestamp)
- `actor_id` (e.g., personas)
- `payload` (JSON)
- `rng` (optional; seed and/or realized rolls/outcomes)[^3] (post V1, stub itout)


### Event types (minimum set)

All events correspond to “firing a transition” in the CPN sense, except `HeadMoved` which is timeline navigation.[^2][^1]

**Write-model (state-changing)**

- `GameStarted`
- `ChoiceMade` (sets flags / chooses branch)
- `Traveled` (character location change)
- `ItemAcquired`
- `ItemUsed` (mutates item state / consumes charges / sets flags)
- `TimeAdvanced`
- `ScheduledEventFired` (includes NPC movement outcomes if applicable)
- `JoinSceneResolved` (multi-character join; includes both character updates)

**Timeline navigation**

- `HeadMoved` (undo/jump; no marking change itself, just selects which node is current reality)[^1]


### Head semantics (branching + hidden futures)

- Append rule: new state-changing events always append as a **child of current head** and atomically advance head to the new node.[^2]
- Jump rule: `HeadMoved` may only target an **ancestor** of the current head in MVP.[^1]
- Visibility rule: APIs return only events on the **ancestor chain** of `head_node_id`; no listing of siblings/children (abandoned branches hidden).[^1]


### Concurrency and idempotency constraints

- Writes use optimistic concurrency on `(game_id, head_version/stream_version)` to prevent silent forks.[^5]
- Commands should include idempotency keys; repeated submissions must resolve to the same resulting `node_id` or a safe conflict response.[^7]


### Projection and snapshot hooks

- Projections build “current marking” read models from the active path events (snapshot + replay).[^8][^1]
- Snapshot records (if used) must reference `node_id` so reconstruction is “nearest snapshot ≤ head + events to head”.[^8]


### Publication (real-time)

- Persist event + head update + outbox row in one DB transaction; publish outbox to Redis/WebSocket subscribers.[^9][^10]
<span style="display:none">[^11][^12][^13][^14][^15][^16][^17][^18][^19][^20][^21][^22][^23]</span>

<div align="center">⁂</div>

[^1]: https://event-driven.io/en/projections_and_read_models_in_event_driven_architecture/

[^2]: https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing

[^3]: https://docs.eventsourcingdb.io/best-practices/designing-read-models/

[^4]: https://stackoverflow.com/questions/38573703/stream-version-in-event-sourcing

[^5]: https://softwaremill.com/implementing-event-sourcing-using-a-relational-database/

[^6]: https://docs.eventsourcingdb.io/best-practices/modeling-events/

[^7]: https://leanpub.com/esversioning/read

[^8]: https://www.kurrent.io/blog/snapshots-in-event-sourcing

[^9]: https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html

[^10]: https://blog.devops.dev/distributed-real-time-communication-scaling-websockets-with-redis-pub-sub-9a7db4f81cd0

[^11]: https://event-driven.io/en/on_putting_stream_id_in_event_data/

[^12]: https://docs.dapr.io/developing-applications/building-blocks/state-management/howto-outbox/

[^13]: http://valerii-udodov.com/posts/event-sourcing/events-versioning/

[^14]: https://debezium.io/blog/2019/02/19/reliable-microservices-data-exchange-with-the-outbox-pattern/

[^15]: https://stackoverflow.com/questions/47311911/event-sourcing-cqrs-read-model-projections

[^16]: https://eventsourcing.readthedocs.io/en/stable/topics/domain.html

[^17]: https://whackd.in/mastering-the-transactional-outbox-pattern-a-deep-dive-with-code-pitfalls-and-best-practices/

[^18]: https://martendb.io/tutorials/read-model-projections

[^19]: https://developer.confluent.io/courses/event-design/best-practices/

[^20]: https://www.kurrent.io/blog/live-projections-for-read-models-with-event-sourcing-and-cqrs

[^21]: https://www.decodable.co/blog/revisiting-the-outbox-pattern

[^22]: https://iyzico.engineering/outbox-pattern-best-practices-for-reliable-messaging-in-distributed-systems-923201f03fd5

[^23]: https://eventsauce.io/docs/reacting-to-events/projections-and-read-models/

