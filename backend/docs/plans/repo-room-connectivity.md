**Golden Path**

1. User creates a room.
2. Backend ensures a room shadow repo exists for `entity_type="room"` and `entity_id=room_id`.
3. User adds an agent whose config already enables `read_repo_file` and `write_repo_files`.
4. Agent can create/edit files in the room repo without the user creating or selecting a separate repo.
5. Room repo contains both system snapshots, such as `room.json` and `room_events.redis.json`, and user/agent-created opaque artifacts.
6. Any room artifact viewer, workspace bootstrap, or future runtime mounts read from that same shadow repo.

“room artifact repos are shadow repos, exposed through a room-scoped repo tool facade.” That keeps the shadow repo as the single source of truth and avoids quietly creating a second `UserRepo` just so existing tools work.

**Current Shape**

The useful pieces already exist:

- Room shadow repos are created/versioned through `shadow_service` and committed by [shadow_outbox_worker.py](/home/josep/dog/backend/app/services/shadow_outbox_worker.py:1).

- Shadow repos already support local git materialization via [shadow_git.py](/home/josep/dog/backend/app/services/shadow_git.py:1).

- Repo tools exist, but they are currently `UserRepo`-centric: [agent_tools.py](/home/josep/dog/backend/app/services/agent_tools.py:388).

- Workspace bootstrap already has a `WorkspaceShadowRepoSource` model, but it is deliberately disabled in [workspace_service.py](/home/josep/dog/backend/app/services/workspace_service.py:895).

- Agent tool enablement already supports pre-existing `repo_read` / `repo_write` style tool config in [agent_instance.py](/home/josep/dog/backend/app/services/agent_instance.py:553).



**Plan**

**1. Make room shadow repo creation explicit at room creation**

Today, room shadowing appears to be event/task driven. 

We are adding an explicit best-effort ensure/enqueue step after `create_room` succeeds.

Target:

- [crud.py](/home/josep/dog/backend/app/crud.py:3577)
- [rooms.py](/home/josep/dog/backend/app/api/routes/rooms.py:143)
- existing `shadow_room_version_best_effort` if it already fits

Behavior:

- Ensure `ShadowRepo(entity_type="room", entity_id=room_id)` exists.
- Enqueue initial room snapshot.
- Do not require the outbox worker to finish before returning the room.
- Add a readiness state for tool calls: “repo initializing, retry shortly” if no first commit exists yet.

**2. Introduce a room-scoped artifact repo service**

Add a small service that mirrors the safe parts of `UserRepoService`, but targets `ShadowRepo`.

Suggested file:

- `backend/app/services/room_artifact_repo_service.py`

Responsibilities:

- Resolve `room_id -> ShadowRepo`.
- Authorize access by active `RoomParticipant`.
- Resolve repo path using `shadow_service.get_entity_repo_path("room", room_id)`.
- Use `settings.SHADOW_REPO_URL_TEMPLATE` and `get_repo_remote_url(...)` when a remote exists.
- Read files from the room shadow repo.
- Commit opaque file mutations.

Important: artifact writes should not use `ShadowVersion`, because these are not entity snapshots. They are direct git commits to the same repo.

**3. Add generic shadow git mutation helpers**

`shadow_git.py` has `commit_snapshot(...)` and `commit_text_file(...)`, but opaque artifact editing needs multi-file mutations and deletes.

Add helpers like:

- `get_head_sha(repo_path, remote_url=None, default_branch="main")`
- `read_file_at_ref(repo_path, path, ref)`
- `commit_file_mutations(repo_path, mutations, message, expected_head_sha, author, remote_url, default_branch)`

Rules:

- Reject paths escaping repo root.
- Reserve system-owned paths:
  - `room.json`
  - `room_events.redis.json`
  - maybe `.dog/` depending on future metadata needs
- Support `upsert` and `delete`.
- Preserve optimistic concurrency with `expected_head_sha`.
- Pull/fetch before reading and writing when remote configured.
- Push after commit when remote configured.

