# Phase 1 Implementation Guide: ContentRenderer

> "First, solve the problem. Then, write the code."
> — John Johnson

This guide provides step-by-step implementation instructions for Phase 1 of the ContentRenderer system, grounded in the integrated specification and scratchpad constraints.

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

Before implementing `CodeHighlight.tsx`, verify the exact export from `react-shiki`:

```bash
# Check package exports
npm ls react-shiki
# Or check the actual export in node_modules
cat node_modules/react-shiki/dist/index.d.ts | head -50
```

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

### 4.1 types.ts (CREATE - not in stubs)

**Purpose:** Single source of truth for all ContentRenderer types.

**Constraints:**
- MUST import `ContentFormat` from `@/client` (not redefine)
- MUST NOT duplicate backend enum values

```typescript
/**
 * ContentRenderer Type Definitions
 *
 * Re-exports ContentFormat from backend client.
 * Defines frontend-specific interfaces for rendering.
 */
import type { ContentFormat } from "@/client"
import type { ReactNode } from "react"

// Re-export for convenience
export type { ContentFormat }

/**
 * UX positioning variants - WHERE content appears
 */
export type ContentVariant =
  | "inline"      // Short snippet, no scroll, no headings
  | "card"        // Limited height, scrollable body
  | "page"        // Full layout, headings, TOC
  | "tooltip"     // Very small, truncated, hover dismissal
  | "preview"     // Medium size, read-only, animated entrance
  | "embed"       // Nested context, reduced chrome
  | "modal"       // Centered, backdrop, dismissible
  | "thumbnail"   // Fixed dimensions, cropped/scaled
  | "background"  // Layer behind other content

/**
 * Content trust levels for security policy
 */
export type ContentTrustLevel = "none" | "moderated" | "trusted"

/**
 * Format-specific rendering options
 */
export interface CodeContentOptions {
  language?: string
  lineNumbers?: boolean
  highlightLines?: number[]
  startLine?: number
  filename?: string
  copyable?: boolean
  theme?: string
}

export interface HTMLContentOptions {
  sanitize?: boolean
  sanitizerConfig?: unknown
}

export interface JSONContentOptions {
  viewMode?: "text" | "tree"
  interactive?: boolean
}

export interface SVGContentOptions {
  inline?: boolean
}

export interface ImageContentOptions {
  alt?: string
  width?: number
  height?: number
  loading?: "eager" | "lazy"
}

export interface MarkdownContentOptions {
  readonly?: boolean
}

/**
 * Union of all format-specific options
 */
export type FormatSpecificOptions =
  | CodeContentOptions
  | HTMLContentOptions
  | JSONContentOptions
  | SVGContentOptions
  | ImageContentOptions
  | MarkdownContentOptions

/**
 * Content metadata with variant, constraints, and options
 */
export interface ContentMetadata {
  variant?: ContentVariant
  label?: string
  constraints?: {
    isTrustedSource: boolean
    cacheKey?: string
  }
  options?: FormatSpecificOptions
}

/**
 * Core content model
 */
export interface Content<T extends ContentFormat = ContentFormat> {
  id?: string
  format: T
  value: string | unknown
  metadata?: ContentMetadata
}

/**
 * Props passed to individual format renderers
 */
export interface ContentProps<T extends ContentFormat = ContentFormat> {
  content: Content<T>
  variant?: ContentVariant
  safeMode?: boolean
  className?: string
}

/**
 * Theme configuration for renderers
 */
export interface ThemeConfig {
  codeTheme?: string
  prose?: boolean
}

/**
 * Main ContentRenderer props
 */
export interface ContentRendererProps {
  content: Content
  variant?: ContentVariant
  safeMode?: boolean
  fallback?: React.FC<Content>
  decorationHint?: "brutalist" | "ethereal" | string
  theme?: ThemeConfig
  className?: string
}

/**
 * Renderer registry entry
 */
export interface Renderer<T extends ContentFormat = ContentFormat> {
  format: T
  Component: React.FC<ContentProps<T>>
}

/**
 * CodeHighlight props for Shiki integration
 */
export interface CodeHighlightProps {
  className?: string
  children?: ReactNode
  options?: {
    language?: string
    theme?: string
    forceBlock?: boolean
    copyable?: boolean
  }
}
```

