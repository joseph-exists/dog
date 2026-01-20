# Shadow Work Plan (Milestones 1–3)

## References:

```
    `backend/docs/shadow/ShadowPhase1Milestone1.md`
    `backend/docs/shadow/ShadowPhase1Milestone1_1.md`
    - `backend/docs/shadow/ShadowPhase2Milestone2_TechnicalSpec.md`
    - `backend/docs/shadow/ShadowPhase2Milestone2_ImplementationGuide.md`
```

This document turns the Shadow goals in `backend/docs/shadow/shadow-overview.md` and our design conversation into an executable implementation plan. It includes a minimal schema to support:

- One active persona per participant per room (users and agents)
- Agent identity stability (UUID/slug stable through config changes)
- Agent cloning across users (new owner must specify config/credentials; provenance preserved)
- Different participants using different model/provider combos at the same time  (ie Sam and Aneeta are both in a room together with several of their agents - Sam's agent Munk is using GPT5.2 with OpenAI API, and his agent Jarnowitz is using Hermes from Nous. Aneeta's agent Gilda is using Anthropic, but she switches halfway through to Ollama. )
- Reading *from* Shadow repos into the context provider (not just writing)

## Decisions recap

- Persona selection is **room-scoped and participant-scoped**: each participant has **exactly one active persona** in a room at a time.
- Runtime model/provider selection is also **participant-scoped** and can vary across participants in the same room.
- Agent identity is stable: modifying config (including provider/model) does **not** change agent UUID/slug.
- Agent cloning creates a **new agent identity** owned by the new user, but should preserve provenance (source repo/commit) and require the new owner to set credentials/config.

## Glossary / ontology (read this first)

This plan crosses multiple domains (Rooms, Agents, Personas, Models/Providers, Story). To avoid “same word means different thing” confusion:

- **Agent**: the stable identity used in rooms and A2A. In the current codebase this maps most closely to `AgentConfig` (`agent_configs.id` + `agent_configs.slug`). The key decision is that **UUID/slug stays stable** even when the agent’s runtime config changes.
- **Agent config vs runtime binding**:
  - **AgentConfig**: persisted “default configuration” for an agent (e.g., system prompt, tool config, default `model_name`).
  - **Room participant binding**: the *per-room, per-participant* runtime selection of persona + model/provider. This is what makes “two agents in the same room can run different models” coherent.
- **Persona library vs active persona**:
  - **Library**: a set of personas a user/agent can choose from (`user_personas`, `agent_personas`).
  - **Active persona**: the single persona currently selected for a specific participant in a specific room (stored in `room_participant_bindings`).
- **Model vs provider vs credentials**:
  - **Model**: “what model do we call” (string id like `openai:gpt-4o-mini`, or a catalog record).
  - **Provider config**: “where/how to call it” (base URL + API key + settings). In this codebase, user-owned provider configs are `UserLLMProvider` (`/llm-providers`), and API keys must never be shadowed in plaintext.  **TODO** link to system providers here somewhere.
- **Shadow snapshot**: a JSON artifact committed to Forgejo representing *one coherent state* of an entity (or aggregate), used for provenance and potentially as a context provider source.

## Minimal tables + constraints (for Milestone 1)

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

## Extended milestone implementation plan (Rooms, Personas, Agents, Models, Story)

### Milestone 1 — Write-path Shadow coverage + bindings schema (POC across all five domains)

**1) Schema + APIs for persona/model binding**

- Add the two new tables above (`agent_personas`, `room_participant_bindings`) with constraints.
(REQUIREMENT: FOLLOW ALL DATA_MODEL_RULES.md - tests must validate data model rules are followed, tests must validate and document alembic upgrade pattern.  don't bork the db with haste or lazy.)
- Add API/service methods:
  - Set active persona for a room participant (closes previous active binding row; inserts new row).
  - Set active runtime model/provider for a room participant (same pattern; can be combined into one “binding update” call).
- Decide addressing rules:
  - `participant_id` for users should be UUID string.
  - `participant_id` for agents should be their stable `AgentConfig.slug` (preferred) or UUID string (legacy): UUID will be deprecated for slug in near future.

Cross-domain note: this “binding update” touches *Room* (membership), *Persona* (selection), and *Models/Providers* (runtime config). Treat it as a single cohesive concept: “how this participant is configured to speak/act in this room right now - this is a collective representation of state, and if any aspect changes, that's a new state that requires a new update.”.

**2) Snapshot exporters (write-side)**

