# Repo And Bootstrap Contract Draft

## Purpose

This artifact defines how repository source, bootstrap behavior, install/start intent, and workspace readiness should fit together for the next milestone.

It is meant to answer four concrete questions:

- how `user_repos` and `shadow_repos` should be referenced by a workspace
- which layer owns clone/install/start orchestration
- what bootstrap progress and failure should look like in the contract
- what `ready` should mean for a repo-backed workspace

This draft is grounded in:

- [user_repos.py](/home/josep/dog/backend/app/api/routes/user_repos.py)
- [shadow_repos.py](/home/josep/dog/backend/app/api/routes/shadow_repos.py)
- [user-repo-frontend-reference.md](/home/josep/dog/backend/app/services/service-docs/user-repo-frontend-reference.md)
- [00-base.sh](/home/josep/dog/kennel/provision/00-base.sh)
- [01-dev.sh](/home/josep/dog/kennel/provision/01-dev.sh)
- [example-spawn-injection.md](/home/josep/dog/kennel/example-spawn-injection.md)
- [workspace_service.py](/home/josep/dog/backend/app/services/workspace_service.py)

## Current State

Today, workspace creation accepts:

- `repo_url`
- `ssh_pubkey`
- `env_vars`

That is enough for a thin spawn-and-terminal slice, but not enough for the next milestone.

Current problems:

- repo source is too raw and under-modeled
- bootstrap intent is implicit rather than declarative
- clone/install/start concerns are mixed together
- workspace readiness currently means roughly “kennel is up and injection finished,” which is not strong enough for agent/service workflows

This section is now historically useful, but incomplete as a current-state reference.

The current public backend create surface now also supports:

- top-level `runtime_preset`
- nested `bootstrap.bootstrap_profile`
- nested `bootstrap.runtime_files`

And the current backend seam now supports mixed-mode requests where:

- backend may still provide explicit bootstrap execution intent
- kennel may still provide runtime preset and profile-owned defaults
- env vars and runtime files are merged through the normalized backend-to-kennel seam

## Current Implementation Snapshot

The first Track 2 implementation slices have now made the contract partially real:

- backend workspace create/detail models now include typed bootstrap intent and progress
- backend normalization now accepts:
  - legacy `repo_url`
  - typed `external_url`
  - typed `user_repo`
- backend validation currently:
  - validates external repo references conservatively
  - validates `user_repo` existence, ownership, and ready/imported state
  - returns structured API errors for invalid bootstrap input

Important current bridge:

- `user_repo` bootstrap currently materializes through `UserRepo.source_repo_url`

This is a practical bridge, not the final design. It keeps the slice moving while preserving a clean place to swap in platform-native repo materialization later.

Still intentionally deferred:

- executable `shadow_repo` bootstrap
- a richer runtime/service readiness model tied to declared endpoints

The next implementation slice has now pushed the contract one step further:

- backend now generates a structured bootstrap plan before kennel injection
- that generated plan is persisted in workspace metadata for inspection and later extension
- kennel now executes explicit plan steps and returns structured step results

Current plan support is intentionally compact:

- step types:
  - `add_ssh_key`
  - `write_env_vars`
  - `clone_repo`
  - `run_command`
- install profiles:
  - `npm`
  - `pnpm`
  - `yarn`
  - `uv`
  - `pip`
- startup profiles:
  - `vite`
  - `nextjs`
  - `fastapi`

These registries should be read as extension points, not closed sets. The point of this slice is to make backend intent explicit and kennel execution legible without pretending the runtime vocabulary is final.

## Current Integration Understanding

The useful current understanding is not that one layer must replace the other.

The important concern is that backend and kennel interfaces must remain connected and ordered consistently.

Today that means:

- the frontend declares intent
- backend validates and normalizes that intent
- backend may send explicit bootstrap instructions to kennel
- backend may also send `runtime_preset` and `bootstrap_profile` so kennel can apply preset-owned defaults
- kennel executes provision/bootstrap steps inside the workspace
- backend records progress and exposes state back to the frontend

The frontend should not compose shell commands as business logic.

The kennel layer should not have to infer platform semantics from a loose `meta` blob.

The current goal is to preserve both:

- backend-defined and backend-overridden environments
- kennel-local runtime preset expansion

without forcing either into the role of the single source of truth for all cases.

## Current Precedence Direction

Create-time direction:

1. internal or operator create-time infrastructure overrides when present
2. explicit `flavour`
3. `runtime_preset` default flavour behavior
4. service default fallback

Inject-time direction:

1. internal explicit bootstrap plan when present
2. explicit `bootstrap.bootstrap_profile`
3. `runtime_preset` default profile behavior
4. legacy inject derivation and fallback behavior