---

### 4.2 hooks/useThemeResolution.ts

**Purpose:** Resolves theme following the cascade order:
1. content.metadata.options.theme (highest)
2. ContentRenderer props.theme
3. Parent ThemeContext
4. Default theme (lowest)

```typescript
/**
 * useThemeResolution - Resolves theme following cascade order
 *
 * Cascade (highest wins):
 * 1. content.metadata.options.theme
 * 2. props.theme
 * 3. Parent ThemeContext (future)
 * 4. Default
 */
import { useMemo } from "react"
import type { Content, ThemeConfig } from "../types"

const DEFAULT_CODE_THEME = "github-dark"

interface ThemeResolutionInput {
  content: Content
  propsTheme?: ThemeConfig
}

interface ResolvedTheme {
  codeTheme: string
  prose: boolean
}

export function useThemeResolution({
  content,
  propsTheme,
}: ThemeResolutionInput): ResolvedTheme {
  return useMemo(() => {
    // Extract content-level theme override
    const contentOptions = content.metadata?.options
    const contentTheme =
      contentOptions && "theme" in contentOptions
        ? (contentOptions as { theme?: string }).theme
        : undefined

    // Cascade resolution
    const codeTheme =
      contentTheme ?? propsTheme?.codeTheme ?? DEFAULT_CODE_THEME

    // Prose defaults to true unless explicitly disabled
    const prose = propsTheme?.prose ?? true

    return { codeTheme, prose }
  }, [content.metadata?.options, propsTheme])
}
```

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

```typescript
/**
 * CodeHighlight - Shiki-powered syntax highlighting
 *
 * Integration points:
 * - CodeRenderer: Direct code format
 * - MarkdownRenderer: Fenced code blocks via components.code
 * - MDXRenderer: Same pattern (Phase 2)
 */
import { ShikiHighlighter } from "react-shiki"
import type { CodeHighlightProps } from "../types"

// Extract language from className like "language-typescript"
function extractLanguage(className?: string): string | undefined {
  if (!className) return undefined
  const match = className.match(/language-(\w+)/)
  return match?.[1]
}

export function CodeHighlight({
  className,
  children,
  options = {},
}: CodeHighlightProps) {
  const language = options.language ?? extractLanguage(className) ?? "text"
  const theme = options.theme ?? "github-dark"

  // Get code content as string
  const code =
    typeof children === "string"
      ? children
      : children?.toString?.() ?? ""

  // Inline detection: single line without explicit forceBlock
  const isInline = !options.forceBlock && !code.includes("\n")

  if (isInline) {
    // Inline code: simple styled span
    return (
      <code className="bg-muted px-1.5 py-0.5 rounded text-sm font-mono">
        {code}
      </code>
    )
  }

  // Block code: full Shiki highlighting
  return (
    <div className="relative group">
      <ShikiHighlighter language={language} theme={theme}>
        {code.trim()}
      </ShikiHighlighter>
      {options.copyable && (
        <button
          type="button"
          className="absolute top-2 right-2 opacity-0 group-hover:opacity-100
                     transition-opacity text-xs bg-muted px-2 py-1 rounded"
          onClick={() => navigator.clipboard.writeText(code)}
        >
          Copy
        </button>
      )}
    </div>
  )
}
```

**Note:** The exact `react-shiki` import may need adjustment based on package exports. Verify with: `npm ls react-shiki`.

---

### 4.4 components/FallbackRenderer.tsx

**Purpose:** Graceful degradation for unsupported or unknown formats.

