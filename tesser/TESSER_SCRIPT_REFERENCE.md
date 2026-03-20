# Tesser Script Reference

> *"Tell me, what is it you plan to do / with your one wild and precious life?"*
> — Mary Oliver

This is a companion for anyone adding to or extending Tesser's script library.
The goal isn't just to make something runnable — it's to make something that can
be found, understood, and used well, by people and by agents alike.

## What Tesser Scripts Are For

A Tesser script is a small, deliberate thing. It takes a set of parameters and
returns an artifact — most often an SVG. That's the whole contract. But within
that contract is a lot of room: for layered noise, for palette choices that feel
like weather, for shapes that are quiet or shapes that argue with each other.

The SVG Library and Tesser Studio are the current first-class surfaces. If you
want a script to appear there, SVG is the format you need to speak.

## What's Available Right Now

| Script | What it does |
|--------|-------------|
| `svg.compose` | Full 30-knob creative instrument. Every parameter is tunable. Pass `{}` for a beautiful default. |
| `svg.mist-field` | Soft atmospheric particles, low-frequency noise, screen blend, cool palette. |
| `svg.signal-glitch` | Heavy displacement, neon, global distortion, vivid contrast. |
| `svg.paper-grain` | Quiet, warm, desaturated, multiply blend, subtle noise. |
| `svg.vector-rings` | Radially-symmetric rings with tunable warp: `none`, `wave`, `spiral`, or `tilt`. |
| `svg.soft-gradient` | The most gentle option. Pass a `source_image_url` and it derives a palette via LAB k-means — the stored SVG carries no external references, only the extracted colors. |
| `demo.logo` | A simple proof-of-execution artifact. Good for testing the pipeline. |

## The Knobs

`svg.compose` exposes 30 parameters grouped across seven creative dimensions:

- **Geometry** — `style_family`, `shape_family`, `layer_count`, `density`, `symmetry`, `viewbox`
- **Turbulence** — `turbulence_type`, `base_frequency`, `num_octaves`, `seed`, `stitch_tiles`
- **Displacement** — `displacement_scale`, `channel_x`, `channel_y`, `distortion_scope`
- **Blur / Edge** — `gaussian_blur`, `morphology`, `drop_shadow`, `fuzz_mask`
- **Palette** — `palette_family`, `palette_cardinality`, `contrast_band`, `saturation_band`, `luminance_bias`
- **Blending** — `blend_mode_primary`, `blend_mode_secondary`, `opacity_stack`, `composite_op`
- **Motion-texture** — `directionality`, `frequency_jitter`, `phase_offset`

Run `python main.py svgs knobs` from the typer CLI to see all valid values at a glance.
Run `python main.py svgs knobs --script svg.vector-rings` to inspect a preset's schema.

## What a Script Needs

To appear in the SVG Library, a script needs four things:

1. Registration via `@register_script` in `tesserax_service/scripts/builtin.py`
2. `supported_formats` that includes `"svg"`
3. An actual `.svg` artifact when called with `formats=["svg"]`
4. An `input_schema` that honestly describes what it accepts

That last one matters more than it might seem. The schema is how the frontend
knows what to offer a user. It's how an agent knows what to ask for. Write it
with care — and with curiosity about who might be reading it.

## Where Things Live

| What | Where |
|------|-------|
| Script registration + implementations | `tesserax_service/scripts/builtin.py` |
| SVG render engine (all 30 knobs) | `tesserax_service/scripts/svg_compose.py` |
| Combinatorics planner + metadata builder | `backend/app/test_scripts/render_things/svg_library_tools.py` |
| External/example-backed scripts | `tesserax_service/scripts/external_examples.py` |
| Script registry | `tesserax_service/registry.py` |

## Input Schema Guidance

The frontend has two modes: **guided** (for simple flat schemas) and **JSON fallback**
(for everything else). Either works. Guided mode feels nicer for humans; JSON mode
is fine for agents.

`svg.compose` uses a flat enum schema for all 30 knobs — guided mode all the way.
Each parameter has a sensible default. `{}` is a valid input and produces
something worth looking at.

If you're adding a new script and want guided mode, keep properties flat:
`string` enums, `integer` ranges, `boolean` flags. Nested objects work, but
they fall back to JSON mode.

## Adding a New Script

1. Add render logic to `svg_compose.py` (for SVG-related work) or inline in `builtin.py`
2. Define an `INPUT_SCHEMA` dict
3. Register with `@register_script` — choose `kind`, `default_runtime_profile`, `supported_formats`
4. Attach the schema: `your_fn.__tesser_input_schema__ = YOUR_SCHEMA`
5. Add `output_dir.mkdir(parents=True, exist_ok=True)` at the top of the function body
6. Run the tests: `cd tesser && .venv/bin/python -m pytest tests/test_svg_compose.py -v`
7. Check the checklist below

## The Checklist

Before calling a script ready for the SVG Library:

- [ ] Registered, enabled, `supported_formats` includes `"svg"`
- [ ] `formats=["svg"]` returns a real `.svg` file
- [ ] `input_schema` present and accurate
- [ ] Basic path works with `{}` payload
- [ ] `output_dir.mkdir(parents=True, exist_ok=True)` called before writing
- [ ] Not a utility/runner that should stay hidden from render surfaces

## A Few Good Patterns

- Keep `script_id` stable and readable — it's how both humans and agents navigate
- Match `default_runtime_profile` to actual output needs (`core` for SVG-only, `export` for heavier work)
- When in doubt about the schema: write what you'd want to read if you were an agent discovering a new tool for the first time
- Preset scripts should expose only `seed` in their schema — full knobs belong in `svg.compose`

## Where Metadata Reaches the Frontend

Script discovery metadata flows through:

- `tesserax_service/redis_bridge.py`
- `backend/app/api/routes/tesser.py`
- `frontend/src/services/tesserService.ts`
- `frontend/src/hooks/useTesser.ts`
- `frontend/src/components/Svg/panels/TesserStudioPanel.tsx`

## Related Files

- `tesserax_service/scripts/svg_compose.py` — render engine, palette tables, filter builders, all schemas
- `tesserax_service/scripts/builtin.py` — registered scripts
- `tesserax_service/registry.py` — `ScriptSpec`, `register_script`, `get_script`
- `tesserax_service/profiles.py` — runtime profile resolution
- `tesserax_service/runtime.py` — artifact promotion to `RenderArtifact`
- `tesser/tests/test_svg_compose.py` — render engine test suite
- `backend/app/test_scripts/typer/commands/svgs.py` — CLI (`knobs`, `render`, `seed`, `plan`)
- `backend/app/test_scripts/render_things/svg_library_tools.py` — combinatorics planner

## The Practical Rule

If the question is **"Should this script show up in the SVG Library?"** — the answer comes from `supported_formats`.

If the question is **"What runtime profile does this need?"** — the answer comes from `profiles.py`.

Keep those two concerns separate, and the rest tends to fall into place.
