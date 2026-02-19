# Phase 2 Implementation Guide: MDX Wiring & Shiki Transformers

> "The best way to predict the future is to invent it."
> — Alan Kay

This guide provides step-by-step implementation instructions for Phase 2 of the ContentRenderer system. It includes:
1. **Shiki Transformer Integration** (deferred from Phase 1)
2. **Full MDX Renderer Implementation** (Phase 2 scope)

---

## 1. Prerequisites Checklist

Before implementing, verify:

- [x] Phase 1 complete (all core renderers working)
- [x] Backend has `mdx` in ContentFormat enum
- [x] `@mdx-js/mdx@3.1.1` installed
- [x] `react-shiki@0.9.1` with `shiki@3.22.0` installed
- [ ] Backend MDX compilation endpoint ready (or will use runtime-only initially)

### 1.1 Package Versions

```
@mdx-js/mdx: 3.1.1
react-shiki: 0.9.1
shiki: 3.22.0
@shikijs/transformers: 3.22.0
@shikijs/types: (included with shiki)
```

### 1.2 New Dependencies (if not installed)

```bash
# These should already be installed, verify with:
npm ls @shikijs/transformers @mdx-js/mdx

# If missing, install:
npm install @shikijs/transformers
```

### 1.3 Files to Modify (Approved)

Per integrated-spec Section 9.1 and Phase 1 precedent:

**Existing files to update:**
- `types.ts` - Add MDX types, update CodeHighlightProps for transformers
- `components/CodeHighlight.tsx` - Add transformer support
- `renderers/CodeRenderer.tsx` - Wire transformer options
- `renderers/MarkdownRenderer.tsx` - Wire transformer options
- `renderers/MDXRenderer.tsx` - Full implementation
- `hooks/useMDXCompiler.ts` - MDX runtime compilation
- `index.ts` - Add new exports

---

## 2. Implementation Order

Files must be implemented in this dependency order:

```
Part A: Shiki Transformers (Phase 1 Deferred)
═══════════════════════════════════════════════
1. types.ts                 ← Add transformer types to CodeHighlightProps
2. CodeHighlight.tsx        ← Implement transformer integration
3. CodeRenderer.tsx         ← Wire lineNumbers, highlightLines, startLine
4. MarkdownRenderer.tsx     ← Ensure transformers work in MD code blocks

Part B: MDX Implementation
═══════════════════════════════════════════════
5. types.ts                 ← Add MDXContentOptions, MDXComponents
6. useMDXCompiler.ts        ← Lazy-load runtime compilation
7. MDXRenderer.tsx          ← Compile-time + runtime paths
8. index.ts                 ← Export new types and hook
```

---

## 3. Part A: Shiki Transformer Integration

### 3.1 Update types.ts - Add Transformer Support

**Location:** `types.ts`

**Changes:** Extend `CodeHighlightProps.options` to include transformer-related options.

```typescript
// ADD to imports at top of file
import type { ShikiTransformer } from "@shikijs/types"

// Re-export for convenience (around line 12)
export type { ShikiTransformer }

// UPDATE CodeHighlightProps (around line 145)
/**
 * CodeHighlight props for Shiki integration
 * UPDATED: Added transformer options
 */
export interface CodeHighlightProps {
  className?: string
  children?: ReactNode
  options?: {
    language?: string
    theme?: string
    forceBlock?: boolean
    copyable?: boolean
    // NEW: Transformer options
    lineNumbers?: boolean
    highlightLines?: number[]
    startLine?: number
    transformers?: ShikiTransformer[]
  }
}
```

**Note:** We import `ShikiTransformer` from `@shikijs/types` rather than defining our own. This ensures compatibility with `@shikijs/transformers` and future Shiki updates.

---

### 3.2 Update CodeHighlight.tsx - Implement Transformers

**Location:** `components/CodeHighlight.tsx`

**Changes:** Add line numbers, line highlighting, and start line support using Shiki transformers.

**Note on @shikijs/transformers:** The project has `@shikijs/transformers@3.22.0` installed, which provides pre-built transformers. However, there's no built-in line numbers transformer, so we create a custom one. The `transformerCompactLineOptions` can be used for line-specific styling.