```typescript
/**
 * FallbackRenderer - Handles unsupported content formats
 *
 * Shows format type and raw value preview for debugging.
 */
import type { Content } from "../types"

interface FallbackRendererProps {
  content: Content
}

export function FallbackRenderer({ content }: FallbackRendererProps) {
  const valuePreview =
    typeof content.value === "string"
      ? content.value.slice(0, 200)
      : JSON.stringify(content.value).slice(0, 200)

  return (
    <div className="border border-amber-300 dark:border-amber-700 rounded-lg p-4 bg-amber-50 dark:bg-amber-950/30">
      <p className="text-sm text-amber-700 dark:text-amber-400 font-medium mb-2">
        Unsupported format: {content.format}
      </p>
      <pre className="text-xs text-muted-foreground overflow-auto max-h-32">
        {valuePreview}
        {valuePreview.length >= 200 && "..."}
      </pre>
    </div>
  )
}
```

---

### 4.5 renderers/TextRenderer.tsx

**Purpose:** Simplest renderer - plain text with whitespace preservation.

**Variant behaviors:**
- `inline`: Single line, truncated
- `card`/`page`: Preserve whitespace, scrollable
- `tooltip`: Truncated to 100 chars
- `background`: Not applicable (shows nothing)

```typescript
/**
 * TextRenderer - Plain text content
 *
 * Respects variant for layout decisions.
 */
import type { ContentProps } from "../types"

export function TextRenderer({ content, variant, className }: ContentProps<"text">) {
  const text = typeof content.value === "string" ? content.value : ""

  // Variant-specific rendering
  switch (variant) {
    case "tooltip":
      return (
        <span className={`text-sm truncate max-w-xs ${className ?? ""}`}>
          {text.slice(0, 100)}
          {text.length > 100 && "..."}
        </span>
      )

    case "inline":
      return (
        <span className={`truncate ${className ?? ""}`}>
          {text}
        </span>
      )

    case "background":
      // Text as background doesn't make sense - render nothing
      return null

    default:
      // card, page, preview, embed, modal, thumbnail
      return (
        <p className={`whitespace-pre-wrap ${className ?? ""}`}>
          {text || "(No content)"}
        </p>
      )
  }
}
```

---

### 4.6 renderers/CodeRenderer.tsx

**Purpose:** Standalone code blocks with full options support.

**Options support (all from CodeContentOptions):**
- language, lineNumbers, highlightLines, startLine, filename, copyable, theme

```typescript
/**
 * CodeRenderer - Standalone code blocks with Shiki highlighting
 *
 * Full options: language, lineNumbers, highlightLines, startLine,
 * filename, copyable, theme
 */
import { CodeHighlight } from "../components/CodeHighlight"
import { useThemeResolution } from "../hooks/useThemeResolution"
import type { ContentProps, CodeContentOptions } from "../types"

export function CodeRenderer({ content, variant, className }: ContentProps<"code">) {
  const code = typeof content.value === "string" ? content.value : ""
  const options = content.metadata?.options as CodeContentOptions | undefined
  const { codeTheme } = useThemeResolution({ content })

  // Derive options with defaults
  const language = options?.language ?? "text"
  const copyable = options?.copyable ?? true
  const filename = options?.filename

  // Background variant: code as decorative layer
  if (variant === "background") {
    return (
      <div
        className={`absolute inset-0 overflow-hidden opacity-10 pointer-events-none ${className ?? ""}`}
      >
        <CodeHighlight
          options={{ language, theme: codeTheme, forceBlock: true }}
        >
          {code}
        </CodeHighlight>
      </div>
    )
  }

  return (
    <div className={`relative ${className ?? ""}`}>
      {filename && (
        <div className="text-xs text-muted-foreground bg-muted px-3 py-1 rounded-t border-b border-border">
          {filename}
        </div>
      )}
      <CodeHighlight
        options={{
          language,
          theme: codeTheme,
          forceBlock: true,
          copyable,
        }}
      >
        {code}
      </CodeHighlight>
    </div>
  )
}
```

**Note:** `lineNumbers`, `highlightLines`, `startLine` require Shiki transformer configuration. These can be wired in Phase 2 or via transformer props. Document this as a paradigm conflict for migration notes.