Merge direction:

- env vars should remain additive with the most local explicit caller value winning
- runtime files should remain additive with explicit caller entries able to override preset-owned entries

These directions matter more than defending one runtime interpretation as universally correct.

## Kennel Validation Note

[validate_provisioning.py](/home/josep/dog/kennel/scripts/validate_provisioning.py) is currently passing for the kennel-owned Codex preset path.

That matters for frontend work because it gives us a clearly healthy default path to prioritize:

- `runtime_preset: "codex"` on create
- `runtime_preset: "codex"` on inject
- service discovery expecting a healthy `codex` websocket service on port `4500`

The current frontend create slice now begins from a preset-first happy path, while still preserving broader override paths through the bootstrap surface.

## Repo Source Model

### Supported Source Types

The workspace contract should support exactly three near-term repo source types:

- `external_url`
- `user_repo`
- `shadow_repo`

### Meaning Of Each Source Type

`external_url`

- used when the workspace should clone directly from an external repository URL
- appropriate for quick import-style provisioning
- backend validates the URL before bootstrap begins

`user_repo`

- used when the workspace should bootstrap from a platform-managed user repo
- source of truth is the platform repo object, not an arbitrary forge URL
- backend resolves the actual clone/access mechanism

`shadow_repo`

- used when the workspace should bootstrap from a shadow repo attached to another platform entity
- backend resolves by `entity_type` and `entity_id`, then derives the shadow repo backing store
- frontend should not have to know the underlying shadow repo layout

### Proposed Bootstrap Source Shape

Near-term canonical shape:

```ts
type WorkspaceRepoSource =
  | {
      type: "external_url"
      repo_url: string
      ref?: string | null
    }
  | {
      type: "user_repo"
      repo_id: string
      ref?: string | null
    }
  | {
      type: "shadow_repo"
      entity_type: string
      entity_id: string
      ref?: string | null
    }
```

Notes:

- `ref` should be optional and likely default to platform conventions such as `main`
- if branch/ref selection is not supported yet for a source type, backend should ignore or reject it explicitly

## Bootstrap Intent Model

Repo source is only one part of bootstrap. We also need to express what should happen after source material becomes available inside the workspace.

### Recommended Intent Layers

1. `base_image`
   Chosen through existing `flavour` and `kind`

2. `repo_materialization`
   How code gets into the workspace

3. `install_intent`
   What dependency/bootstrap step should run

4. `startup_intent`
   What long-running services or agents should start

5. `readiness_contract`
   What conditions must be satisfied before the workspace is considered `ready`

### Proposed Bootstrap Intent Shape

```ts
interface WorkspaceBootstrapIntent {
  repo_source: WorkspaceRepoSource | null

  workspace_path?: string | null

  install_intent:
    | { mode: "none" }
    | { mode: "auto" }
    | { mode: "profile"; profile: string }
    | { mode: "command"; command: string }

  startup_intent:
    | { mode: "terminal_only" }
    | { mode: "profile"; profile: string }
    | { mode: "command"; command: string }
    | { mode: "agent_service"; agent_profile: string }

  env_vars?: Record<string, string>
  ssh_pubkey?: string | null
}
```

## Install Intent

### Recommended Modes

`none`

- create the workspace and materialize repo content if present
- do not run package installation automatically

`auto`

- backend/kennel chooses a safe default based on repo content and workspace flavour
- examples:
  - `uv sync` or `pip install -r requirements.txt` for Python
  - `npm install` or `pnpm install` for Node

`profile`

- backend-controlled named behavior
- examples:
  - `python-dev`
  - `node-dev`
  - `codex-runtime`

`command`

- explicit command string
- powerful but riskier
- should likely be feature-gated or restricted to trusted operators in the near term

### Recommendation

Near term:

- support `none`
- support `auto`
- support backend-defined `profile`
- defer arbitrary `command` until access and audit semantics are clearer

Current implementation note:

- `profile` is now real in the first slice through a small backend-owned registry
- additional profiles should be added by extending the backend plan generator rather than widening the frontend contract

This keeps the system flexible without turning workspace creation into remote shell-as-API.

## Startup Intent

### Recommended Modes

`terminal_only`

- no long-running service is started automatically
- workspace becomes a managed interactive environment

`profile`

- backend-defined runtime profile starts known services
- examples:
  - `jupyter`
  - `dev-server`
  - `agent-runtime`

`command`

- explicit startup command
- same caution as install `command`

`agent_service`

- named agent runtime should be installed or started as part of bootstrap
- examples:
  - `codex`
  - `claude-code`
  - `hermes-agent`

### Recommendation

