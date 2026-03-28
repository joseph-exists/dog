# Kennel Agent Runtime Environment State

This note summarizes the current `kennel` implementation so we can plan ephemeral and persistent agent runtime environments with tools like `codex`, `claude-code`, or `hermes-agent` preinstalled.

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

`server.py` already contains service profiles for:

- `codex`
- `claude_code`
- `hermes`

These profiles currently provide metadata and process tracking only:

- label and runtime kind,
- PID/log file conventions,
- service discovery via `/envs/{name}/services`,
- readiness based on PID presence and optional port listening.

What is not present yet:

- no flavour that preinstalls `codex`, `claude-code`, or `hermes-agent`,
- no canned bootstrap profiles that install or launch those runtimes,
- no package/version management for runtime toolchains,
- no first-class distinction between runtime image selection and repo bootstrap.

## Important Gaps Between Docs and Code

There is a real mismatch between the top-level docs and the implementation.

In [layer-model.md](/home/josep/dog/kennel/layer-model.md), the model is described as snapshot-based and references `snap0`.

In current code:

- [src/rebuild_worker.py](/home/josep/dog/kennel/src/rebuild_worker.py) does not create LXC snapshots.
- It builds reusable `base-{flavour}` containers directly and stops them when provisioning is complete.
- [src/server.py](/home/josep/dog/kennel/src/server.py) still defaults new env creation to `base_snapshot_name = "snap0"`.
- [src/server.py](/home/josep/dog/kennel/src/server.py) also reports `snapshot_ready` by checking for `snap0`.

So the current system behaves more like "overlay-clone from stopped base containers" than "clone from named snapshots".

That mismatch should be resolved before adding runtime presets, because the planning language will otherwise be wrong about where preinstalled agent tooling lives.

## Practical Planning Implications

Based on the current codebase, there are two viable ways to add agent runtime environments.

### Option A: Prebaked runtime flavours

Add flavours like:

- `dev-codex`
- `dev-claude`
- `dev-hermes`

These would extend `dev` and install the runtime tool during rebuild. This keeps spawn fast and predictable, and matches the existing optimization strategy.

### Option B: Runtime install at injection time

Keep using `dev`, then install or activate the runtime in the `bootstrap_plan`.

This gives flexibility but shifts cost and failure risk into workspace startup.

Given the current architecture, Option A is the better fit for stable, repeatable agent environments. Spawn-time injection is better used for:

- repo-specific config,
- secrets and keys,
- runtime config files,
- launch commands,
- per-session personalization.

## Recommended Next Design Step

The cleanest next abstraction is to separate:

- `base flavour`: OS/toolchain image to clone from.
- `runtime preset`: `codex`, `claude-code`, `hermes-agent`, or none.
- `workspace bootstrap`: repo clone, config files, env vars, and runtime launch plan.
- `persistence mode`: ephemeral or persistent.

That would let kennel keep its current layering benefits while making agent runtime environments a first-class concept instead of overloading generic injection.