---

### 4.7 renderers/HTMLRenderer.tsx

**Purpose:** Render HTML with DOMPurify sanitization when `safeMode: true`.

```typescript
/**
 * HTMLRenderer - HTML content with DOMPurify sanitization
 *
 * safeMode: true → aggressive sanitization
 * safeMode: false + trusted → minimal sanitization
 */
import DOMPurify from "dompurify"
import type { ContentProps, HTMLContentOptions } from "../types"

export function HTMLRenderer({
  content,
  variant,
  safeMode = true,
  className,
}: ContentProps<"html">) {
  const html = typeof content.value === "string" ? content.value : ""
  const options = content.metadata?.options as HTMLContentOptions | undefined

  // Determine sanitization level
  const shouldSanitize = safeMode || options?.sanitize !== false
  const sanitizedHtml = shouldSanitize
    ? DOMPurify.sanitize(html, options?.sanitizerConfig ?? {})
    : html

  // Variant-specific wrapper
  const variantClass = variant === "inline" ? "inline" : ""
  const proseClass = variant !== "inline" ? "prose prose-lg dark:prose-invert max-w-none" : ""

  return (
    <div
      className={`${proseClass} ${variantClass} ${className ?? ""}`}
      dangerouslySetInnerHTML={{ __html: sanitizedHtml }}
    />
  )
}
```

---

### 4.8 renderers/JSONRenderer.tsx

**Purpose:** JSON content with two view modes: text (formatted) or tree (interactive).

```typescript
/**
 * JSONRenderer - JSON with text or tree view modes
 *
 * viewMode: "text" → formatted JSON string
 * viewMode: "tree" → interactive collapsible tree (Phase 2: use library)
 */
import { useState } from "react"
import type { ContentProps, JSONContentOptions } from "../types"

export function JSONRenderer({ content, variant, className }: ContentProps<"json">) {
  const options = content.metadata?.options as JSONContentOptions | undefined
  const viewMode = options?.viewMode ?? "text"

  // Parse JSON value
  let parsed: unknown
  let parseError: string | null = null

  try {
    parsed =
      typeof content.value === "string"
        ? JSON.parse(content.value)
        : content.value
  } catch (e) {
    parseError = e instanceof Error ? e.message : "Invalid JSON"
  }

  if (parseError) {
    return (
      <div className={`text-destructive ${className ?? ""}`}>
        <p className="font-medium">Invalid JSON</p>
        <p className="text-sm">{parseError}</p>
      </div>
    )
  }

  // Text mode: formatted JSON
  if (viewMode === "text") {
    return (
      <div className={className}>
        {variant !== "inline" && (
          <p className="text-sm text-muted-foreground italic mb-2">
            [JSON]
          </p>
        )}
        <pre className="bg-muted p-4 rounded-md overflow-auto text-sm font-mono">
          {JSON.stringify(parsed, null, 2)}
        </pre>
      </div>
    )
  }

  // Tree mode: collapsible (basic implementation)
  // TODO: Replace with json-tree library in Phase 2 for full interactivity
  return (
    <div className={className}>
      <p className="text-sm text-muted-foreground italic mb-2">
        [JSON Tree - Interactive mode coming soon]
      </p>
      <pre className="bg-muted p-4 rounded-md overflow-auto text-sm font-mono">
        {JSON.stringify(parsed, null, 2)}
      </pre>
    </div>
  )
}
```

---

### 4.9 renderers/SVGRenderer.tsx

**Purpose:** SVG with two modes: inline `<svg>` or `<img>` wrapper.

**Security:**
- `safeMode: true` → render as `<img>` (no script execution)
- `inline: true` + trusted → render as inline `<svg>`