```typescript
/**
 * CodeHighlight - Shiki-powered syntax highlighting
 *
 * Supports:
 * - Line numbers (lineNumbers: true)
 * - Line highlighting (highlightLines: [1, 3, 5])
 * - Start line offset (startLine: 10)
 * - Custom transformers from @shikijs/transformers
 *
 * react-shiki's ShikiHighlighter accepts `transformers` prop via
 * CodeToHastOptions → TransformerOptions inheritance.
 */
import { ShikiHighlighter } from "react-shiki"
import { useMemo } from "react"
import {
  transformerCompactLineOptions,
  type TransformerCompactLineOption,
} from "@shikijs/transformers"
import type { ShikiTransformer } from "@shikijs/types"
import type { CodeHighlightProps } from "../types"

// Extract language from className like "language-typescript"
function extractLanguage(className?: string): string | undefined {
  if (!className) return undefined
  const match = className.match(/language-(\w+)/)
  return match?.[1]
}

/**
 * Create line numbers transformer
 * Adds data-line attribute for CSS-based line numbers
 */
function createLineNumbersTransformer(startLine: number = 1): ShikiTransformer {
  return {
    name: "line-numbers",
    line(node, line) {
      // Add line number as data attribute (1-indexed, adjusted for startLine)
      const lineNum = line + startLine - 1
      node.properties = node.properties || {}
      node.properties["data-line"] = lineNum
    },
    pre(node) {
      // Add class for CSS line numbers styling
      node.properties = node.properties || {}
      node.properties.className = node.properties.className || []
      if (Array.isArray(node.properties.className)) {
        node.properties.className.push("shiki-line-numbers")
      }
    },
  }
}

/**
 * Create line highlight transformer using @shikijs/transformers
 */
function createHighlightLinesTransformer(
  lines: number[]
): ShikiTransformer {
  const lineOptions: TransformerCompactLineOption[] = lines.map((line) => ({
    line,
    classes: ["shiki-highlighted"],
  }))
  return transformerCompactLineOptions(lineOptions)
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

  // Build transformers array
  const transformers = useMemo(() => {
    const result: ShikiTransformer[] = []

    // Add line numbers if requested
    if (options.lineNumbers) {
      result.push(createLineNumbersTransformer(options.startLine))
    }

    // Add line highlighting if requested (using @shikijs/transformers)
    if (options.highlightLines?.length) {
      result.push(createHighlightLinesTransformer(options.highlightLines))
    }

    // Add custom transformers
    if (options.transformers?.length) {
      result.push(...options.transformers)
    }

    return result
  }, [options.lineNumbers, options.startLine, options.highlightLines, options.transformers])

  if (isInline) {
    // Inline code: simple styled span
    return (
      <code className="bg-muted px-1.5 py-0.5 rounded text-sm font-mono">
        {code}
      </code>
    )
  }

  // Block code: full Shiki highlighting with transformers
  return (
    <div className="relative group">
      <ShikiHighlighter
        language={language}
        theme={theme}
        transformers={transformers.length > 0 ? transformers : undefined}
      >
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

**CSS Required:** Add these styles to support line numbers and highlighting:

```css
/* Add to global styles or component-level CSS */
.shiki-line-numbers {
  counter-reset: line;
}

.shiki-line-numbers .line {
  display: block;
}

.shiki-line-numbers .line::before {
  counter-increment: line;
  content: counter(line);
  display: inline-block;
  width: 2rem;
  margin-right: 1rem;
  text-align: right;
  color: var(--muted-foreground);
  opacity: 0.5;
}

/* Use data-line attribute when startLine is set */
.shiki-line-numbers .line[data-line]::before {
  content: attr(data-line);
}

.shiki-highlighted {
  background-color: rgba(255, 255, 0, 0.1);
  display: block;
  margin: 0 -1rem;
  padding: 0 1rem;
}
```

**Note:** If CSS-in-JS is preferred, these styles can be added via Tailwind's `@apply` or inline styles.

---

### 3.3 Update CodeRenderer.tsx - Wire Options

**Location:** `renderers/CodeRenderer.tsx`

**Changes:** Pass transformer options through to CodeHighlight.

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
  // NEW: Transformer options
  const lineNumbers = options?.lineNumbers ?? false
  const highlightLines = options?.highlightLines
  const startLine = options?.startLine

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
          // NEW: Pass transformer options
          lineNumbers,
          highlightLines,
          startLine,
        }}
      >
        {code}
      </CodeHighlight>
    </div>
  )
}
```

---

### 3.4 Update MarkdownRenderer.tsx - Enable Transformers

