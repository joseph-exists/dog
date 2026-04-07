# Runtime Service Alignment Contract

This note captures the current shared seam between `dog/backend` and `dog/kennel` for runtime-oriented workspace services.

Its purpose is not to declare one side fully canonical. Its purpose is to make the current relationship visible enough that later iterations can adjust it deliberately.

## Why This Exists

Backend and kennel both participate in runtime behavior:

- backend can choose startup intent and process launch shape
- kennel can choose runtime metadata, preset defaults, profile-owned assets, and readiness probing

That means the shared seam is not just a string like `codex` or `claude_code`. It is a bundle of assumptions:

- runtime identifier
- service identifier
- startup command expectations
- protocol and port expectations
- runtime-file defaults
- readiness semantics

This document records the current bundle per runtime.

## Contract Shape

For each shared runtime/service identifier, Stage 1 tracks these fields:

- `runtime_id`
- `service_name`
- backend startup defaults
- kennel service metadata defaults
- kennel preset/profile defaults
- current readiness interpretation
- current alignment notes

These are working integration semantics for the current slice, not a frozen final model.

## Current Runtime Registry

### `codex`

Backend side:

- runtime id: `codex`
- service name: `codex`
- backend startup ownership: kennel-owned for the default agent-runtime path
- backend default command override env var: `DOG_WORKSPACE_AGENT_CODEX_CMD`
- backend default host env var: `DOG_WORKSPACE_AGENT_CODEX_HOST`
- backend default port env var: `DOG_WORKSPACE_AGENT_CODEX_PORT`
- backend projected port value: `4317`

Kennel side:

- service id: `codex`
- service label: `Codex Runtime`
- service kind: `agent_runtime`
- service protocol: `ws`
- service port: `4500`
- service path: `/`
- preset flavour default: `dev-codex`
- preset bootstrap profile default: `codex_app_server`
- profile-owned startup command: `codex app-server --listen ws://0.0.0.0:4500`
- profile-owned runtime file: `~/.codex/config.toml`

Current readiness interpretation:

- ready when the declared port `4500` is listening
- pending when the PID is running but `4500` is not yet listening

Alignment notes:

- backend and kennel currently share the same runtime/service identifier
- backend now delegates default Codex runtime startup to kennel by omitting an explicit inject `bootstrap_plan` for Codex agent-service workspaces
- kennel therefore owns the default Codex launch shape, workspace-directory preparation, runtime file write, and readiness contract for that path
- backend still projects env vars and runtime files into inject, and explicit bootstrap overrides can still reintroduce backend-owned execution when needed

### `claude_code`

Backend side:

- runtime id: `claude_code`
- service name: `claude_code`
- backend default command: `claude`
- backend default host env var: `DOG_WORKSPACE_AGENT_CLAUDE_CODE_HOST`
- backend default port env var: `DOG_WORKSPACE_AGENT_CLAUDE_CODE_PORT`
- backend default port value: `4318`

Kennel side:

- service id: `claude_code`
- service label: `Claude Code Runtime`
- service kind: `agent_runtime`
- service protocol: `ws`
- service port: none
- preset flavour default: `dev-claude-code`
- preset bootstrap profile default: `claude_code_remote_control`
- profile-owned startup command: `claude remote-control --name kennel --permission-mode bypassPermissions --spawn same-dir`
- profile-owned runtime file: `~/.claude/settings.json`

Current readiness interpretation:

- ready when the tracked PID is running

Alignment notes:

- backend and kennel currently agree on the shared identifier
- backend treats Claude Code as an agent-service launch target
- kennel treats the built-in profile as a remote-control server process
- the seam is less port-sensitive here than Codex, but there is still room for future clarification around protocol expectations and exposure model

### `hermes`

Backend side:

- runtime id: `hermes`
- service name: `hermes`
- backend default command: `hermes`
- backend default host env var: `DOG_WORKSPACE_AGENT_HERMES_HOST`
- backend default port env var: `DOG_WORKSPACE_AGENT_HERMES_PORT`
- backend default port value: `4319`

Kennel side:

- service id: `hermes`
- service label: `Hermes Runtime`
- service kind: `agent_runtime`
- service protocol: `http`
- service port: none
- preset flavour default: `hermes-agent`
- preset bootstrap profile default: `hermes_agent_runtime`
- profile-owned startup command: `hermes` (fallback: `hermes-agent`)

Current readiness interpretation:

- ready when the tracked PID is running

Alignment notes:

- backend and kennel currently agree on the shared identifier
- kennel now includes a first-class Hermes preset/profile default path
- callers can still use explicit bootstrap plans when they need backend-owned runtime startup

## Shared Interpretation Rules

### 1. Shared identifiers are meaningful, but not exhaustive

If backend emits a known `service_name`, kennel will attach service metadata and readiness expectations from its current registry.

If backend emits an unknown `service_name`, kennel will still accept it as a custom background service.

### 2. Metadata and execution can come from different layers

The current system allows:

- backend-owned execution intent with kennel-owned service metadata
- kennel-owned preset/profile execution intent with kennel-owned service metadata

That relationship is intentional to preserve flexibility during iteration.

### 3. Readiness is an interpretation layer

Kennel readiness is not pure process truth. It is kennel's current interpretation of the declared service metadata.

That is why protocol and port assumptions need to stay visible in the contract.

### 4. Profile-owned assets are runtime semantics too

Runtime files such as:

- `~/.codex/config.toml`
- `~/.claude/settings.json`

are part of the runtime contract, not just convenience details. Mixed-mode support will need to treat them explicitly.

## Current Open Areas

These are not unresolved in a blocking sense, but they remain intentionally open for later stages:

- whether the backend should retire Codex-specific startup command defaults entirely now that default startup is kennel-owned
- whether Claude Code protocol labeling should remain `ws` or become more explicitly tied to the remote-control exposure model
- whether kennel should gain a first-class profile-owned Hermes preset
- where the shared runtime/service registry should live if we later want machine-enforced parity rather than parallel documented mappings

## Source References

- [backend/app/services/workspace_bootstrap_service.py](/home/josep/dog/backend/app/services/workspace_bootstrap_service.py)
- [kennel/src/server.py](/home/josep/dog/kennel/src/server.py)
- [kennel/docs/runtime-preset-api-reference.md](/home/josep/dog/kennel/docs/runtime-preset-api-reference.md)
- [kennel/docs/backend-kennel-interface-reconciliation.md](/home/josep/dog/kennel/docs/backend-kennel-interface-reconciliation.md)
