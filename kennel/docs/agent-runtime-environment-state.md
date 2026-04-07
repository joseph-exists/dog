# Kennel Agent Runtime Environment State

This note summarizes the current `kennel` implementation so we can provide ephemeral and persistent agent runtime environments with tools like `codex`, `claude-code`, or `hermes-agent`

## Current Model

`kennel` currently has two separate optimization layers:

1. Build-time layering for reusable base environments.
2. Spawn-time injection for per-workspace personalization.

In code, the layering model is defined in [src/flavours.py](/home/josep/dog/kennel/src/flavours.py) and built by [src/rebuild_worker.py](/home/josep/dog/kennel/src/rebuild_worker.py).

- `base`: Ubuntu Noble plus core system packages and the `dev` user.
- `dev`: `base` plus build tools, Python, `pipx`, `uv`, and Node via `nvm`.
- `cuda`: `dev` plus CUDA toolkit, cuDNN, and a PyTorch venv.

The environment creation path lives in [src/server.py](/home/josep/dog/kennel/src/server.py):

- `POST /flavours/{flavour}/rebuild` rebuilds the reusable base chain.
- `POST /envs` clones a user environment from a base flavour.
- `POST /envs/{name}/inject` personalizes that running environment.

## What Is Optimized Today

The main optimization is that expensive package installation happens during flavour rebuild, not at workspace spawn time.

- `rebuild_flavour()` creates `base-{layer}` containers once and provisions them in place.
- Child layers are created with `lxc-copy -s -B overlay`, so each layer reuses its parent filesystem.
- User environments are also created with `lxc-copy -s`, so workspace startup should mostly pay for clone, boot, and injection.
- Ephemeral environments use `lxc-start -e`, which adds a transient overlay on top of the cloned environment.

This means the current fast path is:

1. Prebuild `base-dev` or `base-cuda`.  
2. Clone a new env from that base.
3. Start it.
4. Inject repo, env vars, keys, files, and background runtime commands.

## Spawn Injection State

Spawn-time injection is more capable than the original docs suggest.

The historical example in [example-spawn-injection.md](/home/josep/dog/kennel/example-spawn-injection.md) shows ad hoc shell commands. The current implementation is a typed bootstrap plan in [src/server.py](/home/josep/dog/kennel/src/server.py).

Supported injection capabilities today:

- Ensure a workspace user exists, with passwordless sudo.
- Add SSH public keys.
- Write workspace env vars into `.bashrc` and `.profile`.
- Clone a repo to a target path.
- Write arbitrary runtime files into the container.
- Run foreground bootstrap commands.
- Run background commands and register them as declared services.

This is the main extension seam for agent runtimes right now. A backend can already send a `bootstrap_plan` that:

- writes agent config files,
- clones the project,
- starts an agent runtime in the background,
- tags that process with `service_name`.

## Agent Runtime Support Already Present

`server.py`   service profiles for:

- `codex`
- `claude_code`
- `hermes`

These profiles currently provide metadata and process tracking only:

- label and runtime kind,
- PID/log file conventions,
- service discovery via `/envs/{name}/services`,
- readiness based on PID presence and optional port listening.

Update: the repo now has an initial `dev-codex` flavour scaffold and a `codex_app_server` bootstrap profile in [src/server.py](/home/josep/dog/kennel/src/server.py) that writes a default Codex config and launches `codex app-server` as a tracked websocket service.

Update: kennel also now accepts a first-class `runtime_preset` contract for `codex`, which normalizes the default flavour/bootstrap pairing to `dev-codex` plus `codex_app_server`.

Update: backend now uses that preset as the default Codex agent-runtime startup path by omitting an explicit inject `bootstrap_plan`, so kennel owns `codex_app_server` instantiation for the default Codex runtime flow.

Update: kennel now also supports a `claude_code` runtime preset, mapped to `dev-claude-code` plus `claude_code_remote_control`.


### implemented Prebaked runtime flavours

Add flavours like:

- `dev-codex`
- `dev-claude-code`
- `hermes-agent`
- `hermes-agent-dev`

These would extend `dev` and install the runtime tool during rebuild. This keeps spawn fast and predictable, and matches the existing optimization strategy.
