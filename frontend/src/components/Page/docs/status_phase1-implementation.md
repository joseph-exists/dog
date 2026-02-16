# Phase 1 Implementation Guide: ContentRenderer

> "First, solve the problem. Then, write the code."
> — John Johnson

This guide provides step-by-step status for Phase 1 of the ContentRenderer system, grounded in the integrated specification and scratchpad constraints.

---

## 1. Prerequisites Checklist

Before implementing, verify:

- [X] Backend has `ContentFormat` enum with all values (confirmed: text, html, markdown, json, yaml, mdx, code, svg, image, audio, video, empty, unknown, test)
- [X] Dependencies installed: `react-shiki`, `dompurify`, `react-markdown`
- [X] Stub files created at `@/components/Page/primitives/ContentRenderer/`

### 1.2 Stub Files to Remain as Stubs

These files exist as stubs but are Phase 2 scope:
- `hooks/useMDXCompiler.ts` - MDX runtime compilation (Phase 2)

### 1.3 react-shiki Import Verification

- [X] Complete.  reac6-shiki@0.9.1
Before implementing `CodeHighlight.tsx`, verify the exact export from `react-shiki`:

The guide assumes `ShikiHighlighter` but this may be `Highlighter`, `CodeBlock`, or a default export.

---

## 2. Implementation Order

Files must be implemented in this dependency order to avoid circular imports:

```
1. types.ts              ← Foundation: all type definitions
2. useThemeResolution.ts ← Hook used by all renderers
3. CodeHighlight.tsx     ← Shared component for code highlighting
4. FallbackRenderer.tsx  ← Catches unsupported formats
5. TextRenderer.tsx      ← Simplest renderer (baseline)
6. CodeRenderer.tsx      ← Uses CodeHighlight directly
7. HTMLRenderer.tsx      ← Uses DOMPurify
8. JSONRenderer.tsx      ← Two modes: text/tree
9. SVGRenderer.tsx       ← Two modes: inline/img
10. ImageRenderer.tsx    ← URL normalization evolves here
11. MarkdownRenderer.tsx ← Uses react-markdown + CodeHighlight
12. MDXRenderer.tsx      ← STUB ONLY for Phase 1 (Phase 2 scope)
13. registry.ts          ← Assembles all renderers
14. ContentRenderer.tsx  ← Main dispatcher
15. index.ts             ← Public exports
```

---

## 3. Scratchpad Constraints (Critical)

From `/Page/docs/scratchpad`:

| Constraint | Application |
|------------|-------------|
| Use exported client SDK | `import type { ContentFormat } from "@/client"` |
| Only modify approved files | Files listed in integrated-spec Section 9.1 |
| Don't use styles unless directed | Use Tailwind classes sparingly, rely on prose class |
| Use components from current directory | Import from `./components/` or `./renderers/` |
| Component imports via human | If needing ui/ components, request human to add import statement |

---

## 4. File-by-File Implementation

### 4.1 ContentRender/types.ts

**Purpose:** Single source of truth for all ContentRenderer types.

**Constraints:**
[x] - MUST import `ContentFormat` from `@/client` (not redefine)
[x] - MUST NOT duplicate backend enum values

[ ] Complete: Review requested
  - question: is ReactNode the right type to import here?

---

### 4.2 hooks/useThemeResolution.ts

**Purpose:** Resolves theme following the cascade order:
1. content.metadata.options.theme (highest)
2. ContentRenderer props.theme
3. Parent ThemeContext
4. Default theme (lowest)

[ ] Complete: Review requested

---

### 4.3 components/CodeHighlight.tsx

**Purpose:** Shiki integration for syntax highlighting. Used by:
- CodeRenderer (direct code blocks)
- MarkdownRenderer (fenced code blocks)
- MDXRenderer (Phase 2)

**Key behaviors:**
- Detect language from className (e.g., `language-typescript`)
- Respect theme from options or context
- Support copy button when `copyable: true`

[ ] complete, review requested

---

### 4.4 components/FallbackRenderer.tsx

**Purpose:** Graceful degradation for unsupported or unknown formats.

[ ] complete, review requested

---

### 4.5 renderers/TextRenderer.tsx

**Purpose:** Simplest renderer - plain text with whitespace preservation.

**Variant behaviors:**
- `inline`: Single line, truncated
- `card`/`page`: Preserve whitespace, scrollable
- `tooltip`: Truncated to 100 chars
- `background`: Not applicable (shows nothing)