**4. Extend repo tools without breaking existing `UserRepo` flow**

Keep the public tool names stable so pre-existing agents still work:

- `read_repo_file(...)`
- `write_repo_files(...)`

But allow one of these approaches:

Preferred MVP:

- If `repo_id` is omitted or set to `"room"`, resolve the current room repo from `ctx.deps.room_id`.
- Existing calls with UUID `repo_id` continue to use `UserRepo`.

Example agent call:

```json
{
  "path": "notes/brief.md"
}
```

or:

```json
{
  "repo_id": "room",
  "path": "notes/brief.md"
}
```

This gives the “skip repo creation” golden path without making agents know the room UUID.

**5. Return the same write hint shape**

The current read tool returns `write_hint.branch` and `write_hint.expected_head_sha`. Keep that shape for room artifact repos.

For room repos:

```json
{
  "repo_id": "room",
  "repo_kind": "room_shadow_repo",
  "room_id": "...",
  "path": "notes/brief.md",
  "content": "...",
  "write_hint": {
    "branch": "main",
    "expected_head_sha": "..."
  }
}
```

That preserves the existing read-then-write agent behavior.

**6. Handle shadow worker concurrency deliberately**

The shadow outbox worker and room artifact writes will both commit to the same repo. That is fine, but they need a shared git-level lock or retry strategy.

Minimum MVP:

- Before commit, verify `HEAD == expected_head_sha`.
- If not, return conflict and ask agent to re-read.
- Ensure both worker commits and artifact commits use `ensure_repo(...)`, fetch, and push consistently.

Better follow-up:

- Reuse or implement a per-`ShadowRepo` lease around all git writes, not just outbox jobs.
- Artifact writes and shadow snapshot commits serialize per room repo.

**7. Enable workspace bootstrap from room shadow repo**

`WorkspaceShadowRepoSource` already exists but currently errors in [workspace_service.py](/home/josep/dog/backend/app/services/workspace_service.py:895).

Enable it for room repos:

- Validate active room membership.
- Resolve `entity_type="room"`, `entity_id=room_id`.
- Materialize clone URL using `SHADOW_REPO_URL_TEMPLATE`.
- If no remote is configured, decide whether kennel can mount/clone local paths. If not, require remote for workspace bootstrap but still allow backend repo tools locally.

This lets future room workspaces boot directly from the room artifact repo.

**8. Add room artifact viewer/API surface**

For UX, either extend existing shadow repo endpoints or add room-specific endpoints:

- `GET /rooms/{room_id}/artifacts/tree`
- `GET /rooms/{room_id}/artifacts/file?path=...`
- maybe `POST /rooms/{room_id}/artifacts/commits` for user-driven edits later

These should wrap shadow repo access with room participant auth, not expose raw shadow repo identity as the main UX concept.

**Testing**

Core tests that need to be added:

- Room creation ensures/enqueues room shadow repo.
- Agent with repo tools can write `README.md` to current room repo without `repo_id`.
- Agent cannot overwrite `room.json` or `room_events.redis.json`.
- Non-participant cannot read/write room artifact repo.
- Existing `UserRepo` read/write tests still pass.
- Conflict test: stale `expected_head_sha` returns retryable conflict.
- Workspace bootstrap accepts `WorkspaceShadowRepoSource(entity_type="room", entity_id=room_id)` once enabled.

**Implementation Order**

1. Add room artifact service and git mutation helpers.
2. Extend `read_repo_file` / `write_repo_files` to support implicit current-room repo.
3. Ensure room shadow repo exists on room creation.
4. Add tests for agent tool golden path.
5. Add room artifact API/viewer endpoints.
6. Enable `WorkspaceShadowRepoSource` for room repos.

The key design choice: do not turn room artifacts into `UserRepo`s. Treat `UserRepo` and room shadow repo as two backends behind the same agent-facing tool contract. That gives users the “just enter a room and create files” flow while keeping the room repo as the single source of truth.