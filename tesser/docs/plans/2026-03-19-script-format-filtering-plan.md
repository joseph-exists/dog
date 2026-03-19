# Script Format Filtering Plan

**Date**: 2026-03-19
**Status**: Proposed
**Goal**: make SVG-capable script filtering a first-class registry/API concern so the SVG Library can request only scripts that can return SVG.

## Problem

Today the SVG Library needs to limit callable scripts to those that can return SVG.

The current capability flow is not the right source of truth for that filter:

- `profiles.py` resolves capabilities from a concrete `RenderRequest`
- `render.svg` is inferred from requested formats
- script discovery happens before the frontend creates a render request

So the system needs a declarative script-level answer to:

`Which formats can this script produce when asked correctly?`

## Recommendation

Introduce `supported_formats` on `ScriptSpec` in the registry, carry it through Tesser list/help responses, and allow backend filtering by format at the script-list endpoint.

The frontend SVG Library should then consume:

- `/tesser/scripts?format=svg`

and stop inferring SVG eligibility indirectly.

## Design

## 1. Registry becomes the declaration point

Update `ScriptSpec` in `tesser/src/tesserax_service/registry.py` to include:

- `supported_formats: set[str] = {"svg"}`

and expose it from `ScriptSpec.to_dict()`.

Suggested shape:

```python
@dataclass(slots=True)
class ScriptSpec:
    script_id: str
    kind: str
    default_runtime_profile: str
    enabled: bool = True
    disabled_reason: str | None = None
    supported_formats: set[str] = field(default_factory=lambda: {"svg"})
    base_capabilities: set[str] = field(default_factory=set)
    resolve_capabilities: CapabilityResolver | None = None
```

Update `register_script(...)` to accept:

- `supported_formats: set[str] | None = None`

and normalize to `{"svg"}` when unspecified.

## Why this belongs in the registry

- the registry is already the durable metadata surface for script discovery
- the frontend needs this information before request construction
- it avoids encoding UI filtering rules in `profiles.py`

## 2. Profiles stay execution-focused

Keep `profiles.py` responsible for:

- mapping requested formats to capabilities
- runtime profile selection
- export dependency preflight

Do not make `profiles.py` the source of discoverability.

At most, add a helper that validates a requested format against `spec.supported_formats`, but the declaration itself should still come from the registry.

## 3. Standardize existing external script metadata

`tesser/src/tesserax_service/scripts/external_examples.py` already computes `supported_formats`.

That logic should be threaded into the registry registration call:

- currently external scripts calculate `supported_formats`
- but `_register_external(...)` does not pass it into `register_script(...)`

Change `_register_external(...)` so it registers:

- `supported_formats=set(spec.supported_formats)`

This removes the current split-brain where the external classifier knows formats but `ScriptSpec` does not.

## 4. Builtins should declare formats explicitly

Built-in scripts should pass `supported_formats={"svg"}` explicitly when registered.

Reason:

- avoids hidden defaults
- keeps metadata readable
- makes future non-SVG builtins obvious at registration sites

## 5. Redis bridge should expose supported formats

Update `tesser/src/tesserax_service/redis_bridge.py`:

- `_registry_script_metadata()`
- `_build_script_help_response(...)`
- builtin metadata entries

so responses include:

- `supported_formats`

Suggested script list/help payload additions:

- `supported_formats: ["svg"]`

Builtin metadata should also add this field.

## 6. Backend API should support format filtering

Update the dog backend Tesser route:

- `backend/app/api/routes/tesser.py`

to accept an optional query param:

- `format: str | None = None`

and filter the list response to scripts whose `supported_formats` contains the requested format.

Suggested route contract:

- `GET /tesser/scripts`
- `GET /tesser/scripts?format=svg`

This keeps the API generic enough for later:

- `format=gif`
- `format=mp4`

## 7. Backend models should expose supported_formats

Update:

- `backend/app/models.py`

for:

