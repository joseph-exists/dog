# ContentRenderer: Integrated Design & Technical Specification

> "The details are not the details. They make the design."
> — Charles Eames

This document synthesizes the **design specification** (collaborative decisions) and **technical specification** (MDX/Shiki/backend architecture) into a single, authoritative reference for implementing the ContentRenderer system.

---

## 1. Purpose & Scope

> "Have no fear of perfection—you'll never reach it."
> — Salvador Dalí

**What this system does:**
- Renders polymorphic content across formats: Text, Markdown, MDX, HTML, JSON, SVG, Image, Code (and future formats)
- Supports both static (build-time compiled) and dynamic (runtime compiled) content
- Integrates with FastAPI/PostgreSQL/Redis backend for storage, compilation, and caching
- Provides a secure, extensible plugin architecture

**What success looks like:**
- An author can use the StoryEditor to add these content types to a story
- A viewer/player can watch/play that story with smooth, well-designed rendering
- Exceptional user value, aligned with our quality standards

---

## 2. Content Format Taxonomy

> "Simplicity is the ultimate sophistication."
> — Leonardo da Vinci

### 2.1 The Enum (Backend Request SATISFIED)
** complete ** ContentFormat has been included to include all types listed.
use with 
```import type { ContentFormat } from "@/client"`` 

 ```export type ContentFormat = 'text' | 'html' | 'markdown' | 'json' | 'yaml' | 'mdx' | 'code' | 'svg' | 'image' | 'audio' | 'video' | 'empty' | 'unknown' | 'test';```


**Status:** ✅ Approved (design-spec Q2 follow-up). Backend request pending => BACKEND HAS DELIVERED.

### 2.2 The Frontend Type

```typescript
enum ContentFormat {
  Text = "text",
  Markdown = "markdown",
  MDX = "mdx",
  HTML = "html",
  JSON = "json",
  SVG = "svg",
  Image = "image",
  Code = "code",
  // Future: yaml, audio, video
  // Meta: empty, unknown, test
}
```

---

## 3. Core Content Model

> "Architecture is the learned game, correct and magnificent, of forms assembled in the light."
> — Le Corbusier

```typescript
interface Content<T extends ContentFormat = ContentFormat> {
  id?: string;                    // UUID from Postgres (optional for in-memory)
  format: T;
  value: ContentValue;            // string | unknown (for rich JSON)
  metadata?: ContentMetadata;
}

interface ContentMetadata {
  /** UX variant for rendering context */
  variant?: ContentVariant;
  /** Label or heading hint */
  label?: string;
  /** Source trust constraints */
  constraints?: {
    isTrustedSource: boolean;
    cacheKey?: string;            // Redis cache invalidation hint
  };
  /** Format-specific options */
  options?: FormatSpecificOptions;
}

type ContentValue = string | unknown;
```

### 3.1 UX Variants

```typescript
type ContentVariant =
  | "inline"      // Short snippet, no scroll, no headings
  | "card"        // Limited height, scrollable body
  | "page"        // Full layout, headings, TOC
  | "tooltip"     // Very small, truncated, hover dismissal
  | "preview"     // Medium size, read-only, animated entrance
  | "embed"       // Nested context, reduced chrome
  | "modal"       // Centered, backdrop, dismissible
  | "thumbnail"   // Fixed dimensions, cropped/scaled
  | "background"; // Layer behind other content (Use Case A)
