/**
 * MDXRenderer - MDX content (Phase 2 implementation)
 *
 * - Compile-time path (backend-compiled JS hydration)
 * - Runtime path (lazy-load @mdx-js/mdx)
 * - MDXComponents whitelist
 * Security:
 * - safeMode: true → restricted components only
 * - safeMode: false → full component access
 */

import { lazy, Suspense, useMemo } from "react"
import { FallbackRenderer } from "../components/FallbackRenderer"
import { useMDXCompiler } from "../hooks/useMDXCompiler"
import { useThemeResolution } from "../hooks/useThemeResolution"
import type {
  ContentProps,
  MDXCompiledResult,
  MDXComponents,
  MDXContentOptions,
} from "../types"

const LazyCodeHighlight = lazy(async () => {
  const mod = await import("../components/CodeHighlight")
  return { default: mod.CodeHighlight }
})

/**
 * Default MDX components with Shiki integration
 */
function createDefaultComponents(codeTheme: string): MDXComponents {
  return {
    // Code blocks with Shiki highlighting
    code: ({ className, children }) => (
      <Suspense
        fallback={
          <code className={className}>
            {typeof children === "string"
              ? children
              : (children?.toString?.() ?? "")}
          </code>
        }
      >
        <LazyCodeHighlight
          className={className}
          options={{ theme: codeTheme, forceBlock: true }}
        >
          {children}
        </LazyCodeHighlight>
      </Suspense>
    ),
    // Pre wrapper (Shiki handles this, we just provide a container)
    pre: ({ children }) => <div className="not-prose my-4">{children}</div>,
    // Standard elements with prose styling
    h1: (props) => <h1 className="text-3xl font-bold mt-8 mb-4" {...props} />,
    h2: (props) => (
      <h2 className="text-2xl font-semibold mt-6 mb-3" {...props} />
    ),
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
  "h1",
  "h2",
  "h3",
  "h4",
  "h5",
  "h6",
  "p",
  "svg",
  "strong",
  "em",
  "ul",
  "ol",
  "li",
  "blockquote",
  "a",
  "img",
  "hr",
  "table",
  "thead",
  "tbody",
  "tr",
  "th",
  "td",
  "pre",
  "code",
])

function filterRestrictedComponents(components: MDXComponents): MDXComponents {
  // Filter to only include restricted (safe) component names
  // Uses type assertion since we're dynamically building the object
  const filtered = Object.fromEntries(
    Object.entries(components).filter(([key]) =>
      RESTRICTED_COMPONENT_NAMES.has(key),
    ),
  ) as MDXComponents
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

// export function MDXRenderer({ content }: ContentProps<"mdx">) {
//   // Phase 2: Implement full MDX rendering
//   // For now, fall back to showing format info
//   return (
//     <div className="border border-blue-300 dark:border-blue-700 rounded-lg p-4 bg-blue-50 dark:bg-blue-950/30">
//       <p className="text-sm text-blue-700 dark:text-blue-400 font-medium mb-2">
//         MDX format (Phase 2)
//       </p>
//       <p className="text-xs text-muted-foreground">
//         MDX rendering will be available after backend compilation support is ready.
//       </p>
//       <FallbackRenderer content={content} />
//     </div>
//   )
// }
