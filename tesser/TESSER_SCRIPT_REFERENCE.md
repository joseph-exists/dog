# Tesser Script Reference Card

## Purpose

Use this as the quick engineer-facing reference when adding or extending Tesser scripts.

The goal is not only to make a script runnable, but to make it discoverable and compatible with how the current frontend consumes Tesser, especially the SVG Library and Tesser Studio surfaces.

## Current Frontend Reality

The frontend currently has a first-class path for **SVG** generation.

That means:

- the SVG Library requests only scripts with `supported_formats` containing `svg`
- Tesser Studio expects scripts that can return SVG artifacts
- completed SVG jobs can be saved into the `/svgs` library

GIF and MP4 are possible in Tesser, but they are **not** first-class in the current SVG library flow. If you are adding a script for the SVG Library, SVG support is the key requirement.

## The Minimum Contract For New Scripts

Every script that should appear in the SVG Library must satisfy all of the following:

1. It must be registered in `tesser/src/tesserax_service/registry.py`.
2. It must declare `supported_formats` and include `"svg"`.
3. It must produce at least one `.svg` artifact when called with `formats=["svg"]`.
4. It should expose a useful `input_schema` through the Tesser metadata path.
5. It should be safe for the frontend’s current guided/JSON input patterns:
   - simple top-level object parameters are best
   - deeper or irregular shapes are allowed, but the frontend will fall back to JSON mode

## Where To Wire Things

## 1. Registry metadata

Primary declaration point:

- `tesser/src/tesserax_service/registry.py`

Important fields on `ScriptSpec`:

- `script_id`
- `kind`
- `default_runtime_profile`
- `enabled`
- `disabled_reason`
- `supported_formats`
- `base_capabilities`
- `resolve_capabilities`

If a script should appear in the SVG Library, `supported_formats` must contain `svg`.

## 2. Builtin scripts

Builtin registrations live in:

- `tesser/src/tesserax_service/scripts/builtin.py`

Use explicit metadata. Do not rely on implied defaults if the script is intended for frontend discovery.

Example shape:

```python
@register_script(
    "my.script",
    kind="static",
    default_runtime_profile="core",
    supported_formats={"svg"},
    base_capabilities={"render.svg"},
)
```

## 3. External example-backed scripts

External script registration flows through:

- `tesser/src/tesserax_service/scripts/external_examples.py`

That path already derives `supported_formats`. If you are working in the examples-based system, make sure the script’s actual CLI/output behavior matches the inferred formats.

## Output Expectations

## SVG scripts

For SVG-facing scripts:

- when invoked with `formats=["svg"]`, return a `.svg` file path
- keep the primary artifact valid SVG
- avoid surprising non-SVG-only behavior if the script is advertised as SVG-capable

The runtime turns returned file paths into `RenderArtifact`s in:

- `tesser/src/tesserax_service/runtime.py`

The worker/bridge then promotes SVG specially so frontend consumers can preview it inline.

## Multi-format scripts

If the script can return multiple formats:

- declare all of them in `supported_formats`
- ensure format selection is actually honored
- keep SVG in the set if you want it exposed in the SVG Library

Example:

```python
supported_formats={"svg", "gif", "mp4"}
```

This does **not** mean the SVG Library will expose GIF/MP4 today. It only means the script truthfully advertises its output capabilities.

## Input Schema Guidance

Frontend Tesser Studio currently supports:

- guided mode for simple top-level object schemas
- JSON fallback for everything else

If you want a script to feel good in the current UI, prefer:

- `type: "object"`
- top-level `properties`
- `string`
- `number` / `integer`
- `boolean`
- string `enum`
- `required`
- `default`
- `description`

The frontend can also interpret:

- deep nested objects
- complex conditional schemas
- polymorphic unions
- advanced array/object nesting

Note that these will land in JSON mode rather than guided mode, so may need additional text guidance or --help.

## Where Metadata Reaches The Frontend

Script discovery/help metadata flows through:

- `tesser/src/tesserax_service/redis_bridge.py`
- `backend/app/api/routes/tesser.py`
- `frontend/src/services/tesserService.ts`
- `frontend/src/hooks/useTesser.ts`
- `frontend/src/components/Svg/panels/TesserStudioPanel.tsx`

If you add script-facing metadata that should be visible to the frontend, this is the chain you need to maintain.

## Checklist For SVG Library Compatibility

Before considering a script "ready" for frontend SVG use, confirm:

- [ ] Script is registered.
- [ ] `supported_formats` includes `svg`.
- [ ] `formats=["svg"]` produces a  `.svg` file.
- [ ] The script is enabled.
- [ ] The script is not a utility/runner that should stay hidden from end-user render surfaces.
- [ ] `input_schema` is present and reflects real parameters.
- [ ] At least the basic path works with a simple JSON object payload.
- [ ] If guided mode friendliness matters, the schema stays close to top-level primitives/enums.

## Good Patterns

- Keep `script_id` stable and readable.
- Prefer explicit `supported_formats` declarations.
- Match runtime profile to actual output needs:
  - SVG-only scripts usually stay in `core`
  - export-heavy scripts may resolve to `export`
- Keep parameter names legible for both CLI users and frontend users.
- Provide clear descriptions and help text where possible.



## Practical Rule Of Thumb

If the question is:

`Should this script show up in the SVG Library?`

the answer should come from:

- `supported_formats`

If the question is:

`What runtime profile and dependencies does this request need?`

the answer should come from:

- `profiles.py`

Keep those concerns separate.

## Related Files

- `tesser/src/tesserax_service/registry.py`
- `tesser/src/tesserax_service/profiles.py`
- `tesser/src/tesserax_service/runtime.py`
- `tesser/src/tesserax_service/worker.py`
- `tesser/src/tesserax_service/redis_bridge.py`
- `tesser/src/tesserax_service/scripts/builtin.py`
- `tesser/src/tesserax_service/scripts/external_examples.py`
- `frontend/src/services/tesserService.ts`
- `frontend/src/components/Svg/panels/TesserStudioPanel.tsx`

## Bottom Line

If you want frontend SVG compatibility, design and register the script as an SVG-capable script on purpose.

That means:

- declare `supported_formats={"svg"}`
- return real SVG artifacts
- expose a usable `input_schema`