**Location:** `renderers/MarkdownRenderer.tsx`

**Changes:** Allow transformer options to flow through markdown code blocks.

```typescript
/**
 * MarkdownRenderer - Markdown with Shiki code highlighting
 *
 * Uses react-markdown with custom code component for Shiki integration.
 * Supports transformer options via metadata.
 */
import ReactMarkdown from "react-markdown"
import { CodeHighlight } from "../components/CodeHighlight"
import { useThemeResolution } from "../hooks/useThemeResolution"
import type { ContentProps, MarkdownContentOptions } from "../types"

export function MarkdownRenderer({
  content,
  variant,
  className,
}: ContentProps<"markdown">) {
  const markdown = typeof content.value === "string" ? content.value : ""
  const { codeTheme, prose } = useThemeResolution({ content })
  const options = content.metadata?.options as MarkdownContentOptions | undefined

  // Prose class based on variant and theme resolution
  const proseClass = prose && variant !== "inline"
    ? "prose prose-lg dark:prose-invert max-w-none"
    : ""

  return (
    <div className={`${proseClass} ${className ?? ""}`}>
      <ReactMarkdown
        components={{
          code({ className: codeClassName, children, ...props }) {
            // Check if this is a code block (has language class) vs inline code
            const isBlock = codeClassName?.includes("language-")

            return (
              <CodeHighlight
                className={codeClassName}
                options={{
                  theme: codeTheme,
                  forceBlock: isBlock,
                  // Enable line numbers for blocks by default in page variant
                  lineNumbers: isBlock && variant === "page",
                }}
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

## 4. Part B: MDX Implementation

### 4.1 Update types.ts - Add MDX Types

**Location:** `types.ts`

**Changes:** Add MDXContentOptions, MDXComponents, and MDXRendererProps.

```typescript
// ADD after MarkdownContentOptions (around line 68)

/**
 * MDX-specific rendering options
 */
export interface MDXContentOptions {
  /** If true, only whitelisted components allowed */
  restrictedComponents?: boolean
  /** Custom component overrides */
  components?: MDXComponents
  /** Use backend-compiled MDX instead of runtime compilation */
  useCompiledMDX?: boolean
}

// UPDATE FormatSpecificOptions to include MDXContentOptions
export type FormatSpecificOptions =
  | CodeContentOptions
  | HTMLContentOptions
  | JSONContentOptions
  | SVGContentOptions
  | ImageContentOptions
  | MarkdownContentOptions
  | MDXContentOptions  // ADD THIS

// ADD MDXComponents type (around line 155)

/**
 * MDX component mapping for custom rendering
 */
export type MDXComponents = {
  // Standard HTML elements
  h1?: React.ComponentType<React.HTMLAttributes<HTMLHeadingElement>>
  h2?: React.ComponentType<React.HTMLAttributes<HTMLHeadingElement>>
  h3?: React.ComponentType<React.HTMLAttributes<HTMLHeadingElement>>
  h4?: React.ComponentType<React.HTMLAttributes<HTMLHeadingElement>>
  h5?: React.ComponentType<React.HTMLAttributes<HTMLHeadingElement>>
  h6?: React.ComponentType<React.HTMLAttributes<HTMLHeadingElement>>
  p?: React.ComponentType<React.HTMLAttributes<HTMLParagraphElement>>
  strong?: React.ComponentType<React.HTMLAttributes<HTMLElement>>
  em?: React.ComponentType<React.HTMLAttributes<HTMLElement>>
  ul?: React.ComponentType<React.HTMLAttributes<HTMLUListElement>>
  ol?: React.ComponentType<React.HTMLAttributes<HTMLOListElement>>
  li?: React.ComponentType<React.HTMLAttributes<HTMLLIElement>>
  blockquote?: React.ComponentType<React.HTMLAttributes<HTMLQuoteElement>>
  a?: React.ComponentType<React.AnchorHTMLAttributes<HTMLAnchorElement>>
  img?: React.ComponentType<React.ImgHTMLAttributes<HTMLImageElement>>
  hr?: React.ComponentType<React.HTMLAttributes<HTMLHRElement>>
  table?: React.ComponentType<React.TableHTMLAttributes<HTMLTableElement>>
  thead?: React.ComponentType<React.HTMLAttributes<HTMLTableSectionElement>>
  tbody?: React.ComponentType<React.HTMLAttributes<HTMLTableSectionElement>>
  tr?: React.ComponentType<React.HTMLAttributes<HTMLTableRowElement>>
  th?: React.ComponentType<React.ThHTMLAttributes<HTMLTableCellElement>>
  td?: React.ComponentType<React.TdHTMLAttributes<HTMLTableCellElement>>

  // Code integration (Shiki)
  pre?: React.ComponentType<React.HTMLAttributes<HTMLPreElement>>
  code?: React.ComponentType<CodeHighlightProps>

  // Custom components (whitelisted)
  [key: string]: React.ComponentType<unknown> | undefined
}