Near term:

- support `terminal_only`
- support backend-defined `profile`
- support `agent_service` if mapped to backend-controlled profiles
- defer arbitrary `command`

Current implementation note:

- `terminal_only` is supported
- `profile` is supported for a small initial registry: `vite`, `nextjs`, `fastapi`
- `agent_service` is now supported through a backend-owned first profile set:
  - `codex`
  - `claude_code`
  - `hermes`
- the current launcher commands are intentionally compact and overrideable while the runtime/discovery semantics are clarified in the next slice

## Ownership Boundaries

### Frontend owns

- collecting user intent
- selecting source type
- selecting install/start profile from backend-supported options
- presenting bootstrap progress and failure clearly

### Backend owns

- validating repo source references
- authorizing access to `user_repo` and `shadow_repo` sources
- resolving source references into actual bootstrap instructions
- deciding which install/start profiles are valid
- translating intent into kennel execution steps
- recording progress, failures, and resulting readiness

### Kennel owns

- executing the normalized bootstrap plan inside the workspace
- performing clone/materialization/install/start actions
- returning execution results and failure details to backend

## Suggested Execution Model

The backend should construct a normalized bootstrap plan before calling kennel.

Recommended internal shape:

```ts
interface ResolvedWorkspaceBootstrapPlan {
  workspace_id: string
  workspace_path: string

  repo_materialization:
    | { mode: "none" }
    | { mode: "git_clone"; source_url: string; ref?: string | null }
    | { mode: "repo_export"; source_type: "user_repo" | "shadow_repo"; source_id: string }

  install_steps: Array<{ id: string; command: string }>
  startup_steps: Array<{ id: string; command: string; background?: boolean }>

  readiness_checks: Array<
    | { type: "path_exists"; path: string }
    | { type: "command_success"; command: string }
    | { type: "port_open"; port: number }
    | { type: "process_running"; pattern: string }
  >
}
```

This plan should be backend-generated, not frontend-provided.

Current implementation note:

- the current plan is linear rather than graph-shaped
- kennel executes the plan in-order and returns structured `step_results`
- this keeps the slice easy to understand and revise while future runtime/service work is still taking shape

## How `user_repos` Should Fit

`user_repo` should be treated as a platform resource, not as a convenience alias for `repo_url`.

Recommended behavior:

- workspace create references `repo_source.type = "user_repo"` and `repo_id`
- backend verifies repo visibility and readiness
- backend resolves the source into a backend-supported materialization path
- kennel receives a resolved clone/export instruction, not raw permission logic

Important rule:

- if a `user_repo` is still importing, workspace bootstrap should not proceed as if the repo were ready

Recommended response:

- either reject workspace creation with a clear `409`-style repo-not-ready error
- or allow workspace creation but keep workspace in `requested` / `provisioning` until repo readiness resolves

Recommendation:

- reject early in the first pass

Reason:

- it keeps workspace readiness semantics simpler
- it avoids tying workspace lifecycle to a second asynchronous import queue immediately

## How `shadow_repos` Should Fit

`shadow_repo` should also be treated as a platform resource, but with more caution.

Recommended behavior:

- workspace create references `repo_source.type = "shadow_repo"`
- frontend identifies the related entity, not the storage implementation
- backend resolves the shadow repo from entity identity

Important distinction:

- shadow repos are better suited for read-oriented bootstrap or contextual code surfaces than for arbitrary writeback semantics

Recommendation:

- allow shadow repo bootstrap for code/context materialization
- do not assume writeback or git-authoring semantics in the first pass

## Bootstrap Progress Model

Bootstrap needs more granularity than a single workspace `status`.

Do not explode the top-level workspace status enum to represent every substep.

Instead, add a structured bootstrap progress field.

Recommended shape:

```ts
interface WorkspaceBootstrapProgress {
  phase:
    | "pending"
    | "resolving_source"
    | "materializing_repo"
    | "installing_dependencies"
    | "starting_services"
    | "running_readiness_checks"
    | "complete"
    | "failed"

  message: string | null
  step_count: number | null
  completed_steps: number | null
  failure_message: string | null
}
```

This can live on `WorkspacePublic.bootstrap` or in a dedicated detail field.

## Workspace Readiness Decision

This is the central question.

### Recommendation

For repo-backed workspaces, `ready` should mean:

- repo materialization is complete
- declared install intent is complete
- declared startup intent has run
- declared readiness checks have passed
- terminal access is available

In other words:

- `ready` should mean operationally usable for its requested purpose
- not merely “container exists”

### Why

If `ready` only means terminal-ready:

- the user and agents still have to guess whether repo/bootstrap completed
- service-oriented workspaces become misleading
- failures in install/start collapse into post-ready confusion

