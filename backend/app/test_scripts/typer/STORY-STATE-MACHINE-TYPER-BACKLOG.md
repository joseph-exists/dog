# Story State Machine Typer Backlog

Purpose: prioritized implementation backlog to close the gap between current Typer coverage and full story state-machine authoring/runtime workflows.

Scope: `backend/app/test_scripts/typer/commands/stories.py` (primary), plus optional `rooms.py`/new `story_progress.py` if runtime commands are split.

Guide Basis: follows conventions in `backend/app/test_scripts/typer/AGENT.md` (Annotated args/options, `--json`, `--verbose`, consistent exit codes, auth via `get_authenticated_session()`).

## Current Gap Summary
- Existing `stories` commands cover create/list/get/publish, add node/choice, state schema CRUD+validate, story validate/tree.
- Missing parity for story lifecycle, node/choice full CRUD, and runtime progression APIs.

## Priority Model
- `P0`: unblock full authoring of versioned state-machine graphs.
- `P1`: complete lifecycle/maintenance parity.
- `P2`: runtime execution/testing parity for end-to-end verification.

## P0 (IN REVIEW)
1. Upgrade `stories add-node`
- Add options: `--version`, `--node-type`, `--content-format`.
- Remove hardcoded `story_version=1`, `node_type="text"`, `content_format="text"`.
- API: `POST /api/v1/storynodes/`
- Acceptance:
  - Can create node in non-v1 story.
  - Can set custom `node_type`.
  - `--json` prints API response.
- Status: Done (implemented in `stories.py`).
- Placeholder or deferred functionality: None.

2. Upgrade `stories add-choice`
- Add options: `--requires-state`, `--sets-state` (JSON object strings), optional `--json`.
- API: `POST /api/v1/node-choices/` (and keep support for `POST /storynodes/{node_id}/choices` if desired).
- Acceptance:
  - Guards/effects round-trip in response.
  - Invalid JSON fails with clear error and exit code 1.
- Status: Done (implemented in `stories.py`).
- Placeholder or deferred functionality: None.

3. Add node inspection/edit commands
- `stories list-nodes <story_id> [--version] [--json]`
- `stories get-node <node_id> [--json]`
- `stories update-node <node_id> [--title --content --node-type --start/--no-start --end/--no-end --json]`
- `stories delete-node <node_id> [--force]`
- APIs: `GET/PUT/DELETE /api/v1/storynodes/{id}`, `GET /api/v1/storynodes/`
- Acceptance:
  - Can fully inspect and mutate graph nodes from CLI.
  - Delete supports confirm prompt + `--force`.
- Status: Done (implemented in `stories.py`).
- Placeholder or deferred functionality: None.

4. Add choice inspection/edit commands
- `stories list-choices [--story-id | --node-id] [--json]`
- `stories get-choice <choice_id> [--json]`
- `stories update-choice <choice_id> [--text --order --to-node-id --requires-state --sets-state --json]`
- `stories delete-choice <choice_id> [--force]`
- APIs: `GET/PUT/DELETE /api/v1/node-choices/{choice_id}`, `GET /api/v1/node-choices/`, `GET /api/v1/storynodes/{node_id}/choices`
- Acceptance:
  - Can refactor transitions without leaving Typer.
  - Filters work for node-focused editing.
- Status: Done (implemented in `stories.py`).
- Placeholder or deferred functionality: None.


5. Add `stories start-node`
- `stories start-node <story_id> [--version] [--json]`
- API: `GET /api/v1/stories/{id}/start-node`
- Acceptance:
  - Returns canonical start node quickly for tooling and tests.
- Status: Done (implemented in `stories.py`).
- Placeholder or deferred functionality: None.


## P1 (Lifecycle/Publishing Parity)
1. Add story lifecycle commands
- `stories update <story_id> [--title --desc --story-type --presentation --json]`
- `stories delete <story_id> [--force]`
- `stories unpublish <story_id>`
- `stories new-version <story_id> [--json]`
- APIs: `PUT/DELETE /api/v1/stories/{id}`, `PUT /api/v1/stories/{id}/unpublish`, `POST /api/v1/stories/{id}/new-version`
- Acceptance:
  - Draft/publish/version loop can be done entirely from Typer.
- Status: Done (implemented in `stories.py`).
- Placeholder or deferred functionality: `story_type` and `presentation` not supported by API schema.

2. Add requirements commands
- `stories list-requirements <story_id> [--json]`
- `stories add-requirement <story_id> ...`
- `stories delete-requirement <story_id> <requirement_id> [--force]`
- APIs: `GET/POST/DELETE /api/v1/stories/{story_id}/requirements...`
- Acceptance:
  - Story-level gating requirements manageable from CLI.
- Status: Done (implemented in `stories.py`).
- Placeholder or deferred functionality: None.

## P2 (Runtime State-Machine Verification)
1. Add story progress commands (in `stories` or new `story-progress` group)
- `create-progress`, `get-progress`, `list-progress`
- `current-node`, `make-choice`, `undo`, `jump`
- `validate-state`, `timeline`, `snapshots`, `create-snapshot`
- APIs: `/api/v1/user-personas/{user_persona_id}/stories/{story_id}/...`
- Acceptance:
  - Engineer can run complete playthrough tests via CLI.
  - `jump` supports optimistic concurrency fields when required.
- Status: Done (implemented in `stories.py`).
- Placeholder or deferred functionality: None.

2. Optional room-runtime parity
- Add room runtime wrappers if needed by your workflow:
  - `runtime get|put|advance|rewind|reset`
- API: `/api/v1/rooms/{room_id}/runtime...`
- Status: Done (implemented in `rooms.py`).
- Placeholder or deferred functionality: None.

## Recommended Implementation Slices (Rapid Iteration)
1. PR-1 (`P0-A`): `add-node` + `add-choice` upgrades only.
2. PR-2 (`P0-B`): node CRUD/list commands.
3. PR-3 (`P0-C`): choice CRUD/list commands + `start-node`.
4. PR-4 (`P1-A`): story lifecycle (`update/delete/unpublish/new-version`).
5. PR-5 (`P1-B`): requirements commands.
6. PR-6 (`P2`): progress/runtime commands.

Each PR should include:
- Command help verification:
  - `python main.py stories --help`
  - `python main.py stories <new-command> --help`
- At least one successful JSON-mode run (`--json`) for read/list commands.
- One failure-path check confirming non-zero exit.

## Command Design Rules (Enforced)
- Use `Annotated` and explicit help text on every arg/option.
- Keep debug logs behind `--verbose`.
- Use `typer.secho(..., fg=GREEN)` for success and `fg=RED, err=True` for failures.
- Return non-zero on failure (`raise typer.Exit(1)`).
- Parse JSON inputs safely (`requires_state`, `sets_state`, `presentation`) with clear validation errors.

## Documentation Updates Required Per Milestone
1. Update `backend/app/test_scripts/typer/COMMANDS.md` with exact syntax/options.
2. Update `backend/app/test_scripts/typer/TYPER-README.md` with real examples.
3. Update `backend/app/test_scripts/typer/REFERENCE.md` only for reusable patterns introduced.

## Fast Acceptance Scenario (Full Authoring, Post-P0)
1. Create story.
2. Add state vars.
3. Add nodes with explicit version + node types.
4. Add guarded choices with state mutations.
5. Validate schema + graph.
6. Confirm start node.

If all pass from Typer only, P0 is complete.