/**
 * Props for MDX compilation result
 */
export interface MDXCompiledResult {
  /** Compiled MDX function component */
  default: React.ComponentType<{ components?: MDXComponents }>
  /** Exported values from MDX */
  [key: string]: unknown
}

/**
 * MDX compilation state
 */
export interface MDXCompilationState {
  status: "idle" | "compiling" | "success" | "error"
  result?: MDXCompiledResult
  error?: Error
}
```

---

### 4.2 Implement useMDXCompiler.ts

**Location:** `hooks/useMDXCompiler.ts`

**Purpose:** Lazy-load @mdx-js/mdx and compile MDX at runtime.

```typescript
/**
 * useMDXCompiler - Runtime MDX compilation hook
 *
 * Lazily loads @mdx-js/mdx and compiles MDX source to React components.
 * Uses dynamic import to avoid bundling the compiler for non-MDX content.
 */
import { useState, useEffect, useCallback, useRef } from "react"
import type { MDXCompiledResult, MDXCompilationState } from "../types"

// Cache for compiled MDX to avoid recompilation
const compilationCache = new Map<string, MDXCompiledResult>()

// Lazy-loaded compiler module
let compilerPromise: Promise<typeof import("@mdx-js/mdx")> | null = null

/**
 * Lazily load the MDX compiler
 */
async function getCompiler() {
  if (!compilerPromise) {
    compilerPromise = import("@mdx-js/mdx")
  }
  return compilerPromise
}

/**
 * Generate a cache key from MDX source
 */
function getCacheKey(source: string): string {
  // Simple hash for cache key
  let hash = 0
  for (let i = 0; i < source.length; i++) {
    const char = source.charCodeAt(i)
    hash = ((hash << 5) - hash) + char
    hash = hash & hash // Convert to 32-bit integer
  }
  return `mdx_${hash}`
}

/**
 * Compile MDX source to a React component
 */
async function compileMDX(source: string): Promise<MDXCompiledResult> {
  const cacheKey = getCacheKey(source)

  // Check cache first
  const cached = compilationCache.get(cacheKey)
  if (cached) {
    return cached
  }

  // Load compiler
  const { compile, run } = await getCompiler()

  // Compile MDX to JS
  const compiled = await compile(source, {
    outputFormat: "function-body",
    development: process.env.NODE_ENV === "development",
  })

  // Run the compiled code to get the component
  const { default: runtime } = await import("react/jsx-runtime")
  const result = await run(compiled, {
    ...runtime,
    baseUrl: import.meta.url,
  })

  // Cache and return
  compilationCache.set(cacheKey, result as MDXCompiledResult)
  return result as MDXCompiledResult
}

/**
 * Hook for runtime MDX compilation
 *
 * @param source - MDX source string
 * @param enabled - Whether to compile (false = skip compilation)
 * @returns Compilation state with result or error
 */
export function useMDXCompiler(
  source: string,
  enabled: boolean = true
): MDXCompilationState {
  const [state, setState] = useState<MDXCompilationState>({
    status: "idle",
  })

  // Track current source to handle race conditions
  const sourceRef = useRef(source)
  sourceRef.current = source

  const compile = useCallback(async () => {
    if (!enabled || !source) {
      setState({ status: "idle" })
      return
    }

    setState({ status: "compiling" })

    try {
      const result = await compileMDX(source)

      // Check if source changed during compilation
      if (sourceRef.current !== source) {
        return // Discard stale result
      }

      setState({ status: "success", result })
    } catch (error) {
      // Check if source changed during compilation
      if (sourceRef.current !== source) {
        return
      }

      setState({
        status: "error",
        error: error instanceof Error ? error : new Error(String(error)),
      })
    }
  }, [source, enabled])

  useEffect(() => {
    compile()
  }, [compile])

  return state
}