[ ] Complete: review requested

---

### 4.6 renderers/CodeRenderer.tsx

**Purpose:** Standalone code blocks with full options support.

**Options support (all from CodeContentOptions):**
- language, lineNumbers, highlightLines, startLine, filename, copyable, theme

[ ] complete - review requested

TODO: 
**Note:** `lineNumbers`, `highlightLines`, `startLine` require Shiki transformer configuration. These can be wired in Phase 2 or via transformer props. Document this as a paradigm conflict for migration notes.

---

### 4.7 renderers/HTMLRenderer.tsx

**Purpose:** Render HTML with DOMPurify sanitization when `safeMode: true`.

[ ] complete: review requested

---

### 4.8 renderers/JSONRenderer.tsx

**Purpose:** JSON content with two view modes: text (formatted) or tree (interactive).

[ ] complete, review requested

---

### 4.9 renderers/SVGRenderer.tsx

**Purpose:** SVG with two modes: inline `<svg>` or `<img>` wrapper.

**Security:**
- `safeMode: true` → render as `<img>` (no script execution)
- `inline: true` + trusted → render as inline `<svg>`

[ ] complete, review requested

---

### 4.10 renderers/ImageRenderer.tsx

**Purpose:** Image rendering with URL normalization (evolving).

**URL types to handle:**
- External URLs (https://...)
- Data URIs (data:image/...)
- Blob URLs (blob:...)
- Relative paths (/images/...)

[ ] complete - review requested
---

### 4.11 renderers/MarkdownRenderer.tsx

**Purpose:** Markdown with react-markdown and Shiki code highlighting.

[ ] complete - review requested

---

### 4.12 renderers/MDXRenderer.tsx (STUB - Phase 2)

**Purpose:** Placeholder for Phase 2 MDX implementation.

[ ] complete: review requested

---

### 4.13 registry.ts

**Purpose:** Assembles all renderers into a registry for format dispatch.

[ ] complete, review requested

---

### 4.14 ContentRenderer.tsx

**Purpose:** Main dispatcher that routes to format-specific renderers.

**Key responsibilities:**
- Route to format-specific renderer from registry
- Resolve variant (props > content.metadata > default)
- Pass theme configuration through to child renderers
- Handle fallback for unknown formats

[ ] complete, requires review

**Note on decorationHint:** The `decorationHint` prop is accepted but not fully implemented in Phase 1. The spec indicates it should influence typography (brutalist → mono/uppercase, ethereal → serif/italic). This can be wired in useThemeResolution in Phase 2 or when the design system requires it.

---

### 4.15 index.ts

**Purpose:** Public API exports.

[ ] complete, review requested
---

## 5. Paradigm Conflicts for Migration

Document these for Phase 4 migration work:

| Conflict | Current Pattern | ContentRenderer Pattern | Resolution |
|----------|-----------------|------------------------|------------|
| Format dispatch | `switch(node.content_format)` in component | `ContentRenderer` with registry | Replace inline switch with `<ContentRenderer content={...} />` |
| Safe mode | Implicit (always sanitize) | Explicit `safeMode` prop | Default true, allow override for trusted content |
| Line numbers | Not implemented | `options.lineNumbers` → Shiki transformer | Requires Shiki transformer wiring (note in CodeRenderer) |
| Theme override | Hardcoded `github-dark` | `useThemeResolution` cascade | Authors can now set per-content theme |
| decorationHint | Not implemented | Accepted in props | Wire to typography in Phase 2 |

### 5.1 Known Type Limitations

The `Renderer` type uses `React.FC<ContentProps<T>>` but the registry stores them without full generic safety:

```typescript
// Registry loses format-specific type info
export const rendererRegistry: Partial<Record<ContentFormat, Renderer>> = {
  text: { format: "text", Component: TextRenderer },
  // TextRenderer is typed as ContentProps<"text"> but registry doesn't enforce
}
```

This is acceptable for Phase 1 because:
1. Each renderer validates its own content.format internally
2. The dispatcher routes correctly based on content.format
3. Full type safety can be added in Phase 5 (plugin system) if needed

---

## 6. Testing Strategy

### 6.1 Manual Testing Checklist

After implementation:

- [ ] Text format renders with whitespace preserved
- [ ] Markdown renders with Shiki syntax highlighting in code blocks
- [ ] HTML sanitizes content when `safeMode: true`
- [ ] JSON shows formatted output, handles parse errors gracefully
- [ ] SVG renders inline when `inline: true`, as img otherwise
- [ ] Image shows placeholder when src is empty
- [ ] Code blocks show syntax highlighting for known languages
- [ ] Unknown format shows FallbackRenderer
- [ ] Variant changes affect layout (inline vs card vs page)

### 6.2 Integration Points

These existing files will import ContentRenderer in Phase 4:
- `StoryPlayer.tsx:59-107` - Replace `renderContent()` function
- `StoryPreview.tsx:60-108` - Same pattern

---

## 7. Success Criteria (from Integrated Spec)

Phase 1 is complete when:

1. ✅ `@/components/Page/primitives/ContentRenderer/` exists with all files
2. ✅ Core renderers work: Text, Markdown, HTML, JSON, SVG, Image, Code
3. ✅ UX variants affect rendering: inline, card, page, tooltip, preview, embed, modal, thumbnail, background
4. ✅ Theme resolution follows cascade order
5. ✅ Paradigm conflicts documented for migration

---

## 8. Appendix: Import Dependencies

These must be available in the project:

```typescript
// From @/client (backend SDK)
import type { ContentFormat } from "@/client"

// From npm packages
import DOMPurify from "dompurify"
import ReactMarkdown from "react-markdown"
import { ShikiHighlighter } from "react-shiki"  // Verify exact export name

// From React
import { useMemo, useState } from "react"
import type { ReactNode } from "react"
```

If any import fails, **request human intervention** per scratchpad constraint.

---

## 9. Holistic Review: Coherence Analysis

This section documents the holistic review of how all pieces work together.

### 9.1 Data Flow

```
User calls:
  <ContentRenderer content={...} variant="card" theme={{codeTheme: "github-dark"}} />
       │
       ▼
ContentRenderer.tsx
  1. Resolves variant: props > content.metadata.variant > "card"
  2. Augments content with theme if needed (cascade)
  3. Looks up renderer from registry
  4. Renders: <Component content={...} variant={...} safeMode={...} />
       │
       ▼
Individual Renderer (e.g., MarkdownRenderer)
  1. Extracts value from content
  2. Calls useThemeResolution for theme cascade
  3. Renders format-specific output (react-markdown + CodeHighlight)
       │
       ▼
CodeHighlight (for code blocks)
  1. Detects language from className
  2. Decides inline vs block
  3. Calls react-shiki for highlighting
```

### 9.2 Theme Cascade Flow

```
Priority (highest first):
1. content.metadata.options.theme   ← Author intent
2. ContentRenderer props.theme      ← Page-level override
3. DEFAULT_CODE_THEME ("github-dark") ← System default

useThemeResolution() implements this cascade.
ContentRenderer augments content with props.theme if content doesn't specify.
```

### 9.3 Variant Propagation

All 9 variants are handled:
- `inline`: Truncated, single-line treatment
- `card`: Default, bounded height with scroll
- `page`: Full layout, headings enabled
- `tooltip`: Very compact, max 100 chars
- `preview`: Read-only, medium size
- `embed`: Reduced chrome
- `modal`: Centered, max viewport
- `thumbnail`: Fixed dimensions
- `background`: Absolute positioning, decorative

Each renderer implements variant-specific behavior where meaningful.

### 9.4 Security Model

```
safeMode: true (default)
  ├── HTML: DOMPurify sanitization
  ├── SVG: Rendered as <img> data URL (no script execution)
  └── MDX: Will use restricted components (Phase 2)

safeMode: false (requires trusted content)
  ├── HTML: Minimal sanitization
  ├── SVG: Can render inline with scripts
  └── MDX: Full component set (Phase 2)
```

### 9.5 Coherence Verification

| Aspect | Status | Notes |
|--------|--------|-------|
| types.ts imports from @/client | ✅ | Uses `ContentFormat` from SDK |
| All renderers use shared types | ✅ | Import from ../types |
| CodeHighlight reused across renderers | ✅ | MarkdownRenderer, CodeRenderer |
| Theme cascade implemented | ✅ | useThemeResolution hook |
| Variant affects all applicable renderers | ✅ | Each renderer checks variant |
| FallbackRenderer catches unknown formats | ✅ | Registry returns undefined → Fallback |
| Public API exports everything needed | ✅ | index.ts exports all components, types, hooks |



---

*Implementation guide for Phase 1. Aligned with integrated-spec.md and scratchpad constraints. Holistically reviewed for coherence.*