Build exporters that produce a stable JSON envelope:

- Common envelope fields: `entity_type`, `entity_id`, `owner_id` (if applicable), timestamps, and `links` (provenance pointers).
- Story exporter: Story + nodes + choices + state vars (+ requirements if applicable).
- Room exporter: room metadata + participants + *active* `room_participant_bindings`.
- Persona exporter: Persona + qualities + quality state (as applicable) + event-derived changes.
- Agent exporter: AgentConfig + capabilities + prompt/config blobs (+ optional persona library pointers).
- Models/providers exporters:
  - Custom models from `/llm-catalog/models/custom`
  - User provider configs from `/llm-providers` with **secrets redacted**.

Redaction rule (non-negotiable): never commit plaintext secrets (API keys, tokens) to Shadow. If a snapshot includes provider config, store only non-secret fields (provider type, base URL, “is_default”, last tested timestamps) and a placeholder like `api_key_present=true`.

**3) ShadowService configuration expansion**

- Add entity types + service tokens for: `room`, `persona`, `llm_model`, `user_llm_provider` (names can be adjusted). ensure extensibility for entitytypes, or you'll be very sorry during code review and refactor.
- Keep consistent repo naming and file layout so reads are predictable later.  

Junior-friendly naming guidance: pick and document the exact `entity_type` strings once (e.g., `room`, `story`, `agent`, `persona`, `llm_model`, `user_llm_provider`) and treat them as API/DB/Forgejo contract. Avoid inventing new spellings in different modules.  Ensure that the contract is documented explicitly. see rules for guidance.

**4) Wire Shadow versioning to real mutation points**

- Story:
  - Keep story create/update shadowing.
  - Add shadowing on story graph edits: StoryNode + NodeChoice create/update/delete → export the whole story snapshot.
  - Add shadowing to `/stories/{id}/new-version`.
- Rooms:
  - Shadow on room create/update.
  - Shadow on participant add/remove.
  - Shadow on binding changes (persona/model/provider changes).
- Personas:
  - Shadow on persona create/update/delete.
  - Shadow on persona quality add/remove.
  - Shadow on persona event processing.
  - Shadow on user_personas changes.
  - Shadow on agent_personas changes.
- Agents:
  - Already shadowed on create/update; add tombstone on delete.
  - For clone flow: new agent repo should record provenance (`forked_from_id` + source commit SHA stored in snapshot links).
- Models/providers:
  - Shadow on custom model create.
  - Shadow on user provider create/update/delete; redact secrets; optionally store test results as a separate “event snapshot”.

What to shadow when a binding changes: treat it as a **Room-level Shadow update**, because it changes the effective runtime configuration of the room’s participants. Concretely: update the room snapshot exporter to include the active binding rows, and version the room repo when bindings change.

**5) Safety + correctness**

- Add idempotency to shadow writes (avoid duplicate versions on retries).
- Handle Forgejo file SHA conflicts (refetch + retry).

### Milestone 2 — Read-path + Context Provider integration (Shadow becomes a first-class context source)

**1) Shadow read service**

- Read latest snapshot for `(entity_type, entity_id)` from Forgejo.
- Read snapshot by pinned `commit_sha` or `version_number` (via `ShadowVersion`).
- Provide prompt-friendly summaries for each domain (room/story/persona/agent/model/provider).

**2) Deterministic “what to load” rules for context**

Use `room_participant_bindings` as the runtime truth for “what the participant is using right now”, and then pull:

- Room-wide: room snapshot summary, story snapshot summary (if room.story_id).
- Agent-scoped: current agent’s active persona summary + current agent’s runtime model/provider summary.

**3) Feed the existing context pipeline**

- Represent Shadow reads as `ContextItem`s (source=`shadow`) so they flow through `extra_contexts`.
- Ensure A2A tool calls build context with `agent_slug` so the correct agent-scoped binding is applied.
- Add caching by `(repo, sha)` in Redis; fallback to DB snapshots when Forgejo is unavailable (mark stale).