```


---

## 4. Format-Specific Options

> "God is in the details."
> — Ludwig Mies van der Rohe

### 4.1 Code Format Options

```typescript
interface CodeContentOptions {
  /** Programming language for syntax highlighting */
  language?: string;          // "typescript", "python", "bash", etc.
  /** Show line numbers */
  lineNumbers?: boolean;
  /** Lines to visually highlight (1-indexed) */
  highlightLines?: number[];
  /** Start line number (for snippets) */
  startLine?: number;
  /** Show filename/title bar */
  filename?: string;
  /** Enable copy button */
  copyable?: boolean;
  /** Highlighting theme override */
  theme?: string;             // "github-dark", "ayu-dark", etc.
  /** Shiki transformers for advanced features */
  transformers?: ShikiTransformer[];
}
```

**Status:** ✅ All options included in v1.

### 4.2 Three Concepts Model

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    THREE CONCEPTS (Not Two)                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. VARIANT / ROLE (Positioning & Composition)                          │
│  ═══════════════════════════════════════════════                        │
│  WHERE and HOW content is positioned in the layout                      │
│  Lives at: Content.metadata.variant                                     │
│  Values: "inline" | "card" | "page" | "embed" | "background" | ...      │
│                                                                         │
│  Examples:                                                              │
│  - SVG as background layer (Use Case A)                                 │
│  - Codeblock embedded in markdown (Use Case B)                          │
│  - Image as hero banner vs thumbnail                                    │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  2. RENDER MODE (Format-Specific Technique)                             │
│  ══════════════════════════════════════════                             │
│  HOW the format-specific renderer produces output                       │
│  Lives at: Content.metadata.options.<format-specific>                   │
│                                                                         │
│  Examples:                                                              │
│  - SVG: inline=true (as <svg>) vs inline=false (as <img>)               │
│  - JSON: viewMode="tree" vs viewMode="text"                             │
│  - Code: lineNumbers=true, highlightLines=[3,5]                         │
│                                                                         │
│  Note: Variant MAY influence default render mode:                       │
│  - variant="inline" → Code defaults to lineNumbers=false                │
│  - variant="background" → SVG defaults to inline=true                   │
│  But explicit options ALWAYS override.                                  │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  3. THEME (Visual Style, Cascading)                                     │
│  ═══════════════════════════════════                                    │
│  WHAT colors, fonts, and decorations are applied                        │
│  Lives at: Multiple levels with cascade + override                      │
│                                                                         │
│  Cascade order (highest wins):                                          │
│  1. User per-element override (Shiki dropdown)                          │
│  2. Content.metadata.options.theme (author intent)                      │
│  3. ContentRenderer props.theme                                         │
│  4. Parent ThemeContext (page-level, user-controllable)                 │
│  5. System default                                                      │
│                                                                         │
│  Use Case D: User can control BOTH page cascade AND per-element         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Key behaviors:**
- Variant can provide **defaults** for render mode (e.g., `variant="background"` → SVG defaults to `inline=true`)
- Explicit options **always override** variant defaults
- Theme cascades from page level; user can override at page OR element level

### 4.3 Markdown Options

```typescript
interface MarkdownContentOptions {
  /** If true, no interactive elements (links, buttons) */
  readonly?: boolean;
}
```

### 4.4 MDX Options

```typescript
interface MDXContentOptions {
  /** If true, only whitelisted components allowed */
  restrictedComponents?: boolean;
  /** Component map for MDX rendering */
  components?: MDXComponents;
}
```

### 4.5 HTML Options

```typescript
interface HTMLContentOptions {
  /** If true, sanitize aggressively */
  sanitize?: boolean;
  /** DOMPurify-style config */
  sanitizerConfig?: unknown;
}
```

### 4.6 JSON Options

```typescript
interface JSONContentOptions {
  /** Render mode: formatted text or interactive tree */
  viewMode?: "text" | "tree";
  /** Enable expand/collapse for nested objects */
  interactive?: boolean;
}
```

### 4.7 SVG Options

```typescript
interface SVGContentOptions {
  /** If true, render as inline <svg>; otherwise, as <img> */
  inline?: boolean;
}
```

### 4.8 Image Options

```typescript
interface ImageContentOptions {
  alt?: string;
  width?: number;
  height?: number;
  loading?: "eager" | "lazy";
}
```

**Note:** Image URL normalization (external, data URI, blob, relative) deferred to implementation.

---

## 5. Syntax Highlighting Architecture

> "Any sufficiently advanced technology is indistinguishable from magic."
> — Arthur C. Clarke

### 5.1 Highlighting Engine: Shiki

Use **Shiki** (via `react-shiki`) as the highlighting engine.

**Why Shiki:**
1. Uses VS Code's TextMate grammars (same highlighting as editor)
2. Supports `transformers` for advanced features (diff highlighting, annotations)
3. Works at build-time AND runtime

**Status:** ✅ Included in v1 (load-bearing).

### 5.2 Highlighting Entry Points

```
┌─────────────────────────────────────────────────────────────┐
│                    ContentRenderer                          │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │ format: "code"  │  │ format: "markdown" / "mdx"         │
│  │       │         │  │       │                            │
│  │       ▼         │  │       ▼                            │
│  │  CodeRenderer   │  │  MarkdownRenderer / MDXRenderer    │
│  │       │         │  │       │                            │
│  │       ▼         │  │       ▼                            │
│  │  react-shiki    │  │  components.code → CodeHighlight   │
│  │                 │  │       │                            │
│  │                 │  │       ▼                            │
│  │                 │  │  react-shiki                       │
│  └─────────────────┘  └─────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

