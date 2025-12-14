Phase 1 (Event Sourcing + Room Management) should ship four SQLModel-conformant models (rooms, room_events, room_participants, messages), plus a documented event-emitter skeleton, plus CRUD skeletons that make it fast to finish endpoints without violating the “append-only events + transactional projections” rules.[^1][^2][^3]

## Data models

Create the models in `backend/app/rooms/room-models.py` using the repo’s standard “Base / Create / Update / Table / Public / Collection” pattern and the established relationship-definition best practices (string forward refs + post-definition relationship binding when needed).[^4][^5]
All primary entities should follow the project’s UUID-primary-key convention, while still supporting the event-sourcing requirement for a monotonically increasing per-room `room_sequence` (enforced via a unique constraint on `(room_id, room_sequence)`).[^2][^5][^1]

Minimum tables/models to include now (no extra bespoke tables unless required by these constraints):[^1][^2]

- `Room` (projection): `room_id (UUID PK)`, `creator_id (UUID FK user)`, optional `story_id (UUID FK story)`, `title`, `created_at`, `last_activity`.[^2][^1]
- `RoomParticipant` (projection): `id (UUID PK)`, `room_id (FK)`, `participant_id (string: user UUID string or agent name)`, `participant_type (user|agent)`, `role (owner|member)`, `joined_at`, `left_at`, `active`, plus unique constraint `(room_id, participant_id)`. [^2][^1]
- `Message` (projection): `message_id (UUID PK)`, `room_id (FK)`, `sender_type (user|agent)`, optional `sender_id (UUID)` and optional `agent_name (string)`, `content`, `created_at`, with an index optimized for `(room_id, created_at desc)` access patterns. [^2][^1]
- `RoomEvent` (system of record): `event_id (UUID PK)`, `room_id (UUID)`, `room_sequence (bigint)`, `event_type (string)`, `payload (JSON/JSONB)`, `created_at`, plus unique constraint `(room_id, room_sequence)` and replay-friendly indexes.[^1][^2]

Migration workflow requirements (must be followed as part of Phase 1 completion): use Alembic autogenerate after models are added/updated, keep migrations in `backend/app/alembic/versions`, and do not edit already-applied migrations.[^5][^1]

## Event emitter skeleton

Update `backend/app/services/event_emitter.py` as the single write-path utility that appends to `RoomEvent` and updates `Room`, `RoomParticipant`, and `Message` projections in the same DB transaction to preserve strong read-after-write behavior.[^2][^1]
This module must be the only supported mechanism for room-related writes, and it must preserve the invariants: events are immutable (no UPDATE/DELETE), event ordering is per-room via `room_sequence`, and projections are fully rebuildable by replaying events in sequence order.[^1][^2]

This service must also conform to other project requirements for pydantic, sqlmodel, and fastapi best practices.

## Room CRUD skeleton

In a new file (`backend/app/for-review-crud.py`) add Phase-1 room operations which can be reviewed for addition to the centralized CRUD layer (`backend/app/crud.py`) so API routes can remain thin and consistent with existing repository patterns.[^6][^5]
All room-scoped operations must enforce authorization by checking active membership in `RoomParticipant` before allowing reads/writes, and owner-only actions must verify role `owner`.[^2][^1]  These membership checks should only use the dominant pre-existing pattern, and should require no additional utilities or bespoke implementation. Initial proposal follows.

- COMPLETE: file under review


## Participant API routes

Only add the participant-management routes needed to satisfy Phase 1 “rooms + participants + events + projections” behavior, and ensure each route’s contract is enforced by role/membership checks and by emitting the correct events.[^1][^2]
The minimum required participant endpoints (routes + contracts) are:[^2][^1]

- `POST /rooms/{room_id}/participants`: Owner-only; emits `participant.joined` for either a user or an agent, and must be idempotent for re-adding an inactive participant (reactivate via projection update from the join event).[^1][^2]
- `GET /rooms/{room_id}/participants`: Participant-only; returns the active participant list derived from the `RoomParticipant` projection (users and agents are both first-class participants).[^2][^1]
- `DELETE /rooms/{room_id}/participants/{participant_id}`: Owner-only; emits `participant.left` (soft-leave via `active=false` in projection), and must not delete historical events.[^1][^2]
- `PATCH /rooms/{room_id}/participants/{participant_id}/role`: Owner-only; emits `participant.rolechanged`, and must never grant an invalid role value outside the supported set.[^2][^1]

<div align="center">⁂</div>

[^1]: AgentEventRulesMaster.md

[^2]: MasterImplementationPlan.md

[^3]: SteelThreadReference.md

[^4]: data-model-best-practices.md

[^5]: CLAUDE.md

[^6]: crud-readme.md