- `TesserScriptPublic`
- `TesserScriptHelpResponse`

to include:

- `supported_formats: list[str] = Field(default_factory=list)`

The frontend service types should then expose it as well.

## Concrete File Touches

## Tesser service layer

- `tesser/src/tesserax_service/registry.py`
  - add `supported_formats` to `ScriptSpec`
  - add `supported_formats` argument to `register_script`
  - expose it in `to_dict()`

- `tesser/src/tesserax_service/scripts/builtin.py`
  - register builtins with explicit `supported_formats={"svg"}`

- `tesser/src/tesserax_service/scripts/external_examples.py`
  - pass `supported_formats=set(spec.supported_formats)` into `register_script(...)`

- `tesser/src/tesserax_service/redis_bridge.py`
  - include `supported_formats` in list/help metadata
  - builtin metadata entries include `supported_formats`

- optional:
  - `tesser/src/tesserax_service/api.py`
  - if the sync API should expose the same metadata surface

## Dog backend

- `backend/app/models.py`
  - add `supported_formats` to `TesserScriptPublic`
  - add `supported_formats` to `TesserScriptHelpResponse`

- `backend/app/api/routes/tesser.py`
  - add `format` query param to list route
  - filter payload by requested format
  - return `supported_formats` in list/help responses

- optional:
  - `backend/app/services/tesser_service.py`
  - add passthrough payload support only if request typing needs expansion later

## Frontend

- `frontend/src/services/tesserService.ts`
  - add `supported_formats` to `TesserScript`
  - add `supported_formats` to `TesserScriptHelpResponse`
  - optionally add `listScripts({ format?: string })`

- SVG Library usage
  - call `listScripts({ format: "svg" })`

## Suggested Interfaces

## Registry

```python
def register_script(
    script_id: str,
    *,
    kind: str = "render",
    default_runtime_profile: str = "core",
    enabled: bool = True,
    disabled_reason: str | None = None,
    supported_formats: set[str] | None = None,
    base_capabilities: set[str] | None = None,
    resolve_capabilities: CapabilityResolver | None = None,
) -> Callable[[ScriptFn], ScriptFn]:
```

## Backend API route

```python
@router.get("/scripts", response_model=TesserScriptsPublic)
async def list_scripts(
    current_user: CurrentUser,
    format: str | None = Query(default=None),
) -> Any:
```

## Frontend service

```ts
async listScripts(input?: { format?: string }): Promise<TesserScriptsResponse>
```

## Filtering Semantics

Recommended list route behavior:

- no `format` query:
  - return all enabled/visible scripts
- `format=svg`:
  - return only scripts where `supported_formats` contains `svg`
- unknown format:
  - return empty list, not an error

Reason:

- simple consumer behavior
- safe for future experimentation

## Why not filter only in the frontend

Because that would leave the frontend dependent on incomplete metadata and duplicate filtering rules across surfaces.

The backend already mediates Tesser discovery, so it should deliver an already-scoped list when a surface has a clear media requirement.

## Why not use base_capabilities alone

Because current capability resolution is partially request-derived.

Absence of `render.svg` in `base_capabilities` does not currently mean the script cannot return SVG. It may simply mean SVG was never declared there because format capability is added later from the request.

So `supported_formats` is the cleaner and more accurate concept.

## Rollout Order

1. Add `supported_formats` to `ScriptSpec` and registration sites.
2. Thread it through Redis bridge list/help responses.
3. Add backend model fields and route filtering.
4. Update frontend Tesser service types and `listScripts({ format: "svg" })`.
5. Update SVG Library to request only SVG-capable scripts.

## Acceptance Criteria

- Script discovery metadata includes `supported_formats`.
- Builtin and external scripts both populate it.
- `GET /tesser/scripts?format=svg` returns only SVG-capable scripts.
- Tesser help responses also expose `supported_formats`.
- The SVG Library no longer needs frontend-side heuristics to decide whether a script belongs there.