/**
 * Clear the MDX compilation cache
 * Useful for development or memory management
 */
export function clearMDXCache(): void {
  compilationCache.clear()
}
```

---

### 4.3 Implement MDXRenderer.tsx

**Location:** `renderers/MDXRenderer.tsx`

**Purpose:** Full MDX rendering with compile-time and runtime paths.

```typescript
/**
 * MDXRenderer - MDX content with compile-time and runtime paths
 *
 * Two rendering modes:
 * 1. Compile-time: Backend provides compiled MDX (faster, preferred)
 * 2. Runtime: Frontend compiles MDX on-demand (flexible, slower)
 *
 * Security:
 * - safeMode: true → restricted components only
 * - safeMode: false → full component access
 */
import { Suspense, useMemo } from "react"
import { useMDXCompiler } from "../hooks/useMDXCompiler"
import { useThemeResolution } from "../hooks/useThemeResolution"
import { CodeHighlight } from "../components/CodeHighlight"
import { FallbackRenderer } from "../components/FallbackRenderer"
import type {
  ContentProps,
  MDXContentOptions,
  MDXComponents,
  MDXCompiledResult,
} from "../types"

/**
 * Default MDX components with Shiki integration
 */
function createDefaultComponents(codeTheme: string): MDXComponents {
  return {
    // Code blocks with Shiki highlighting
    code: ({ className, children, ...props }) => (
      <CodeHighlight
        className={className}
        options={{ theme: codeTheme, forceBlock: true }}
      >
        {children}
      </CodeHighlight>
    ),
    // Pre wrapper (Shiki handles this)
    pre: ({ children, ...props }) => (
      <div className="not-prose my-4" {...props}>
        {children}
      </div>
    ),
    // Standard elements with prose styling
    h1: (props) => <h1 className="text-3xl font-bold mt-8 mb-4" {...props} />,
    h2: (props) => <h2 className="text-2xl font-semibold mt-6 mb-3" {...props} />,
    h3: (props) => <h3 className="text-xl font-medium mt-4 mb-2" {...props} />,
    p: (props) => <p className="my-4 leading-relaxed" {...props} />,
    ul: (props) => <ul className="my-4 ml-6 list-disc" {...props} />,
    ol: (props) => <ol className="my-4 ml-6 list-decimal" {...props} />,
    li: (props) => <li className="my-1" {...props} />,
    blockquote: (props) => (
      <blockquote
        className="border-l-4 border-muted pl-4 italic my-4"
        {...props}
      />
    ),
    a: (props) => (
      <a
        className="text-primary underline hover:no-underline"
        target="_blank"
        rel="noopener noreferrer"
        {...props}
      />
    ),
    hr: (props) => <hr className="my-8 border-muted" {...props} />,
  }
}

/**
 * Restricted components for safeMode
 * Only allows basic formatting, no custom components
 */
const RESTRICTED_COMPONENT_NAMES = new Set([
  "h1", "h2", "h3", "h4", "h5", "h6",
  "p", "strong", "em", "ul", "ol", "li",
  "blockquote", "a", "img", "hr",
  "table", "thead", "tbody", "tr", "th", "td",
  "pre", "code",
])

function filterRestrictedComponents(
  components: MDXComponents
): MDXComponents {
  const filtered: MDXComponents = {}
  for (const [key, value] of Object.entries(components)) {
    if (RESTRICTED_COMPONENT_NAMES.has(key)) {
      filtered[key] = value
    }
  }
  return filtered
}

/**
 * Loading state while MDX compiles
 */
function MDXLoadingState() {
  return (
    <div className="animate-pulse space-y-4">
      <div className="h-4 bg-muted rounded w-3/4" />
      <div className="h-4 bg-muted rounded w-1/2" />
      <div className="h-4 bg-muted rounded w-5/6" />
    </div>
  )
}

/**
 * Error state when MDX fails to compile
 */
function MDXErrorState({ error }: { error: Error }) {
  return (
    <div className="border border-destructive/50 rounded-lg p-4 bg-destructive/10">
      <p className="text-sm text-destructive font-medium mb-2">
        MDX Compilation Error
      </p>
      <pre className="text-xs text-muted-foreground overflow-auto">
        {error.message}
      </pre>
    </div>
  )
}

/**
 * Runtime-compiled MDX renderer
 */