### 5.3 CodeHighlight Component Contract

```typescript
interface CodeHighlightProps {
  className?: string;           // May contain language hint (language-tsx)
  children?: ReactNode;         // Code content
  node?: Element;               // AST node from react-markdown
  options?: {
    language?: string;
    theme?: string;
    forceBlock?: boolean;       // Override inline detection
    copyable?: boolean;
    transformers?: ShikiTransformer[];
  };
  onRendered?: () => void;      // Callback when highlighting completes
}
```

---

## 6. MDX Lifecycle & Compilation

> "The best way to predict the future is to invent it."
> — Alan Kay

### 6.1 Two Paths

```
┌─────────────────────────────────────────────────────────────────────┐
│                     MDX COMPILATION PATHS                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  COMPILE-TIME (Backend-Compiled)                                    │
│  ════════════════════════════════                                   │
│  Author writes MDX                                                  │
│       │                                                             │
│       ▼                                                             │
│  Save → Backend compiles to JS → Stores compiled output             │
│       │                                                             │
│       ▼                                                             │
│  Viewer requests → Backend returns compiled JS                      │
│       │                                                             │
│       ▼                                                             │
│  Frontend hydrates/renders (no @mdx-js/runtime needed)              │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  RUNTIME (Frontend-Compiled)                                        │
│  ═══════════════════════════                                        │
│  Author writes MDX                                                  │
│       │                                                             │
│       ▼                                                             │
│  Save → Backend stores raw MDX                                      │
│       │                                                             │
│       ▼                                                             │
│  Viewer requests → Backend returns raw MDX                          │
│       │                                                             │
│       ▼                                                             │
│  Frontend lazy-loads @mdx-js/mdx → Compiles + renders               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 6.2 Frontend Toggle

```typescript
interface MDXRendererProps extends Content<ContentFormat.MDX> {
  /** Use backend-compiled MDX vs frontend runtime */
  useCompiledMDX?: boolean;
  /** Component map for MDX elements */
  components?: MDXComponents;
  /** Restrict to whitelisted components */
  restricted?: boolean;
  /** Sanitize content */
  safeMode?: boolean;
}
```

**Note:** Toggle (per-item or per-session).

### 6.3 MDXComponents Contract

```typescript
type MDXComponents = {
  // Standard elements
  h1: React.ComponentType<any>;
  h2: React.ComponentType<any>;
  h3: React.ComponentType<any>;
  p: React.ComponentType<any>;
  strong: React.ComponentType<any>;
  em: React.ComponentType<any>;
  ul: React.ComponentType<any>;
  ol: React.ComponentType<any>;
  li: React.ComponentType<any>;
  blockquote: React.ComponentType<any>;

  // Code integration (Shiki)
  code: React.ComponentType<CodeHighlightProps>;
  pre: React.ComponentType<React.PropsWithChildren<HTMLAttributes<HTMLPreElement>>>;

  // Custom components (whitelisted)
  [key: string]: React.ComponentType<any>;
};
```

### 6.4 Backend Work

**Status:** completed:

Frontend should expect:
- After `mdx` added to `ContentFormat` enum (done)
- API call to get content will return compiled MDX object when called.
- Raw MDX returned when requested as text.

---

## 7. Renderer Architecture

> "First, solve the problem. Then, write the code."
> — John Johnson

### 7.1 ContentRenderer Contract

```typescript
interface ContentRendererProps {
  content: Content;