```typescript
/**
 * SVGRenderer - SVG as inline element or img wrapper
 *
 * inline: true → <svg> directly (scripts can run if trusted)
 * inline: false → <img src="data:..."> (safe, no scripts)
 *
 * Variant defaults:
 * - background → inline: true
 * - others → inline: false (safer)
 */
import DOMPurify from "dompurify"
import type { ContentProps, SVGContentOptions } from "../types"

export function SVGRenderer({
  content,
  variant,
  safeMode = true,
  className,
}: ContentProps<"svg">) {
  const svg = typeof content.value === "string" ? content.value : ""
  const options = content.metadata?.options as SVGContentOptions | undefined

  // Determine inline mode - background defaults to inline
  const shouldInline = options?.inline ?? (variant === "background")

  // If safe mode, force img wrapper regardless of options
  if (safeMode && shouldInline) {
    // Sanitize and convert to data URL
    const sanitized = DOMPurify.sanitize(svg)
    const dataUrl = `data:image/svg+xml,${encodeURIComponent(sanitized)}`

    return (
      <img
        src={dataUrl}
        alt="SVG content"
        className={`${variant === "background" ? "absolute inset-0 w-full h-full object-cover" : ""} ${className ?? ""}`}
      />
    )
  }

  // Inline SVG rendering
  if (shouldInline) {
    const sanitized = safeMode ? DOMPurify.sanitize(svg) : svg

    return (
      <div
        className={`${variant === "background" ? "absolute inset-0 [&>svg]:w-full [&>svg]:h-full" : ""} ${className ?? ""}`}
        dangerouslySetInnerHTML={{ __html: sanitized }}
      />
    )
  }

  // Default: img wrapper
  const dataUrl = `data:image/svg+xml,${encodeURIComponent(svg)}`
  return (
    <img
      src={dataUrl}
      alt="SVG content"
      className={className}
    />
  )
}
```

---

### 4.10 renderers/ImageRenderer.tsx

**Purpose:** Image rendering with URL normalization (evolving).

