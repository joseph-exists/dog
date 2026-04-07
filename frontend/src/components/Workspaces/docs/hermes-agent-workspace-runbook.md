# Hermes Agent Workspace Runbook

This runbook defines the platform-supported process to provision, configure, connect to, and operate Hermes agent workspaces.

## Goals

- make workspace-type intent explicit at create time
- keep startup semantics clear between `terminal_only` and `agent_service`
- make room connectivity predictable for Hermes runtime usage
- standardize Hermes runtime file placement under `/home/dev/.hermes`

## Provisioning Contract

For a default Hermes runtime workspace, create with:

- `runtime_preset: "hermes"`
- `bootstrap.startup_intent: { "mode": "agent_service", "agent_profile": "hermes" }`
- optional `bootstrap.repo_source` / `workspace_path` / install intent

Expected runtime outcomes:

- create defaults `flavour` from `dev` to `hermes-agent` (unless explicit non-default flavour is provided)
- inject defaults to bootstrap profile `hermes_agent_runtime`
- kennel owns startup process selection for the Hermes runtime path when no explicit `bootstrap_profile` override is sent

## Startup Intent Semantics

### Terminal Only

`bootstrap.startup_intent.mode = "terminal_only"`

- no long-running Hermes runtime process is auto-started
- workspace terminal access still works
- Hermes commands are manual operator actions in terminal

### Agent Runtime

`bootstrap.startup_intent = { "mode": "agent_service", "agent_profile": "hermes" }`

- long-running Hermes runtime process is started during bootstrap
- runtime service is declared/discovered as `agent_runtime` with runtime id `hermes`
- workspace becomes eligible for room `agent_runtime_connect` once service discovery reports availability

## Runtime Files and Paths

For `hermes_agent_runtime`, kennel writes default runtime files to:

- config: `/home/dev/.hermes/config.yaml`
- secrets template: `/home/dev/.hermes/.env`
- launcher: `/home/dev/.hermes/hermes-agent`

Notes:

- `~/.hermes/.env` is created for workspace-scoped secret injection and is written with restricted file mode
- `~/.hermes/hermes-agent` is the canonical launcher path for Hermes runtime bootstrap in this flow
- callers may still override/add files through `bootstrap.runtime_files`

## Connection Paths

### Workspace Terminal

1. Provision workspace as above.
2. Wait until workspace status is `ready` and terminal action is allowed.
3. Open workspace terminal from Workspaces UI.
4. Validate runtime artifacts:
   - `ls -la /home/dev/.hermes`
   - inspect `/home/dev/.hermes/config.yaml`
   - update `/home/dev/.hermes/.env` with environment-specific secrets as needed

### Room Workspaces Panel

1. Open room panel: `Workspace Links`.
2. Select the target workspace candidate.
3. Set purpose to `Agent Runtime`.
4. Wait for descriptor status `available`.
5. Click `Set Current`.
6. Use `Send To Runtime` for backend-mediated runtime invocation.

If status is `pending`, the runtime is not yet routable in discovery. Refresh until available or inspect workspace runtime readiness in workspace details.

## Hermes Gateway Setup Alignment

Hermes gateway and runtime auth details should follow the upstream quickstart:

- https://hermes-agent.nousresearch.com/docs/getting-started/quickstart/

Platform recommendation:

- store gateway/auth values in `/home/dev/.hermes/.env` for workspace-local runtime usage
- keep non-secret defaults in `/home/dev/.hermes/config.yaml`
- avoid embedding real secrets directly in bootstrap plan command text

## Advanced Overrides

Use advanced fields only when operator intent requires it:

- `bootstrap.bootstrap_profile` overrides preset-selected profile
- `bootstrap.runtime_files` overlays or replaces profile-owned files

If advanced overrides are used, runtime startup ownership may move away from the default preset-driven path.