Cross-domain pitfall: “agent_slug” is not the same thing as `room_participants.participant_id` for agents unless you standardize it. When implementing Milestone 2, enforce a single mapping path:

- `current_agent_slug` (runtime) → resolve `AgentConfig` → resolve the corresponding `(participant_type='agent', participant_id=<slug>)` binding row.

### Milestone 3 — Provenance + async processing (align with the Shadow overview)

THIS MILESTONE NEEDS FURTHER REVIEW PRIOR TO IMPLEMENTATION.  ONLY PROCEED ONCE MILESTONE 1 and 2 ARE FULLY VALIDATED.

**1) Asyncify Forgejo IO**

- Replace in-request Forgejo commits with an outbox/job queue + worker.
- Worker: ensure repo → commit → retry/backoff → persist SHA/error diagnostics.

#### Current-state reality check (what we have today)

Today, Forgejo IO happens in-process via synchronous calls in `backend/app/services/shadow_service.py`:

- Repo creation: `ShadowService.ensure_shadow_repo(...)` → `RepositoryApi.create_current_user_repo(...)`
- Commit/write: `ShadowService.create_version(...)` → `RepositoryApi.repo_get_contents(...)` then `repo_update_file(...)` / `repo_create_file(...)`

“Non-blocking” in several routes currently means “wrapped in a try/except”, not “moved off the request thread”.

#### Touchpoint inventory (breadth)

Request-path synchronous Forgejo writes (highest impact if we asyncify):

- Agents:
  - `backend/app/api/routes/agent_routes.py` (`create_agent`, `update_agent`) calls `shadow_service.create_entity_version(...)`
  - `backend/app/api/routes/agent_personas.py` (create/update/delete agent persona) calls `shadow_service.create_entity_version(...)` for `entity_type="agent"`
- Stories:
  - `backend/app/api/routes/stories.py` (`create_story`, `update_story`) calls `shadow_service.create_entity_version(...)`

Post-response background task (still in the web process, not durable):

- Rooms:
  - `backend/app/api/routes/room_participant_bindings.py` schedules `shadow_room_version_best_effort(...)`
  - `backend/app/services/shadow_tasks.py` opens a sync DB `Session(engine)` and calls `shadow_service.create_entity_version_with_owner(...)`

Note: the snapshot builders for Milestone 1/2 entity types already exist in `backend/app/services/shadow_exporters.py`, but most entity types beyond agent/story/room aren’t yet wired to mutation points.

#### Flow traces (depth)

Flow A — request-path (agent/story):

1. Route writes domain state to DB (e.g., create/update agent/story) and commits.
2. Route builds a snapshot from DB (e.g., `build_agent_snapshot(...)`).
3. Route calls `shadow_service.create_entity_version(...)`:
   - `ensure_shadow_repo(...)` may create the Forgejo repo (network IO).
   - `create_version(...)` reads file SHA then updates/creates `{entity_type}.json` (network IO).
   - A `ShadowVersion` row is written even on Forgejo failure, with `commit_sha` set to `error-<status>` (and `snapshot_json` stored in DB).

Flow B — “background task” (room binding changes):

1. Route updates bindings transactionally, then returns response.
2. FastAPI BackgroundTasks runs `shadow_room_version_best_effort(...)` after the response:
   - Re-opens a new DB session, rebuilds the room snapshot, then executes the same Forgejo repo+commit path as Flow A.

#### Scope multipliers / why outbox+worker is non-trivial

When we move to an outbox/job queue, we need to make explicit decisions (and update code accordingly) for:

- Transaction boundaries (durability):
  - “DB mutation succeeds but enqueue fails” must not silently drop Shadow writes.
  - The enqueue should happen in the *same* DB transaction as the domain mutation (classic outbox pattern).
- Snapshot consistency:
  - Do we enqueue the full `snapshot_json` (stable, but increases payload size), or enqueue a “recompute snapshot from DB” instruction (risk: DB state changes before worker runs)?