function RuntimeMDXRenderer({
  source,
  components,
  safeMode,
}: {
  source: string
  components: MDXComponents
  safeMode: boolean
}) {
  const { status, result, error } = useMDXCompiler(source, true)

  if (status === "compiling" || status === "idle") {
    return <MDXLoadingState />
  }

  if (status === "error" || !result) {
    return <MDXErrorState error={error ?? new Error("Unknown error")} />
  }

  const MDXContent = result.default
  const finalComponents = safeMode
    ? filterRestrictedComponents(components)
    : components

  return <MDXContent components={finalComponents} />
}

/**
 * Compile-time MDX renderer (backend-provided)
 */
function CompiledMDXRenderer({
  compiled,
  components,
  safeMode,
}: {
  compiled: MDXCompiledResult
  components: MDXComponents
  safeMode: boolean
}) {
  const MDXContent = compiled.default
  const finalComponents = safeMode
    ? filterRestrictedComponents(components)
    : components

  return <MDXContent components={finalComponents} />
}

/**
 * Main MDX Renderer
 */
export function MDXRenderer({
  content,
  variant,
  safeMode = true,
  className,
}: ContentProps<"mdx">) {
  const { codeTheme } = useThemeResolution({ content })
  const options = content.metadata?.options as MDXContentOptions | undefined

  // Determine rendering path
  const useCompiledMDX = options?.useCompiledMDX ?? false

  // Build component map
  const components = useMemo(() => {
    const defaults = createDefaultComponents(codeTheme)
    const custom = options?.components ?? {}

    // Merge: defaults < custom
    return { ...defaults, ...custom }
  }, [codeTheme, options?.components])

  // Variant-specific wrapper class
  const variantClass = useMemo(() => {
    switch (variant) {
      case "inline":
        return "inline"
      case "card":
        return "max-h-96 overflow-auto"
      case "page":
        return "prose prose-lg dark:prose-invert max-w-none"
      case "modal":
        return "prose dark:prose-invert max-w-2xl mx-auto"
      default:
        return "prose dark:prose-invert max-w-none"
    }
  }, [variant])

  // Check for compiled MDX in content value
  const value = content.value
  const isCompiledMDX =
    useCompiledMDX &&
    typeof value === "object" &&
    value !== null &&
    "default" in value

  // Handle compiled MDX path
  if (isCompiledMDX) {
    return (
      <div className={`${variantClass} ${className ?? ""}`}>
        <Suspense fallback={<MDXLoadingState />}>
          <CompiledMDXRenderer
            compiled={value as MDXCompiledResult}
            components={components}
            safeMode={safeMode}
          />
        </Suspense>
      </div>
    )
  }

  // Handle runtime compilation path
  if (typeof value === "string") {
    return (
      <div className={`${variantClass} ${className ?? ""}`}>
        <RuntimeMDXRenderer
          source={value}
          components={components}
          safeMode={safeMode}
        />
      </div>
    )
  }

  // Fallback for invalid content
  return <FallbackRenderer content={content} />
}
```

---

### 4.4 Update index.ts - Add New Exports

**Location:** `index.ts`

**Changes:** Export new types and the useMDXCompiler hook.

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
  MDXContentOptions,           // NEW
  // CodeHighlight
  CodeHighlightProps,
  ShikiTransformer,            // NEW
  // MDX
  MDXComponents,               // NEW
  MDXCompiledResult,           // NEW
  MDXCompilationState,         // NEW
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
export { useMDXCompiler, clearMDXCache } from "./hooks/useMDXCompiler"  // NEW
```

---

## 5. Testing Strategy

### 5.1 Shiki Transformer Testing

```typescript
// Test line numbers
<ContentRenderer
  content={{
    format: "code",
    value: `function hello() {\n  console.log("world")\n}`,
    metadata: {
      options: {
        language: "typescript",
        lineNumbers: true,
        startLine: 10,
      }
    }
  }}
/>

// Test line highlighting
<ContentRenderer
  content={{
    format: "code",
    value: `const a = 1\nconst b = 2\nconst c = 3`,
    metadata: {
      options: {
        language: "typescript",
        highlightLines: [1, 3],
      }
    }
  }}
/>
```

### 5.2 MDX Testing

```typescript
// Test runtime MDX compilation
<ContentRenderer
  content={{
    format: "mdx",
    value: `# Hello World\n\nThis is **MDX** content.\n\n\`\`\`typescript\nconst x = 1\n\`\`\``,
  }}
/>