  /** Custom renderer overrides */
  renderers?: Partial<RendererRegistry>;

  /** Safety mode (affects HTML/MDX sanitization) */
  safeMode?: boolean;

  /** UX variant override */
  variant?: ContentVariant;

  /** Fallback for unsupported formats */
  fallback?: React.FC<Content>;

  /** Theme integration */
  decorationHint?: "brutalist" | "ethereal" | string;
  theme?: ThemeConfig;
  overrides?: {
    typography?: Partial<TypographyConfig>;
    colors?: Partial<ColorConfig>;
  };
}
```

### 7.2 Theme Handling

**Resolution (design-spec Concern 2):**
- Accept theme from parent context providers
- Allow content object to override if specified
- `decorationHint` influences typography (brutalist → mono/uppercase, ethereal → serif/italic)

```
┌─────────────────────────────────────────────────┐
│              Theme Resolution                   │
├─────────────────────────────────────────────────┤
│  1. content.metadata.options.theme    (highest) │
│  2. ContentRenderer props.theme                 │
│  3. Parent ThemeContext                         │
│  4. Default theme                     (lowest)  │
└─────────────────────────────────────────────────┘
```

### 7.3 Renderer Registry

```typescript
interface Renderer<T extends ContentFormat> {
  format: T;
  Component: React.FC<ContentProps<T>>;
}

type RendererRegistry = {
  [K in ContentFormat]: Renderer<K>;
};
```

### 7.4 Format Dispatch

```
ContentRenderer receives content
       │
       ▼
┌──────────────────────────────────────────────────────────┐
│  switch(content.format)                                  │
├──────────────────────────────────────────────────────────┤
│  "text"     → TextRenderer                               │
│  "markdown" → MarkdownRenderer (react-markdown + Shiki)  │
│  "mdx"      → MDXRenderer (compiled or runtime)          │
│  "html"     → HTMLRenderer (DOMPurify when safeMode)     │
│  "json"     → JSONRenderer (text or tree mode)           │
│  "svg"      → SVGRenderer (inline or img, sanitized)     │
│  "image"    → ImageRenderer                              │
│  "code"     → CodeRenderer (react-shiki)                 │
│  unknown    → FallbackRenderer                           │
└──────────────────────────────────────────────────────────┘
```

---

## 8. Security & Trust Model

> "Security is not a product, but a process."
> — Bruce Schneier

### 8.1 Trust Levels

```typescript
enum ContentTrustLevel {
  /** No HTML, no JS; safe for anonymous user-generated content */
  None = "none",
  /** Can render HTML/MDX with configurable sanitization */
  Moderated = "moderated",
  /** Can render HTML/MDX with minimal sanitization */
  Trusted = "trusted",
}
```

### 8.2 Risky Features by Format

| Format | Risky Features |
|--------|----------------|
| Text | *none* |
| Markdown | *none* |
| MDX | jsx_components, inline_scripts, arbitrary_html |
| HTML | scripts, iframes, arbitrary_html |
| SVG | scripts, external_refs |
| Code | *none* |
| JSON | *none* |
| Image | tracking_pixels |

### 8.3 Security Policy Application

```
┌─────────────────────────────────────────────────────────────┐
│  IF safeMode: true OR trust = None/Moderated               │
│  ════════════════════════════════════════════               │
│  • MDX: restricted = true (whitelisted components only)     │
│  • HTML: sanitize via DOMPurify                             │
│  • SVG: sanitize OR render as <img> (no inline)             │
├─────────────────────────────────────────────────────────────┤
│  IF trust = Trusted                                         │
│  ═══════════════════                                        │
│  • MDX: full component set (still scoped to MDXComponents)  │
│  • HTML: minimal sanitization                               │
│  • SVG: inline allowed                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 9. File Structure & Location

