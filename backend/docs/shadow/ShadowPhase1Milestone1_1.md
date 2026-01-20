# Shadow — Milestone 1.1 (Bindings + Write-Path Hardening)

This is a follow-on artifact to Milestone 1 that turns the remaining Milestone 1 gaps into an executable, ordered checklist. It assumes these decisions are locked:

- Room integration bindings are event-sourced: emit `participant.binding_changed` and update `room_participant_bindings` during projection updates.
- Standardize `room_participants.participant_id` for agents to `AgentConfig.slug` (treat “agent UUID string” as legacy compatibility only if needed).

## Current state (what’s already done)

- `agent_personas` exists end-to-end: model + CRUD + routes + Alembic migration.
- Shadow versioning currently covers **agents** and **stories** only (create/update).

## 1.1 Goals (what “better place” means)

By the end of Milestone 1.1:

- We can set and read back a participant’s active persona + runtime model/provider for a room (single active binding per participant).
- Agent participants are addressed consistently by `AgentConfig.slug` (rooms + events + messages + context).
- A binding change emits a room event and updates the binding projection atomically.
- Shadow write-path coverage is expanded enough that rooms/bindings can be versioned safely (with secret redaction).

## Work plan (ordered steps)

### [complete] 0) Doc hygiene (quick fix)

- Remove/adjust any “ALL WORK COMPLETE AND VERIFIED” claims in `backend/docs/shadow/ShadowPhase1Milestone1.md` until bindings + write-path wiring are actually complete.

### 1) Standardize agent `participant_id` to `AgentConfig.slug`

**Why first**: everything else (bindings lookup, context selection, A2A) depends on a stable addressing key.

- Update room participant add flow to enforce:
  - `participant_type="agent"` → `participant_id` must be an existing `AgentConfig.slug` (and reject non-slug strings).
  - `participant_type="user"` → `participant_id` remains UUID string.
- Update any “available agents” / join flows so the frontend always sends the slug for agents.
- If you need legacy compatibility:
  - accept UUID strings for agents temporarily, but normalize to slug internally (and emit the event using slug).

**Acceptance checks**
- Adding an agent participant by slug works.
- Attempting to add an agent participant using a random name fails with a clear 400.

### 2) Add `room_participant_bindings` schema (models + migration)

Implement in `backend/app/models.py` + Alembic:

- Table: `room_participant_bindings`
- Key fields:
  - `room_id` FK → `rooms.room_id` (cascade)
  - `participant_type` (`"user"` | `"agent"`)
  - `participant_id` (string key; slug for agents, UUID string for users)
  - optional resolved IDs: `user_id` FK → `user.id` (nullable), `agent_id` FK → `agent_configs.id` (nullable)
  - `persona_id` FK → `persona.id` (nullable allowed at DB level)
  - runtime selection: `model_name` (string), `user_llm_provider_id` FK → `userllmprovider.id` (nullable)
  - history: `effective_at`, `ended_at`, `created_at`
- Constraints:
  - “one active binding per (room, participant)”:
    - Postgres partial unique index on (`room_id`, `participant_type`, `participant_id`) WHERE `ended_at IS NULL`
    - fallback: enforce in application logic (transaction: close old row then insert new)
  - type integrity checks (prefer DB-level CHECK constraints if you’re committing to Postgres):
    - if `participant_type='user'` then `user_id IS NOT NULL`
    - if `participant_type='agent'` then `agent_id IS NOT NULL`

**Acceptance checks**
- Migration applies cleanly.
- You can insert multiple historical bindings for the same participant (ended rows), but only one active row.

### 3) Emit `participant.binding_changed` and update binding projections

Add new room event type:

- `participant.binding_changed`
  - payload: `participant_type`, `participant_id`, optional resolved IDs, and the new binding values (persona_id/model_name/provider_id).

Update projection pipeline in `backend/app/services/event_emitter.py`:

- Add handler `_handle_participant_binding_changed` that:
  - resolves `user_id`/`agent_id` if possible (or trusts payload if you decide to).
  - closes the previous active binding row for that `(room_id, participant_type, participant_id)` by setting `ended_at`.
  - inserts a new binding row with `effective_at=event.created_at`, `ended_at=NULL`.
  - runs inside the same transaction as the event write.

**Acceptance checks**
- Binding updates are idempotent-ish at the API level (re-sending same binding should not create infinite churn).
- Under concurrency, you never end up with two active rows for the same participant.

### 4) Add API endpoints to set/read bindings (write + query)

Suggested new routes module: `backend/app/api/routes/room_participant_bindings.py`

- `GET /rooms/{room_id}/bindings` → list active bindings (and optionally history).
- `PUT /rooms/{room_id}/participants/{participant_id}/binding` (or `PATCH`) → set active binding for that participant.

Suggested CRUD functions in `backend/app/crud.py` (async)

- CRUD function should:
  - verify permissions (room membership / owner rules as appropriate).
  - validate the participant exists in `room_participants` and is active.
  - validate persona ownership rules:
    - if participant is user, persona must exist in that user’s `user_personas`
    - if participant is agent, persona must exist in that agent’s `agent_personas`
  - emit `participant.binding_changed` (do not write the binding table directly).

**Acceptance checks**
- You can set and fetch bindings for both user and agent participants.
- Invalid persona assignment is rejected with 400/403 (whichever matches your policy).

### 5) Shadow: expand entity types + room snapshot exporter (minimum viable)

Update `backend/app/core/config.py` + `backend/app/services/shadow_service.py`:

- Add service-account token slots + SERVICE_ACCOUNT_MAP entries for at least:
  - `room`
  - `persona`
  - `llm_model` (or `model`)
  - `user_llm_provider`
- Decide and document exact `entity_type` strings once; treat them as an API/DB/Forgejo contract.

Implement a **room snapshot exporter** (can start minimal):

- room metadata
- participants
- active `room_participant_bindings` rows
- (optional) linked `story_id` and story version pointers

**Non-negotiable**
- Provider snapshots must redact secrets (never store plaintext API keys/tokens).

**Acceptance checks**
- When a binding changes, a new **room** Shadow version is written (non-blocking).
- Snapshot JSON contains bindings but never contains secrets.

### 6) Wire Shadow versioning to binding changes + agent_personas changes

- On `participant.binding_changed` handling completion (or immediately after emitting event in the request handler), trigger room shadow versioning.
- On `agent_personas` create/update/delete, trigger agent shadow versioning or a dedicated “agent library” snapshot (decide which contract you want).

### 7) Tests + verification scripts

- Add focused tests for:
  - participant_id slug enforcement
  - “one active binding” invariant
  - binding event handler correctness (close old row + insert new)
  - permission + persona ownership rules
- Add/extend your room test scripts to include a binding-change scenario.

## Exit criteria (Milestone 1.1)

- `agent_personas` + `room_participant_bindings` are both real tables with migrations applied.
- Agent participants use `AgentConfig.slug` consistently in rooms.
- Binding changes are event-sourced and projection-updated transactionally.
- Room snapshot includes active bindings and is versioned on binding change.
- Provider secrets are redacted in any Shadow artifacts.

## Notes / intentionally deferred

- Full Milestone 1 Shadow coverage for *every* mutation point (story graph edits, persona quality changes, provider test result snapshots, etc.) can be staged after bindings are stable.
- Milestone 2 (read-path + context provider integration) should start only after `room_participant_bindings` and slug standardization are in place.