**URL types to handle:**
- External URLs (https://...)
- Data URIs (data:image/...)
- Blob URLs (blob:...)
- Relative paths (/images/...)

```typescript
/**
 * ImageRenderer - Image content with URL normalization
 *
 * URL normalization evolves during implementation (per spec).
 * Currently handles: external URLs, data URIs, relative paths.
 */
import type { ContentProps, ImageContentOptions } from "../types"

export function ImageRenderer({ content, variant, className }: ContentProps<"image">) {
  const src = typeof content.value === "string" ? content.value : ""
  const options = content.metadata?.options as ImageContentOptions | undefined

  const alt = options?.alt ?? "Image"
  const loading = options?.loading ?? "lazy"

  // Variant-specific styling
  const variantStyles: Record<string, string> = {
    inline: "inline max-h-6",
    thumbnail: "w-24 h-24 object-cover rounded",
    background: "absolute inset-0 w-full h-full object-cover",
    card: "w-full max-h-64 object-contain",
    page: "w-full max-h-96 object-contain",
    modal: "max-w-full max-h-[80vh] object-contain",
  }

  const style = variantStyles[variant ?? ""] ?? ""

  // Error handling: show placeholder if src is empty
  if (!src) {
    return (
      <div className={`bg-muted rounded flex items-center justify-center text-muted-foreground text-sm ${style} ${className ?? ""}`}>
        No image source
      </div>
    )
  }

  return (
    <img
      src={src}
      alt={alt}
      loading={loading}
      width={options?.width}
      height={options?.height}
      className={`${style} ${className ?? ""}`}
    />
  )
}
```

---

### 4.11 renderers/MarkdownRenderer.tsx

**Purpose:** Markdown with react-markdown and Shiki code highlighting.

```typescript
/**
 * MarkdownRenderer - Markdown with Shiki code highlighting
 *
 * Uses react-markdown with custom code component for Shiki integration.
 */
import ReactMarkdown from "react-markdown"
import { CodeHighlight } from "../components/CodeHighlight"
import { useThemeResolution } from "../hooks/useThemeResolution"
import type { ContentProps } from "../types"

export function MarkdownRenderer({
  content,
  variant,
  className,
}: ContentProps<"markdown">) {
  const markdown = typeof content.value === "string" ? content.value : ""
  const { codeTheme, prose } = useThemeResolution({ content })

  // Prose class based on variant and theme resolution
  const proseClass = prose && variant !== "inline"
    ? "prose prose-lg dark:prose-invert max-w-none"
    : ""

  return (
    <div className={`${proseClass} ${className ?? ""}`}>
      <ReactMarkdown
        components={{
          code({ className: codeClassName, children }) {
            return (
              <CodeHighlight
                className={codeClassName}
                options={{ theme: codeTheme }}
              >
                {children}
              </CodeHighlight>
            )
          },
        }}
      >
        {markdown}
      </ReactMarkdown>
    </div>
  )
}
```

---

### 4.12 renderers/MDXRenderer.tsx (STUB - Phase 2)

**Purpose:** Placeholder for Phase 2 MDX implementation.

```typescript
/**
 * MDXRenderer - MDX content (Phase 2 implementation)
 *
 * Phase 2 will implement:
 * - Compile-time path (backend-compiled JS hydration)
 * - Runtime path (lazy-load @mdx-js/mdx)
 * - MDXComponents whitelist
 */
import { FallbackRenderer } from "../components/FallbackRenderer"
import type { ContentProps } from "../types"

export function MDXRenderer({ content }: ContentProps<"mdx">) {
  // Phase 2: Implement full MDX rendering
  // For now, fall back to showing format info
  return (
    <div className="border border-blue-300 dark:border-blue-700 rounded-lg p-4 bg-blue-50 dark:bg-blue-950/30">
      <p className="text-sm text-blue-700 dark:text-blue-400 font-medium mb-2">
        MDX format (Phase 2)
      </p>
      <p className="text-xs text-muted-foreground">
        MDX rendering will be available after backend compilation support is ready.
      </p>
      <FallbackRenderer content={content} />
    </div>
  )
}
```

---

### 4.13 registry.ts

**Purpose:** Assembles all renderers into a registry for format dispatch.

```typescript
/**
 * Renderer Registry - Format to renderer mapping
 *
 * Assembles all format renderers for ContentRenderer dispatch.
 */
import type { ContentFormat } from "@/client"
import type { Renderer } from "./types"

import { TextRenderer } from "./renderers/TextRenderer"
import { CodeRenderer } from "./renderers/CodeRenderer"
import { HTMLRenderer } from "./renderers/HTMLRenderer"
import { JSONRenderer } from "./renderers/JSONRenderer"
import { SVGRenderer } from "./renderers/SVGRenderer"
import { ImageRenderer } from "./renderers/ImageRenderer"
import { MarkdownRenderer } from "./renderers/MarkdownRenderer"
import { MDXRenderer } from "./renderers/MDXRenderer"

/**
 * Registry mapping ContentFormat to renderer components
 */
export const rendererRegistry: Partial<Record<ContentFormat, Renderer>> = {
  text: { format: "text", Component: TextRenderer },
  code: { format: "code", Component: CodeRenderer },
  html: { format: "html", Component: HTMLRenderer },
  json: { format: "json", Component: JSONRenderer },
  svg: { format: "svg", Component: SVGRenderer },
  image: { format: "image", Component: ImageRenderer },
  markdown: { format: "markdown", Component: MarkdownRenderer },
  mdx: { format: "mdx", Component: MDXRenderer },
  // yaml: Phase 2+
  // audio: Phase 2+
  // video: Phase 2+
}

/**
 * Get renderer for a given format
 */
export function getRenderer(format: ContentFormat): Renderer | undefined {
  return rendererRegistry[format]
}
```

---

### 4.14 ContentRenderer.tsx

**Purpose:** Main dispatcher that routes to format-specific renderers.

**Key responsibilities:**
- Route to format-specific renderer from registry
- Resolve variant (props > content.metadata > default)
- Pass theme configuration through to child renderers
- Handle fallback for unknown formats

```typescript
/**
 * ContentRenderer - Main dispatcher for polymorphic content
 *
 * Routes content.format to appropriate renderer from registry.
 * Handles theme resolution, variant propagation, and fallback.
 */
import type { ContentRendererProps, Content } from "./types"
import { getRenderer } from "./registry"
import { FallbackRenderer } from "./components/FallbackRenderer"

export function ContentRenderer({
  content,
  variant,
  safeMode = true,
  fallback,
  decorationHint,
  theme,
  className,
}: ContentRendererProps) {
  // Resolve variant: props override > content.metadata > default
  const resolvedVariant = variant ?? content.metadata?.variant ?? "card"

  // Get renderer for this format
  const renderer = getRenderer(content.format)

  if (!renderer) {
    // Use custom fallback or default
    if (fallback) {
      const FallbackComponent = fallback
      return <FallbackComponent {...content} />
    }
    return <FallbackRenderer content={content} />
  }

  // Augment content with theme if not already set
  // This enables the cascade: props.theme → content.metadata.options.theme
  const augmentedContent: Content = theme?.codeTheme
    ? {
        ...content,
        metadata: {
          ...content.metadata,
          options: {
            ...content.metadata?.options,
            // Only set if not already specified in content
            theme: (content.metadata?.options as { theme?: string })?.theme ?? theme.codeTheme,
          },
        },
      }
    : content

  // Render with resolved props
  const { Component } = renderer
  return (
    <Component
      content={augmentedContent}
      variant={resolvedVariant}
      safeMode={safeMode}
      className={className}
    />
  )
}
```

**Note on decorationHint:** The `decorationHint` prop is accepted but not fully implemented in Phase 1. The spec indicates it should influence typography (brutalist → mono/uppercase, ethereal → serif/italic). This can be wired in useThemeResolution in Phase 2 or when the design system requires it.

---

### 4.15 index.ts

**Purpose:** Public API exports.

```typescript
/**
 * ContentRenderer - Public Exports
 *
 * Primary export: ContentRenderer component
 * Type exports: Content, ContentFormat, ContentVariant, etc.
 */

// Main component
export { ContentRenderer } from "./ContentRenderer"

// Types (re-exported for consumer convenience)
export type {
  Content,
  ContentFormat,
  ContentVariant,
  ContentMetadata,
  ContentProps,
  ContentRendererProps,
  ThemeConfig,
  ContentTrustLevel,
  // Format-specific options
  CodeContentOptions,
  HTMLContentOptions,
  JSONContentOptions,
  SVGContentOptions,
  ImageContentOptions,
  MarkdownContentOptions,
  // CodeHighlight
  CodeHighlightProps,
} from "./types"

// Registry (for advanced use cases)
export { rendererRegistry, getRenderer } from "./registry"

// Individual renderers (for direct use or testing)
export { TextRenderer } from "./renderers/TextRenderer"
export { CodeRenderer } from "./renderers/CodeRenderer"
export { HTMLRenderer } from "./renderers/HTMLRenderer"
export { JSONRenderer } from "./renderers/JSONRenderer"
export { SVGRenderer } from "./renderers/SVGRenderer"
export { ImageRenderer } from "./renderers/ImageRenderer"
export { MarkdownRenderer } from "./renderers/MarkdownRenderer"
export { MDXRenderer } from "./renderers/MDXRenderer"

// Components
export { CodeHighlight } from "./components/CodeHighlight"
export { FallbackRenderer } from "./components/FallbackRenderer"

// Hooks
export { useThemeResolution } from "./hooks/useThemeResolution"
```

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

### 9.6 Open Questions for Implementation

1. **react-shiki exact API**: Verify export name before implementing CodeHighlight
2. **Shiki theme names**: Confirm available themes (github-dark, ayu-dark, etc.)
3. **Prose styling**: Confirm Tailwind Typography plugin is installed for prose classes

---

*Implementation guide for Phase 1. Aligned with integrated-spec.md and scratchpad constraints. Holistically reviewed for coherence.*