> "A place for everything, and everything in its place."
> — Benjamin Franklin

### 9.1 Primary Implementation

Files created.  These are the only files currently approved for modification for Phase 1 of the plan.

```
@/components/Page/primitives/ContentRenderer/
├── index.ts                    # Public exports
├── ContentRenderer.tsx         # Main dispatcher
├── types.ts                    # Content, ContentFormat, etc.
├── registry.ts                 # RendererRegistry
├── renderers/
│   ├── TextRenderer.tsx
│   ├── MarkdownRenderer.tsx
│   ├── MDXRenderer.tsx
│   ├── HTMLRenderer.tsx
│   ├── JSONRenderer.tsx
│   ├── SVGRenderer.tsx
│   ├── ImageRenderer.tsx
│   └── CodeRenderer.tsx
├── components/
│   ├── CodeHighlight.tsx       # Shiki integration for MD/MDX
│   └── FallbackRenderer.tsx
└── hooks/
    ├── useThemeResolution.ts
    └── useMDXCompiler.ts       # Lazy-loaded runtime compiler
```

### 9.2 Common Re-export

```
@/components/Common/ContentRenderer/
├── index.ts                    # Re-exports from Page/primitives/
└── renderContent.ts            # Compatibility helper for migration
```

### 9.3 Import Pattern

```typescript
// For new code (preferred)
import { ContentRenderer } from "@/components/Common/ContentRenderer"

// For migration (legacy support)
import { renderContent } from "@/components/Common/ContentRenderer"
```

---

## 10. Plugin & Extensibility

> "Make it work, make it right, make it fast."
> — Kent Beck

### 10.1 Plugin Interface

```typescript
interface Plugin<
  T extends ContentFormat = ContentFormat,
  Props extends ContentProps<T> = ContentProps<T>
> {
  /** Unique plugin identifier */
  id: string;
  /** Renderers provided by this plugin */
  renderers: Partial<PluginRendererRegistry>;
  /** Optional content validator */
  validate?(content: Content): Error[] | null;
  /** Optional pre-render transform */
  transform?(content: Content): Content;
}

interface PluginRenderer<T extends ContentFormat> extends Renderer<T> {
  meta: {
    pluginId: string;
    label: string;
    priority?: number;    // Higher = preferred
  };
}
```

### 10.2 Shiki Transformers

```typescript
// Extensibility point for code enhancements
type ShikiTransformer = unknown; // From react-shiki ecosystem

// Example transformers:
// - Diff highlighting
// - Line annotations
// - Animated transitions (framer-motion)
```

---

## 11. Backend Integration

> "The best code is no code at all."
> — Jeff Atwood

### 11.1 Data Model

**Contract-first approach** (design contracts first, then align data shape):
- Backend exposes Content via API
- Frontend doesn't assume specific DB schema
- Use client SDK for API calls (auto-generated from OpenAPI)

### 11.2 Caching Strategy

