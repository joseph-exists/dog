**SVG asset contract**

 generation/import should maintain compatibility across `NodeEditorForm` + `ContentRenderer`.

## 1) Compatibility Modes You Need To Support
 3 current render targets:

1. `content_format: "svg"` (via `SVGRenderer`)
- Best compatibility.
- Works as `<img data-url>` or inline SVG depending on options/safeMode.

2. `content_format: "mdx"` + background wrapper mode (`div style={{ backgroundImage: data-url(...) }}`)
- Very safe for MDX parsing.
- Best for “use SVG as background”.

3. `content_format: "mdx"` raw inline SVG (future/manual)
- Most fragile.
- Requires JSX-safe SVG syntax.

optimizing for 1 & 2 for current iteration.

## 2) Required SVG Constraints (Generator Output)
Enforce these at generation time:

- Single root `<svg ...>...</svg>` only.
- Must include `viewBox`.
- No XML prolog / DOCTYPE.
- No `<script>`, no event handlers (`on*` attrs), no `foreignObject`.
- No external refs (`href/xlink:href` to remote URLs), no external fonts.
- No HTML comments inside embedded JSX paths (or strip comments entirely).
- IDs must be namespaced per asset (and rewrite all `url(#...)` references).
- Prefer deterministic ordering/formatting for stable hashing/diffs.

## 3) Performance Constraints (Important for 10k Library)
Set hard limits so NodeEditor stays fast:

- File size target: `< 100 KB` (hard cap ~`250 KB`).
- Element count cap (paths/shapes/defs), e.g. `< 2,000`.
- Filter complexity cap (especially turbulence/displacement/convolve chains).
- Animation cap or disable for library default tier.
- No unbounded dimensions; rely on `viewBox`.

Also store precomputed metadata per asset:
- `bytes`, `viewbox_w/h`, `element_count`, `has_filters`, `filter_count`, `dominant_colors`, `tags`.

## 4) MDX-Specific Constraints
If used through background wrapper/data URL:
- Works well with normal SVG syntax.
- Keep size smaller (data URLs bloat quickly).
- Don’t rely on interactive/script behavior.

If ever inserted as inline JSX:
- Convert attrs to JSX-safe form (`className`, camelCase SVG attrs, etc.).
- Replace `<!-- -->` comments with JSX comments or remove.

## 5) Import Contract Recommendation
When users import from library, store:
- `svg_source` (canonical sanitized SVG)
- `asset_id`, `version`, `sha256`
- `tags` (semantic + style + complexity)
- `safety_level` (safe/default/advanced)
- `recommended_mode` (`svg`, `mdx-background`, `inline-mdx`)

And gate apply options in UI based on `recommended_mode`.

---

See also: `svg_combinatorics_reference_card.md` for pairwise parameter coverage guidance.
