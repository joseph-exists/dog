# Workspace Create Form Shape

## Purpose

This note sketches the frontend shape for workspace creation now that the backend and kennel seam can express:

- top-level `runtime_preset`
- explicit `flavour`
- nested bootstrap intent
- nested `bootstrap_profile`
- nested `runtime_files`

The goal is to expose the healthy, simple path first while still preserving broader operator paths.

## Current Frontend State

The frontend create path now exposes the new seam in a first-pass operator-friendly shape.

Today:

- [WorkspaceCreatePanel.tsx](/home/josep/dog/frontend/src/components/Workspaces/panels/WorkspaceCreatePanel.tsx) exposes:
  - top-level `runtime_preset`
  - explicit `flavour`
  - typed bootstrap intent
  - advanced `bootstrap_profile`
  - advanced `runtime_files`
- [useWorkspaces.ts](/home/josep/dog/frontend/src/hooks/useWorkspaces.ts) serializes these fields into the normalized create input
- [workspaceService.ts](/home/josep/dog/frontend/src/services/workspaceService.ts) submits:
  - `runtime_preset`
  - nested `bootstrap.bootstrap_profile`
  - nested `bootstrap.runtime_files`

What remains intentionally simple:

- the form is still a single create panel rather than a more guided multi-step flow
- the runtime file editor is intentionally lightweight
- raw `bootstrap_plan` is still not exposed

## Current Backend / Kennel Reality

Today we have two important truths at the same time:

1. The backend seam can now express preset-driven and explicit-plan-driven creation in one normalized path.
2. The healthiest validated Codex runtime path in kennel is the kennel preset path exercised by [validate_provisioning.py](/home/josep/dog/kennel/scripts/validate_provisioning.py).

That means the frontend should not begin by exposing every low-level seam control equally.

Instead, the initial form should:

- make `runtime_preset` the clearest default path for runtime-oriented workspaces
- keep explicit `flavour` available
- keep typed bootstrap intent available
- keep advanced override controls present but clearly separated

## Initial UX Shape

The create form should be organized into three layers.

### 1. Core Workspace Settings

Always visible.

Fields:

- `name`
- `kind`
- `runtime_preset`
- `flavour`

Behavior:

- `runtime_preset` should be framed as "runtime defaults"
- `flavour` should remain editable even when `runtime_preset` is selected
- the UI should not imply that choosing a preset locks out explicit flavour choice
- if no runtime preset is selected, the form should still support a generic workspace flow through explicit `flavour`

Recommended first options:

- runtime presets:
  - none
  - `codex`
  - `claude_code`
  - `hermes-agent`
- flavours:
  - `base`
  - `dev`
  - `cuda`

### 2. Bootstrap Intent

Visible by default, but compact.

Fields:

- repository source(s)
- repo URL or user repo id
- repo ref
- workspace path
- install intent
- startup intent
- ssh public key
- env vars

Behavior:

- this section remains the main declarative path for most non-operator users
- startup intent should still allow:
  - terminal only
  - named startup profile
  - agent service

### 3. Advanced Runtime Overrides

Collapsed by default.

Fields:

- `bootstrap.bootstrap_profile`
- `bootstrap.runtime_files`

Behavior:

- label this clearly as advanced or operator-focused
- do not hide it behind permissions in the UI unless the backend is also enforcing that distinction
- treat it as valid and intentional, not as a debug-only escape hatch
- present these fields as overrides and extensions, not replacements for presets or bootstrap intent
- use explicit, detailed tooltip information which does not assume or require detailed understanding of backend or kennel.

## Recommended Panel Shape

### Section A: Core

- Name
- Kind
- Runtime Preset
- Flavour

Support text:

"Use a runtime preset for sane defaults. Keep flavour editable when you need to override the base environment."

Recommended initial interaction:

- keep `runtime_preset` optional
- if a runtime preset is chosen, keep `flavour` visible rather than disabling it
- if `startup_intent.mode === "agent_service"`, prefill matching runtime presets where useful, but do not force them

### Section B: Source And Bootstrap

- Repository source selector
- Repo details
- Install intent
- Startup intent
- SSH public key
- Env vars

Support text:

"This section declares what the workspace should materialize and how it should start."

### Section C: Advanced Runtime Overrides

Collapsed accordion or secondary card.

- Bootstrap Profile
- Runtime Files editor

Support text:

"These fields override or extend runtime-specific defaults. Use them when kennel defaults are close but not sufficient."

## Runtime Files Editor Shape

Do not begin with a raw JSON blob for the entire form.

A reasonable first implementation is:

- multiline key/value list
- one file path plus content block per entry
- add/remove entry controls

Suggested view model:

```ts
type RuntimeFileDraft = {
  path: string
  content: string
}
```

That can later serialize into:

```ts
Record<string, string>
```

## Initial Frontend Submission Shape

The frontend create form should submit:

```ts
{
  name,
  kind,
  flavour,
  runtime_preset,
  repo_url,
  ssh_pubkey,
  env_vars,
  bootstrap: {
    repo_source,
    workspace_path,
    install_intent,
    startup_intent,
    env_vars,
    ssh_pubkey,
    bootstrap_profile,
    runtime_files,
  }
}
```

This should be read as a permissive surface:

- `runtime_preset` may be omitted
- `bootstrap` may be omitted
- `runtime_preset`, `flavour`, and typed bootstrap intent may all coexist
- advanced fields should only be sent when explicitly populated

## What To Expose Initially

Recommended initial exposure:

- expose `runtime_preset`
- keep explicit `flavour`
- keep typed bootstrap intent
- expose `bootstrap_profile` in Advanced
- expose `runtime_files` in Advanced

Recommended not to expose initially:

- raw `bootstrap_plan`
- internal create-time base-container fields

## Initial Form Recommendation

For the first frontend integration slice, expose:

- `name`
- `kind`
- `runtime_preset`
- `flavour`
- repository source controls
- install intent
- startup intent
- env vars
- ssh public key

Expose in an advanced section:

- `bootstrap_profile`
- `runtime_files`

Do not expose in the first slice:

- raw `bootstrap_plan`
- internal base container or base snapshot controls
- operator-only create-time infrastructure selectors that are not part of the current public backend contract

## Why This Shape Fits Current Reality

- It matches the backend request model now.
- It respects the healthy kennel Codex preset path.
- It preserves explicit operator overrides.
- It avoids making the first frontend integration depend on raw execution-plan authoring.

## Immediate Follow-Through

The next frontend integration slice should update:

- [WorkspaceCreatePanel.tsx](/home/josep/dog/frontend/src/components/Workspaces/panels/WorkspaceCreatePanel.tsx)
- [useWorkspaces.ts](/home/josep/dog/frontend/src/hooks/useWorkspaces.ts)
- [workspaceService.ts](/home/josep/dog/frontend/src/services/workspaceService.ts)

so the current panel reflects this three-layer structure instead of only the earlier bootstrap-intent-only shape.
