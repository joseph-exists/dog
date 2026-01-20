Existing tables you already have:

- `user_personas`: User ↔ Persona (many-to-many)
- `room_participants`: Room membership projection (user/agent participants)

New tables to add:

### 1) `agent_personas` (Agent ↔ Persona many-to-many library)

Purpose: allow an agent to “have personas” (a library of selectable personas). The active persona in a specific room is set via the bindings table below.

Columns (conceptual):

- `id` UUID PK
- `agent_id` UUID FK → `agent_configs.id` (on delete cascade)
- `persona_id` UUID FK → `persona.id` (on delete cascade)
- `created_at` timestamp

Constraints:

- Unique: (`agent_id`, `persona_id`)

### 2) `room_participant_bindings` (per-room per-participant active persona + runtime model/provider, with history)

Purpose: capture the active persona and runtime model/provider for a participant in a room, plus a history of changes (needed for provenance + Shadow pinning).

Important: `room_participants.participant_id` is currently a **string** that is described as “UUID string for users, agent name for agents”. To keep junior implementation safe, the plan below uses:

- `participant_type` + `participant_id` as the *addressing key* (what the room already stores),
- plus optional resolved IDs (`user_id`, `agent_id`) for referential integrity and joins.

Recommendation: standardize agent `participant_id` to `AgentConfig.slug` going forward, and treat “agent UUID string” handling as legacy compatibility.

Columns (conceptual):

- `id` UUID PK
- `room_id` UUID FK → `rooms.room_id` (on delete cascade)
- `participant_type` enum/str: `"user"` | `"agent"`
- `participant_id` str (the same addressing value used in `room_participants.participant_id`)

Optional resolved IDs (recommended if you can resolve reliably):

- `user_id` UUID FK → `user.id` (nullable; required when participant_type = `"user"`)
- `agent_id` UUID FK → `agent_configs.id` (nullable; required when participant_type = `"agent"`)

Active persona:

- `persona_id` UUID FK → `persona.id` (nullable allowed at DB level; app can require it for “active persona” semantics)

Runtime model/provider (participant-scoped):

- `model_name` str (same format as `AgentConfig.model_name`, e.g. `"openai:gpt-4o-mini"`)
- `user_llm_provider_id` UUID FK → `userllmprovider.id` (nullable; required when a user-owned provider config is selected)

History:

- `effective_at` timestamp (when this binding becomes active)
- `ended_at` timestamp nullable (NULL = active)
- `created_at` timestamp

Constraints:

- One active binding per (room, participant):
  - Postgres partial unique index on (`room_id`, `participant_type`, `participant_id`) WHERE `ended_at IS NULL`
  - If partial indexes aren’t available in a target env, enforce in application logic (close old row before inserting new).
- Type integrity:
  - If `participant_type='user'` then `user_id IS NOT NULL`
  - If `participant_type='agent'` then `agent_id IS NOT NULL`

Implementation note for juniors: the “close old row then insert new row” must be done in a single transaction, otherwise you can temporarily violate the “one active row” invariant under concurrency.

