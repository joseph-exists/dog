**Implementation Plan (No New Models): Render `composition.blocks` + Use Authored `content_json`**

1. [x] Route-level rendering contract cleanup
- File: `frontend/src/routes/_layout/demo.$slug.tsx`
- Keep `ResolveDemoEntryPayload` as single source.
- Stop treating content as demo showcase; treat content as authored data.

2. [x] Add block renderer pipeline (using existing composition types)
- Create helper in route or `Demo` component module:
  - `renderDemoBlock(block: DemoBlockSpec, ctx) => ReactNode`
- Group blocks by existing `region` (`top`, `primary`, `auxiliary`, `footer`), sort by `order`.
- Render only `visibility !== "hidden"`.

3. [x] Use existing ContentRenderer primitive for block content
- Replace demo-only content showcase path for authored blocks.
- For `block.type === "content"` (and optionally `context` when `content_json` exists):
  - render `ContentRenderer` from `Page/primitives/ContentRenderer`.
  - pass `content={block.content_json}`.
- This directly enables code format + Shiki highlighting through existing renderer stack.

4. [x] Replace `panel.kind === "content"` implementation
- Current: `ContentRendererDemo compact` (showcase)
- Target: render authored panel payload:
  - `panel.options.content_json` -> `ContentRenderer`
  - fallback UI if missing/invalid payload.
- Keep existing typed panel options from generated client exports (no new model).

5. [x] Integrate blocks into DemoShell layout composition (without new schemas)
- File: `frontend/src/components/Demo/DemoShell.tsx`
- Extend props with optional block buckets already derived from composition:
  - `topBlocks`, `footerBlocks`, `primaryBlocks`, `auxBlocks` (or single `blocks` + grouped in shell).
- Render structure:
  - header
  - top blocks
  - main area (`DemoLayout` panels)
  - footer blocks
- Keep existing theme scopes (page/cards) intact.

6. [x] Keep panel sizing/positioning untouched
- Continue mapping `composition.panels` -> `DemoLayoutPanelConfig`
- Preserve `prominence`, `order`, `viewport_mode`, size constraints.
- This avoids regressions in existing panel control behavior.

7. [x] Validation/guardrails (runtime-safe)
- Add lightweight type guards before calling `ContentRenderer`:
  - ensure object has at least `format` + `value`.
- On invalid content payload:
  - render non-fatal warning card in panel/block.
- Do not throw route-level errors for malformed content.

8. [ ] QA coverage cases to verify immediately
- `content` block with `format: "code"` and `metadata.options.language/theme`.
- `context` block with markdown.
- `content` panel with JSON payload.
- mixed: top code block + story panel + chat panel.
- hidden block (`visibility: "hidden"`) not rendered.
- region ordering (`order`) respected.

9. Suggested execution order
1. [x] Implement content panel authored rendering (`panel.options.content_json`).
2. [x] Implement block grouping + rendering in route.
3. [x] Move block containers into DemoShell props/render.
4. [ ] Run TS build and smoke test 3 QA compositions.

This addresses both issues cohesively with existing `ResolveDemoEntryPayload`, `DemoBlockSpec`, `DemoPanelSpec`, and `ContentRenderer` primitives, without adding backend or schema models.