// Test with custom components
<ContentRenderer
  content={{
    format: "mdx",
    value: `<CustomAlert>Important!</CustomAlert>`,
    metadata: {
      options: {
        components: {
          CustomAlert: ({ children }) => <div className="alert">{children}</div>
        }
      }
    }
  }}
/>

// Test safe mode (should filter custom components)
<ContentRenderer
  content={{
    format: "mdx",
    value: `<DangerousComponent />`,
  }}
  safeMode={true}
/>
```

### 5.3 Manual Testing Checklist

- [ ] Code blocks show line numbers when `lineNumbers: true`
- [ ] Line numbers start from `startLine` value
- [ ] Highlighted lines are visually distinct
- [ ] MDX compiles and renders basic markdown
- [ ] MDX renders code blocks with Shiki highlighting
- [ ] MDX custom components work when not in safeMode
- [ ] MDX custom components are filtered in safeMode
- [ ] MDX shows loading state during compilation
- [ ] MDX shows error state on compilation failure
- [ ] Compiled MDX (backend-provided) renders correctly

---

## 6. Success Criteria

Phase 2 is complete when:

1. **Shiki Transformers:**
   - [ ] `lineNumbers` option works in CodeRenderer and MarkdownRenderer
   - [ ] `highlightLines` visually highlights specified lines
   - [ ] `startLine` offsets line number display

2. **MDX Renderer:**
   - [ ] Runtime compilation path works (lazy-loads @mdx-js/mdx)
   - [ ] Compiled MDX path works (hydrates backend-compiled JS)
   - [ ] MDXComponents map applied correctly
   - [ ] safeMode filters to restricted components only
   - [ ] Code blocks in MDX use Shiki highlighting

3. **Exports:**
   - [ ] All new types exported from index.ts
   - [ ] useMDXCompiler hook exported and documented

---

## 7. Paradigm Conflicts Resolved

| Conflict from Phase 1 | Resolution in Phase 2 |
|-----------------------|----------------------|
| Line numbers not implemented | ✅ Shiki transformer `lineNumbers` |
| highlightLines not implemented | ✅ Shiki transformer `highlightLines` |
| startLine not implemented | ✅ Shiki transformer `startLine` |
| MDXRenderer stub | ✅ Full implementation with runtime + compiled paths |

---

## 8. Open Items Remaining

| Item | Status | Notes |
|------|--------|-------|
| decorationHint wiring | Deferred | Can be added to useThemeResolution when design system requires |
| JSON tree interactive mode | Deferred | Basic text mode works; tree needs library (Phase 3+) |
| Backend MDX compilation API | External | Frontend ready; backend integration pending |

---

## 9. Holistic Review

### 9.1 Data Flow with Transformers

```
CodeRenderer receives content with options
       │
       ├── options.lineNumbers = true
       ├── options.highlightLines = [2, 4]
       ├── options.startLine = 10
       │
       ▼
CodeHighlight receives options
       │
       ├── Creates lineNumbers transformer
       ├── Creates highlightLines transformer
       │
       ▼
ShikiHighlighter with transformers
       │
       ▼
Rendered code with line numbers and highlights
```

### 9.2 MDX Compilation Flow

```
MDXRenderer receives content
       │
       ├── content.value is string?
       │   │
       │   ▼ YES: Runtime path
       │   useMDXCompiler(source)
       │       │
       │       ├── Lazy-load @mdx-js/mdx
       │       ├── Compile source to JS
       │       ├── Run JS to get React component
       │       ├── Cache result
       │       │
       │       ▼
       │   <MDXContent components={...} />
       │
       └── content.value has .default?
           │
           ▼ YES: Compiled path
           <CompiledMDXRenderer compiled={value} />
               │
               ▼
           <MDXContent components={...} />
```

### 9.3 Security Model Update

```
safeMode: true (default)
  ├── HTML: DOMPurify sanitization
  ├── SVG: Rendered as <img> data URL
  └── MDX: RESTRICTED_COMPONENT_NAMES only ← NEW
           (h1-h6, p, strong, em, ul, ol, li,
            blockquote, a, img, hr, table elements,
            pre, code)

safeMode: false
  ├── HTML: Minimal sanitization
  ├── SVG: Can render inline
  └── MDX: Full component access ← NEW
           (custom components allowed)
```

---

*Phase 2 Implementation Guide. Builds on Phase 1 foundation. Aligned with integrated-spec.md.*