```
┌─────────────────────────────────────────────────────────────┐
│                    Redis Caching                            │
├─────────────────────────────────────────────────────────────┤
│  Key Pattern              │  Value                          │
│  ─────────────────────────┼────────────────────────────────│
│  content:{id}:html        │  Pre-rendered HTML              │
│  content:{id}:mdx         │  Compiled MDX                   │
│  code:{id}:{theme}        │  Shiki-highlighted HTML         │
├─────────────────────────────────────────────────────────────┤
│  Invalidation: On content update (via updated_at or hook)  │
│  TTL: Configurable per content type                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 12. Error Handling

> "Expect the best, plan for the worst, and prepare to be surprised."
> — Denis Waitley

### 12.1 Strategy by Context

| Context | Behavior |
|---------|----------|
| **Preview (Authoring)** | Show error inline, don't block save |
| **Save** | Backend validates, returns errors |
| **Publish** | Strict validation, block if invalid |
| **Viewing** | Graceful degradation, fallback UI |

### 12.2 Error States

```typescript
// Each renderer handles its own errors gracefully
// - Markdown: Invalid syntax → render as plain text
// - JSON: Parse failure → show error message
// - Image: 404 → show placeholder
// - SVG: Malformed → show error or fallback to <img>
```

---

## 13. Loading & Performance

> "Premature optimization is the root of all evil."
> — Donald Knuth (but we still plan for it)

### 13.1 Strategy

- **Suspense boundaries:** Accept at renderer level
- **Skeleton loaders:** Prevent page jumps
- **Lazy loading:** MDX compiler, heavy images
- **Caching:** Redis backend + browser cache

### 13.2 Bundle Considerations

all installed in frontend environment, will be added to build-dependencies after proof of work.

| Module | Strategy |
|--------|----------|
| `@mdx-js/mdx` | Lazy-load only when runtime MDX needed |
| `react-shiki` | Include in main bundle (load-bearing) |
| `DOMPurify` | Include in main bundle (security critical) |

---

## 14. Implementation Phases

> "Rome wasn't built in a day, but they were laying bricks every hour."
> — John Heywood

### Phase 1: New Format Value Proof [X] COMPLETE

1. Create `@/components/Page/primitives/ContentRenderer/`
2. Implement core renderers:
   - Text (baseline)
   - Markdown (with Shiki syntax highlighting)
   - HTML (with DOMPurify, trust-level aware)
   - JSON (text + tree modes)
   - SVG (inline + img modes, sanitization toggle)
   - Image (URL handling evolves during implementation)
   - Code (full options: language, lineNumbers, highlightLines, startLine, filename, copyable)
3. Implement UX variants: inline, card, page, tooltip, preview, embed, modal, thumbnail, background
4. Wire theme/decorationHint props with parent context fallback
5. **Document** any paradigm conflicts for migration (per design-spec Q11 constraint)

### Phase 2: MDX Wiring [X] Complete

1. Add `MDX` to backend ContentFormat enum (request to backend team) [X - complete]
2. Implement MDX renderer with:
   - Compile-time path: hydrate backend-compiled JS
   - Runtime path: lazy-load `@mdx-js/mdx`, compile + render
   - Toggle:  `useCompiledMDX` 
3. Define MDXComponents whitelist - pending review

### Phase 3: Proving Ground [X] Complete

1. Demo page approach: Deferred until components ready (Josep has stub/mock frameworks)
2. Add ContentRenderer to StoryEditor (import from Page/)
3. Test all formats in authoring + viewing contexts
4. Validate success criteria:
   - Author can add content types in StoryEditor
   - Viewer can play story smoothly
   - Experience is well-designed and sophisticated

### Phase 4: Migration [X] Complete

1. Create `@/components/Common/ContentRenderer/` (re-exports)
2. Export `renderContent()` compatibility helper
3. Migrate: `StoryContent`, `StoryPreview`, `StoryPlayer`
4. Migrate: `Page/panels/StoryPanel/NodeDisplay`, `Room/panels/StoryPanel/NodeDisplay`

### Phase 5: Plugin System [ ] IMPLEMENTATION GUIDE READY

> **Implementation Guide:** `phase5-implementation-guide.md`

1. Formalize `Plugin<T>` interface
2. Add `PluginRenderer<T>` with metadata (pluginId, label, priority)
3. Create `pluginRegistry.ts` with:
   - `registerPlugin()` / `unregisterPlugin()` API
   - Priority-based renderer resolution
   - Transform and validation hooks
4. Wire transforms and validation in ContentRenderer
5. Document plugin authoring guide

---

## 15. Open Items & Unresolved Questions

> "The important thing is not to stop questioning."
> — Albert Einstein

| Item | Status | Notes |
|------|--------|-------|
| Image URL normalization | Deferred | Evolve during implementation |
| MDX toggle scope | Paused | Pending RBAC/trust system |
| Demo page | Deferred | Josep has stub/mock frameworks ready |
| Backend ContentFormat enum | Pending | Request to backend team needed |
| `hero` UX variant | Deferred | Not in v1 |

---

## 16. Decisions Summary

> "In the middle of difficulty lies opportunity."
> — Albert Einstein

| Decision | Resolution | Source |
|----------|------------|--------|
| Syntax highlighting engine | **Shiki** (not rehype-highlight) | tech-spec alignment |
| Syntax highlighting in v1 | **Yes** (load-bearing) | design-spec Q4 |
| UX variants in v1 | inline, card, page, tooltip, preview, embed, modal, thumbnail, background | design-spec C3 + Use Case A |
| Code options in v1 | **All** (language, lineNumbers, highlightLines, startLine, filename, copyable) | design-spec Concern 1 |
| Variant location | Content level (not format-specific) | design-spec vs tech-spec |
| Three concepts model | **Variant + RenderMode + Theme** (see 4.1.3) | Use cases A-D |
| Variant → RenderMode | Variant provides defaults; explicit options override | Use case B clarified |
| Theme cascade | Page → element, user can override both | Use case D |
| Theme handling | Parent context + content override | design-spec Concern 2 |
| File location | Page/primitives primary, Common/ re-export | design-spec Q1 |
| MDX runtime | **Must render** (not placeholder) | design-spec MDX follow-up |
| Priority | New formats first, then migration | design-spec Q11 |

---

## Appendix A: Type Definitions Summary

```typescript
// See sections 2-4 for full definitions
export {
  ContentFormat,
  Content,
  ContentMetadata,
  ContentVariant,
  ContentValue,
  ContentTrustLevel,
  CodeContentOptions,
  MarkdownContentOptions,
  MDXContentOptions,
  HTMLContentOptions,
  JSONContentOptions,
  SVGContentOptions,
  ImageContentOptions,
  Renderer,
  RendererRegistry,
  ContentRendererProps,
  CodeHighlightProps,
  MDXComponents,
  MDXRendererProps,
  Plugin,
  PluginRenderer,
};
```

---

## Appendix B: Quotation Index

| Section | Quote | Author |
|---------|-------|--------|
| 1 | "The details are not the details. They make the design." | Charles Eames |
| 2 | "Simplicity is the ultimate sophistication." | Leonardo da Vinci |
| 3 | "Architecture is the learned game..." | Le Corbusier |
| 4 | "God is in the details." | Mies van der Rohe |
| 5 | "Any sufficiently advanced technology..." | Arthur C. Clarke |
| 6 | "The best way to predict the future is to invent it." | Alan Kay |
| 7 | "First, solve the problem. Then, write the code." | John Johnson |
| 8 | "Security is not a product, but a process." | Bruce Schneier |
| 9 | "A place for everything..." | Benjamin Franklin |
| 10 | "Make it work, make it right, make it fast." | Kent Beck |
| 11 | "The best code is no code at all." | Jeff Atwood |
| 12 | "Expect the best, plan for the worst..." | Denis Waitley |
| 13 | "Premature optimization is the root of all evil." | Donald Knuth |
| 14 | "Rome wasn't built in a day..." | John Heywood |
| 15 | "The important thing is not to stop questioning." | Albert Einstein |
| 16 | "In the middle of difficulty lies opportunity." | Albert Einstein |

---

*This specification synthesizes `design-specification-content-renderer.md` and `content-renderer-technical-specification.md`. Last updated: 2024-02-14.*