- Provenance state machine:
  - Today `ShadowVersion` is written at the same time we attempt the Forgejo commit, and the model is described as immutable.
  - With async commits, we need a representation for “version exists in DB but Forgejo commit pending/failed/retried”.
- Idempotency:
  - Retrying must not create duplicate versions or out-of-order version numbers.
  - We likely need a stable idempotency key per version attempt (e.g., `(shadow_repo_id, version_number)`), and/or a unique constraint on the outbox row.
- Concurrency + file SHA conflicts:
  - Multiple pending writes to the same repo will contend on `{entity_type}.json` updates.
  - Worker should serialize per repo (lock/lease) or implement robust refetch+retry on SHA conflicts.
- Operational concerns:
  - retries/backoff + dead-lettering
  - metrics/logs with correlation from request → outbox → worker attempt
  - a repair/reconciliation loop that can detect “DB says version N exists but Forgejo commit missing” and replay safely

#### Change impact matrix (what will actually change)

| Area | Current behavior | What changes with outbox+worker | Notes / risk |
|---|---|---|---|
| Request handlers | Often do Forgejo IO inline (agent/story) | Only enqueue; no Forgejo calls | Requires refactor so enqueue is durable |
| `shadow_tasks.py` | BackgroundTasks run in web process | Either removed or becomes “enqueue only” | BackgroundTasks is not a job queue |
| DB schema | `ShadowRepo`, `ShadowVersion` only | Add outbox + attempt/lease state | Decide how to represent pending/failed commits |
| `ShadowVersion` semantics | Written immediately; `commit_sha` can be `error-*` | Either (a) create “pending version” then finalize, or (b) create version only after worker success | Model currently describes versions as immutable |
| Snapshot source | Snapshot built in request, stored in DB | Store snapshot in outbox or recompute in worker | Recompute risks race with later edits |
| Idempotency | “Best effort”; duplicates possible under retries | Must be strict; retries safe | Needs stable keys + uniqueness constraints |
| Concurrency | Multiple requests can contend; no explicit locks | Worker must serialize per repo or handle conflicts | File SHA conflict retry loops |
| Ops/observability | Logs only; no job visibility | Job monitoring + DLQ + metrics | Needed to debug missing commits |

#### Breadth-first review checklist (before we write Milestone 3 spec)

1. Enumerate every call site of `shadow_service.create_entity_version*` (done above) and decide which become “enqueue only”.
2. Decide the “pending version” representation (new tables vs updating `ShadowVersion`).
3. Decide whether the outbox payload is “full snapshot_json” vs “recompute snapshot from DB”.
4. Decide worker model (simple polling loop, RQ/Celery, Temporal, etc.) and deployment topology (same container vs separate).
5. Write the failure modes explicitly (“DB ok, Forgejo down”, “worker crash mid-commit”, “duplicate enqueue”) and how each is repaired.

**2) Relationship materialization**

- Implement a per-user ShadowUser “reference index” repo:
  - links to room/story/persona/agent/model repos
  - pins commit SHAs used in specific rooms/at specific times (derived from bindings + versions)
- Implement fork/clone tracking using `ShadowRepo.forked_from_id` + snapshot links.

**3) Backfill + reconciliation**

- Backfill shadow repos for existing Rooms, Personas, Agents, Models, Stories.
- Add a repair job to detect missing repos/commits and replay exports idempotently.

## “Definition of done” checkpoint requirements

Milestone 1 is done when:

- You can set a participant’s active persona + runtime model/provider in a room and query it back reliably.
- A binding change results in a new **room** Shadow version (room snapshot includes active bindings).
- Story graph edits (nodes/choices) result in a new **story** Shadow version that contains the whole story graph.
- Provider snapshots never contain secrets.

- typer and typer-forge have both been completely extended with coverage from both sides.  this is non-negotiable.

- documentation is complete, synthesized, and holistic.

Milestone 2 is done when:

- `build_room_context(..., agent_slug=...)` reliably includes Shadow-derived context items for the current room and agent.
- A2A tool calls include the correct agent-scoped Shadow context (not the caller’s).


Milestone 3 is done when:

- Forgejo commits happen via background worker, not in the request path, and retries are idempotent.
- ShadowUser reference index is populated and can be used as a fast “what SHAs should I load for this room/user” lookup.

---

## Appendix: conversation notes (verbatim reference)

Milestone 1 — Write-path Shadow coverage (Rooms, Personas, Agents, Models, Story)

Create exporters (snapshot builders) per entity
story: Story + StoryNodes + NodeChoices + StoryStateVariables (+ requirements if you use them) from stories.py, storynodes.py, node_choices.py.
room: Room metadata + participants (+ linked story_id/current_version/published_version if present), excluding messages initially (rooms.py).
agent: AgentConfig (and any derived fields you need for reproducibility) (agent_routes.py).
persona: Persona + qualities + any quality states; include event-driven changes (personas.py, persona_qualities.py, persona_events.py, plus user_personas.py if “persona selection per user” matters).
model: cover both (a) catalog “custom models” and (b) user provider configs:
llm_model: created via POST /llm-catalog/models/custom (llm_catalog.py).
user_llm_provider: create/update/delete/test (llm_providers.py) with secrets redacted (never shadow plaintext keys).
Add ShadowService entity types + config
Extend SERVICE_ACCOUNT_MAP/SERVICE_ACCOUNT_USERNAMES and env settings for the new types (e.g., SHADOW_ROOMS_TOKEN, SHADOW_PERSONAS_TOKEN, SHADOW_MODELS_TOKEN, SHADOW_USER_LLM_PROVIDERS_TOKEN) (shadow_service.py, config.py).
Wire versioning to the real mutation points
Story: add shadow commits on POST /stories/{id}/new-version and on content edits (StoryNode/NodeChoice create/update/delete) by exporting the whole story snapshot each time.
Room: shadow on create/update room + add/remove participant (optional: pin/unpin/context updates if they affect agent behavior).
Persona: shadow on persona CRUD + add/remove quality + process event; also shadow user persona CRUD if it’s part of gameplay/agent context.
Agents: shadow already on create/update; add a “tombstone snapshot” on delete.
Models: shadow on custom model creation; shadow user provider config create/update/delete (and optionally “test result” updates as separate event/snapshot type).
Make versioning safe
Add idempotency (avoid double-versions on retry) and handle concurrent writes to the same Forgejo file (SHA mismatch retries).
Milestone 2 — Read-path + Context Provider integration (“Shadow as a context source”)

Implement Shadow read APIs
Fetch latest snapshot from Forgejo per (entity_type, entity_id).
Fetch pinned snapshot by commit SHA / version_number using ShadowVersion.
Add a “summary view” formatter (prompt-friendly) for each entity type.
Define the context items you want agents to see
Room-wide context items (source=shadow): shadow.room.snapshot, shadow.story.snapshot, shadow.persona.snapshot (if room has an active persona), shadow.model.snapshot (if room uses a specific model).
Agent-scoped context items: shadow.agent.snapshot for the current agent; shadow.user_llm_provider.snapshot for the invoking user (redacted).
Hook into existing context pipeline
Emit these as ContextItems into the existing store (context_store.py) so build_room_context includes them (context_provider.py).
Ensure A2A tool calls pass agent_slug into build_room_context so agent-scoped shadow contexts show up in A2A responses too (agent_tools.py).
Caching + fallback
Cache Forgejo reads by (repo, sha) in Redis; fall back to DB ShadowVersion.snapshot_json when Forgejo is down and mark payload as stale.
Milestone 3 — Provenance + relationships + async worker (close the loop with shadow-overview)

Asyncify Forgejo IO
Replace direct Forgejo calls with an outbox/job + worker that does: ensure repo → commit → record SHA → retry/backoff.
Relationship materialization
Maintain a per-user “reference index” (ShadowUser repo) that links to: room/story/persona/agent/model repos + pinned SHAs used in that room/session (your context provider can read this index first).
Implement fork/clone tracking (use ShadowRepo.forked_from_id + store “forked_from_commit_sha” in snapshot links).
Backfill + reconciliation
Backfill shadow repos from existing DB records for the five entity types.
Add a repair job that detects missing repos/commits and replays exports.


