# Composition G Quick Mode (1-Page)

Audience: UX, QA, Product, and stakeholders who want a fast, low-jargon review path.

Goal: decide quickly if Composition G is visually and functionally "working as intended."

## Start Here

1. Open Demo Builder.
2. Load template: `Composition G: UX Style Matrix Review`.
3. Make sure a story is attached (`story_id` set).
4. Turn on preview.
5. Use the checks below and mark each: `Pass`, `Partial`, or `Fail`.

## Quick Checks

### 1) Overall look

- The page has a clear styled background (not plain default).
- The page looks intentionally themed, not random or mixed.
- The visual hierarchy is clear (important areas stand out).

### 2) Panels (main workspace sections)

- Story Runtime panel has a visible header accent/overlay.
- Chat panel looks denser/compact than default when configured.
- Participant panel styling is visibly different from default.
- Debug panel appears smaller-text/utility-like.

### 3) Blocks (content cards around/under panels)

- Top blocks are visually distinct and readable.
- Runtime-focused blocks (`Story Metadata`, `Orchestrator State`, `Tool Capability`, `Contribution Feed`) show style cues and callouts.
- Contribution Feed rows show highlight styling.
- Footer blocks (Git/File Explorer) still look consistent with the theme.

### 4) Motion

- Enter animations feel smooth (not jarring or broken).
- Motion is visible but not distracting.
- Different regions can feel slightly different without looking inconsistent.

### 5) Readability and usability

- Text is readable everywhere (contrast and sizing are acceptable).
- Decorative effects do not block important information.
- Styled state still feels usable for real demo tasks.

## If Something Looks Wrong

Capture:
- which panel/block
- what you expected
- what actually happened
- screenshot/video

Use this short report format:

```md
Area: <panel/block/global>
Expected: <one sentence>
Actual: <one sentence>
Result: Pass | Partial | Fail
Evidence: <link>
```

## Common Questions

### "How do I change animation?"

Use motion settings in `presentation_json.motion` (for example enter timing/easing).

### "How do I change exact size/shape?"

- Size/layout: panel layout fields (`default_size`, `min_size`, `max_size`, `prominence`).
- Visual shape/look: `presentation_json` (overlays, backgrounds, effects, typography).

### "Where do I learn the terms?"

See glossary:
`frontend/src/components/Demo/demo-docs/demo-testing-references/demo-builder-style-glossary.md`
