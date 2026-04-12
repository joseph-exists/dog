# Runtime Preset API Reference

This note documents the kennel-side `runtime_preset` API and its ordering relative to explicit create and inject fields.

The goal is not to treat backend presets/profiles and kennel presets/profiles as a redundancy problem. The practical concern is interface coordination: both layers may apply defaults or overrides, and those applications need to compose predictably.

## Purpose

`runtime_preset` is a kennel-facing defaulting mechanism.

It exists so callers can:

- select a compatible runtime-oriented flavour during `POST /envs`,
- select a compatible runtime-oriented bootstrap profile during `POST /envs/{name}/inject`,
- add new preset mappings inside kennel without removing backend control over explicit env construction.

This mechanism is compatible with callers that also want to:

- define envs explicitly on the backend,
- override flavour or bootstrap behavior case by case,
- send fully explicit bootstrap plans.

## Supported Presets

Today kennel defines:

- `codex`
- `claude_code`
- `hermes`

Current mapping:

- `codex` -> create flavour `dev-codex`, inject bootstrap profile `codex_app_server`
- `claude_code` -> create flavour `dev-claude-code`, inject bootstrap profile `claude_code_remote_control`
- `hermes` -> create flavour `hermes-agent`, inject bootstrap profile `hermes_agent_runtime`

References:

- [kennel/src/server.py](/home/josep/dog/kennel/src/server.py#L294)
- [kennel/src/flavours.py](/home/josep/dog/kennel/src/flavours.py#L14)

## Create Request Semantics

Kennel create accepts:

```json
{
  "kind": "ephemeral",
  "flavour": "dev",
  "runtime_preset": "codex",
  "base_container": null
}
```

### Create Ordering

Kennel applies create-time preset defaults before resolving the base container, but only as a default.

Effective precedence:

1. Explicit `base_container` or `base_snapshot`
2. Explicit non-default `flavour`
3. `runtime_preset` default flavour
4. Kennel default flavour `dev`

In implementation terms, `runtime_preset` only replaces `flavour` when:

- `runtime_preset` is present,
- `base_container` is not supplied,
- `base_snapshot` is not supplied,
- and `flavour` is still the default `dev`.

References:

- [kennel/src/server.py](/home/josep/dog/kennel/src/server.py#L907)
- [kennel/src/server.py](/home/josep/dog/kennel/src/server.py#L1146)

## Inject Request Semantics

Kennel inject accepts:

```json
{
  "runtime_preset": "codex",
  "bootstrap_profile": null,
  "bootstrap_plan": null,
  "runtime_files": {},
  "repo_url": "https://github.com/example/repo.git",
  "env_vars": {
    "OPENAI_API_KEY": "sk-..."
  }
}
```

### Inject Ordering

Kennel inject composes runtime defaults and explicit execution data in this order:

1. Apply `runtime_preset` to fill `bootstrap_profile` only when `bootstrap_profile` is absent.
2. Build profile-owned runtime files from `bootstrap_profile`.
3. Merge caller-supplied `runtime_files` on top of profile runtime files.
4. Choose execution plan by precedence:
   1. explicit `bootstrap_plan`
   2. derived `bootstrap_profile` plan
   3. legacy plan from `ssh_pubkey` / `env_vars` / `repo_url`

That means:

- `runtime_preset` is a defaulting layer,
- `bootstrap_profile` is a more explicit kennel-side override,
- `bootstrap_plan` is the most explicit execution contract.

References:

- [kennel/src/server.py](/home/josep/dog/kennel/src/server.py#L916)
- [kennel/src/server.py](/home/josep/dog/kennel/src/server.py#L428)
- [kennel/src/server.py](/home/josep/dog/kennel/src/server.py#L438)
- [kennel/src/server.py](/home/josep/dog/kennel/src/server.py#L1240)

## Built-In Bootstrap Profiles

### `codex_app_server`

Current built-in behavior:

- writes a default `~/.codex/config.toml`
- creates the workspace directory if needed
- starts `codex app-server --listen ws://0.0.0.0:4500`
- registers the runtime as service `codex`

### `claude_code_remote_control`

Current built-in behavior:

- writes a default `~/.claude/settings.json`
- creates the workspace directory if needed
- starts `claude remote-control --name kennel --permission-mode bypassPermissions --spawn same-dir`
- registers the runtime as service `claude_code`

### `hermes_agent_runtime`

Current built-in behavior:

- writes default runtime files under `/home/dev/.hermes`:
  - `config.yaml`
  - `.env`
  - `hermes-agent-launcher`
- launcher defaults include:
  - `DOG_WORKSPACE_AGENT_HERMES_RUNTIME_MODE=gateway_ws`
  - `DOG_WORKSPACE_AGENT_HERMES_HOST=0.0.0.0`
  - `DOG_WORKSPACE_AGENT_HERMES_PORT=4319`
  - `DOG_WORKSPACE_AGENT_HERMES_AUTO_INSTALL=true` (attempt installer bootstrap when runtime command is missing)
  - optional `DOG_WORKSPACE_AGENT_HERMES_GATEWAY_CMD` override
- `.env` includes API mode placeholders (disabled by default):
  - `API_SERVER_ENABLED=false`
  - `API_SERVER_HOST=127.0.0.1`
  - `API_SERVER_PORT=8642`
  - `API_SERVER_KEY=`
- creates `/home/dev/workspace` if needed
- starts `/home/dev/.hermes/hermes-agent-launcher` as a websocket gateway runtime on port `4319` (or falls back to `hermes` / `hermes-agent` gateway commands)
- registers the runtime as service `hermes`

Canonical Stage 1 paths:

- Hermes home: `/home/dev/.hermes`
- workspace path: `/home/dev/workspace`

References:

- [kennel/src/server.py](/home/josep/dog/kennel/src/server.py#L395)
- [kennel/src/server.py](/home/josep/dog/kennel/src/server.py#L438)

## Service Manifest and Readiness

Background `run_command` steps with a `service_name` are converted into declared services.

Kennel then reports discovered service state through `GET /envs/{name}/services`.

Current readiness rules:

- if a declared service has a port and that port is listening, it is `ready`
- if a declared service has no port and its PID is running, it is `ready`
- if a declared service has a PID but the expected port is not listening yet, it is `pending`

Hermes-specific readiness note:

- when Hermes PID is running but port `4319` is not listening, readiness text points operators to `/tmp/hermes.log`

References:

- [kennel/src/server.py](/home/josep/dog/kennel/src/server.py#L557)
- [kennel/src/server.py](/home/josep/dog/kennel/src/server.py#L671)
- [kennel/src/server.py](/home/josep/dog/kennel/src/server.py#L1004)

## Coexistence With Backend Logic

This kennel API does not require callers to give up backend-defined env construction.

The intended coexistence is:

- kennel `runtime_preset` remains available as a kennel-owned defaulting layer,
- callers may still send explicit `flavour`,
- callers may still send explicit `bootstrap_profile`,
- callers may still send explicit `bootstrap_plan`,
- callers may still overlay `runtime_files` and `env_vars`.

The integration question is therefore not whether both sides may contain preset/profile logic. The integration question is whether the combined interface preserves a clear ordering so callers know which layer is supplying defaults and which layer is issuing an explicit override.

## Current Backend Relationship

`dog/backend` now uses kennel in two distinct ways:

- generic and explicitly backend-owned workspace startup still uses explicit `flavour` plus explicit `bootstrap_plan`
- default Codex agent-runtime startup now passes `runtime_preset: "codex"` and intentionally omits inject `bootstrap_plan` so kennel instantiates `codex_app_server`
- default Hermes agent-runtime startup can now pass `runtime_preset: "hermes"` to get kennel-owned default flavour/profile wiring when compatible startup settings are used

That means kennel’s preset system is now partially surfaced through the active backend workspace contract for Codex runtime startup, while backend retains explicit-plan control for other cases.

References:

- [backend/app/services/workspace_service.py](/home/josep/dog/backend/app/services/workspace_service.py#L183)
- [backend/app/services/workspace_service.py](/home/josep/dog/backend/app/services/workspace_service.py#L281)

For the broader reconciliation of backend and kennel interfaces, see [backend-kennel-interface-reconciliation.md](/home/josep/dog/kennel/docs/backend-kennel-interface-reconciliation.md).