If you confirm how you want “active persona” and “active model/provider” to be associated (room-level fields vs user-level defaults vs agent-level settings), I’ll turn Milestone 1 into an exact endpoint-by-endpoint wiring list with commit messages + snapshot file layouts per entity.

those are both many-to-many associations, aren't they?

User ↔ Persona is already many-to-many in your backend: user_personas is the join layer (user_personas.py), and Persona ↔ Quality is also many-to-many via PersonaQualityLink (persona_qualities.py).

“Active persona” and “active model/provider” can be modeled as many-to-many too, but it depends what you mean by “active”:

If “active” means “a room can select one persona (and one model) at a time”, that’s typically one-to-many (many rooms → one active persona/model each) with optional history (a separate table recording changes over time).
If “active” means “a room can have multiple personas/models concurrently (or a set of enabled options)”, then it’s many-to-many (room ↔ persona, room ↔ model), usually with a join table that can include metadata like is_active, pinned_sha, activated_at, agent_slug, etc.
Tell me which “active” behavior you want (single selection vs a set), and I’ll recommend the cleanest schema + where to hang Shadow refs.

a user or an agent can have a persona (agents will have an agent_persona join table) and a room can have multiple personas (users or agents) and each of those agents might be using a different model and provider at that time.  Is that logically coherent?

Yes—logically coherent. The clean way to think about it is: persona and model/provider are attributes of a “participant in a room (at a point in time)”, not global properties of the room.

A coherent shape is:

User ↔ Persona (many-to-many) via user_personas (you already have this).
Agent ↔ Persona (many-to-many) via your planned agent_personas.
Room has many participants (already via RoomParticipant), and each participant can have:
an active persona selection (picked from their user/agent personas), and
an active runtime config (model + provider), which can differ per participant and can change over time.
If you want history/audit/provenance (which Shadow implies), represent “at that time” explicitly:

a RoomParticipantState / RoomParticipantSession / RoomRuntimeBinding table keyed by (room_id, participant_id, participant_type) with fields like persona_id, provider_id, model_id, effective_at, ended_at (or event-sourced changes).
That makes “room has multiple personas” true in aggregate (across its participants), while still keeping persona/model selection correctly scoped to who is speaking/acting.

Two quick clarifiers that affect the schema:

Can a single participant have multiple active personas at once in a room, or exactly one?
Are models/providers user-owned configs (e.g., UserLLMProvider) that agents can borrow, or do agents have their own provider configs too?
a participant will only have one active persona in a room at a time.  agents have configs, and when an agent object is cloned from user A to user B, user B will need to specify that agent's config.  an agent that is modified to have a different config (ie, use a different provider/model combination) is a direct use case, and the agent maintains it's uuid and slug through that transition.

Yes—this is coherent, and it suggests a clear separation of concerns:

Participant persona (room-scoped, single active):

Model this as a room-participant “binding” with exactly one active row at a time, e.g. RoomParticipantPersona(room_id, participant_type, participant_id, persona_id, effective_at, ended_at=NULL).
Enforce “only one active persona” with a uniqueness rule on (room_id, participant_type, participant_id) where ended_at IS NULL.
Agent identity vs agent config (stable UUID/slug across config changes):

Treat the Agent (uuid/slug) as the stable identity.
Treat AgentConfig as mutable state or better: versioned configs where the agent points to the current config version.
Your requirement (“agent maintains uuid and slug through transition”) maps cleanly to: keep the same Agent row, just update its current_config_id (or create a new config version and repoint).
Provider/model changes are config changes, not identity changes:

Provider/model selection belongs in the agent’s active config (or config version): provider_id, model_id, plus any non-secret knobs.
Cloning an agent from user A → user B:

If user B must “specify that agent’s config”, the clone should copy the shape of the config but not carry over user A’s credentials.

Practically: the cloned agent owned by user B references user B’s UserLLMProvider (or equivalent) and chosen model; until set, the agent is incomplete/disabled.
Shadow-wise: create a new agent repo for the cloned agent and record forked_from_id/source commit to preserve provenance.
If you want, I can propose the minimal table set + constraints for agent_personas and the room participant binding, aligned with your existing RoomParticipant and UserLLMProvider patterns.