### Counterweight

Do not require every possible service to be healthy forever before `ready`.

Instead:

- `ready` means initial declared readiness checks passed
- ongoing runtime health belongs in service discovery / runtime monitoring, not the top-level status enum

## Proposed API Deltas

### `POST /api/v1/workspaces/`

Current request is too thin.

Recommended request shape:

```ts
interface WorkspaceCreate {
  name: string
  flavour?: string
  kind?: string
  project_id?: string | null
  visibility?: "private" | "project" | "shared"

  bootstrap?: {
    repo_source?: WorkspaceRepoSource | null
    install_intent?: { mode: "none" | "auto" } | { mode: "profile"; profile: string }
    startup_intent?:
      | { mode: "terminal_only" }
      | { mode: "profile"; profile: string }
      | { mode: "agent_service"; agent_profile: string }
    env_vars?: Record<string, string>
    ssh_pubkey?: string | null
  }
}
```

Compatibility note:

- keep accepting legacy top-level `repo_url`, `ssh_pubkey`, and `env_vars` for one transition period
- backend should normalize old input into the new bootstrap shape

### `GET /api/v1/workspaces/{id}`

Recommended additions:

- `bootstrap.intent`
- `bootstrap.progress`
- `bootstrap.result`
- `readiness_summary`

Example response fragment:

```json
{
  "status": "starting",
  "bootstrap": {
    "intent": {
      "repo_source": { "type": "user_repo", "repo_id": "uuid" },
      "install_intent": { "mode": "auto" },
      "startup_intent": { "mode": "agent_service", "agent_profile": "codex" }
    },
    "progress": {
      "phase": "installing_dependencies",
      "message": "Installing Python dependencies",
      "step_count": 4,
      "completed_steps": 2,
      "failure_message": null
    }
  },
  "readiness_summary": {
    "terminal_ready": false,
    "bootstrap_complete": false,
    "services_ready": false
  }
}
```

### Optional supporting endpoint

Consider:

- `GET /api/v1/workspaces/bootstrap-profiles`

Purpose:

- let frontend discover supported install/start profiles
- avoid hardcoding runtime profile names in UI

## Service Layer Changes

Current backend flow in [workspace_service.py](/home/josep/dog/backend/app/services/workspace_service.py) is:

- create workspace
- create kennel env
- inject config
- mark ready

Recommended flow:

1. validate workspace create request
2. resolve repo source and bootstrap profile into a normalized bootstrap plan
3. create workspace record with requested bootstrap intent
4. create kennel env
5. materialize repo
6. run install steps
7. run startup steps
8. run readiness checks
9. mark workspace `ready` only when checks pass
10. mark workspace `failed` with first-class failure summary on error

## Kennel Contract Direction

The kennel integration should move away from “inject loose config and hope the container script handles it” toward “execute a resolved plan.”

That does not require a big rewrite immediately.

Near-term compatible approach:

- backend still calls kennel inject/spawn
- injected payload becomes more structured
- kennel executes explicit steps in order
- each step reports success/failure and an optional message

Current implementation note:

- this is now true for the current first slice
- legacy inject fields are still accepted so the transition remains gentle
- backend now records `bootstrap_plan`, `bootstrap_step_results`, `bootstrap_started_services`, and `bootstrap_workspace_path` in workspace metadata

This fits naturally with the existing base/provision split in:

- [00-base.sh](/home/josep/dog/kennel/provision/00-base.sh)
- [01-dev.sh](/home/josep/dog/kennel/provision/01-dev.sh)

## First-Phase Recommendation

The narrowest useful first implementation of this contract is:

1. add structured `bootstrap` to workspace create/detail
2. support repo sources:
   - `external_url`
   - `user_repo`
   - `shadow_repo`
3. support install intents:
   - `none`
   - `auto`
   - backend-defined `profile`
4. support startup intents:
   - `terminal_only`
   - backend-defined `profile`
   - backend-defined `agent_service`
5. add bootstrap progress reporting
6. define `ready` as bootstrap-complete plus terminal-available
7. reject `user_repo` sources that are not yet `ready`

That is enough to make the next milestone legible without overcommitting to arbitrary remote command execution.

## Open Questions

- Should `shadow_repo` bootstrap support writeback in the near term, or remain strictly read/materialization oriented?
- Should repo materialization use clone, export, or archive extraction for `user_repo` and `shadow_repo` sources?
- Do we want one shared profile registry for install and startup, or two separate registries?
- Should agent-profile startup imply install behavior automatically, or remain independent?
- How much bootstrap output should be persisted as structured logs versus ephemeral debug text?
