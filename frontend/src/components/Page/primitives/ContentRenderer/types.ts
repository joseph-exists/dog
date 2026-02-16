/**
 * ContentRenderer Type Definitions
 *
 * Re-exports ContentFormat from backend client.
 * Defines frontend-specific interfaces for rendering.
 */
import type { ContentFormat } from "@/client"
import type { ReactNode } from "react"
import type { ShikiTransformer } from "@shikijs/types"

// Re-export for convenience
export type { ContentFormat }
export type { ShikiTransformer }

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
  | MDXContentOptions

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
 * Props for fallback renderer component
 */
export interface FallbackRendererProps {
  content: Content
}

/**
 * Main ContentRenderer props
 */
export interface ContentRendererProps {
  content: Content
  variant?: ContentVariant
  safeMode?: boolean
  fallback?: React.FC<FallbackRendererProps>
  decorationHint?: "brutalist" | "ethereal" | string
  theme?: ThemeConfig
  className?: string
}

/**
 * MDX component mapping for custom rendering
 *
 * Uses Record<string, ComponentType<any>> to allow:
 * - Standard HTML element overrides (h1, p, code, etc.)
 * - Custom components (whitelisted)
 *
 * Note: We use `any` here because MDX components receive varying props
 * depending on context (markdown AST, custom usage). The MDX runtime
 * handles prop validation at runtime.
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type MDXComponents = Record<string, React.ComponentType<any>>

/**
 * Renderer registry entry (type-safe version for external use)
 */
export interface Renderer<T extends ContentFormat = ContentFormat> {
  format: T
  Component: React.FC<ContentProps<T>>
}

/**
 * Renderer registry entry (loose version for internal registry storage)
 *
 * The registry stores renderers with loose typing because TypeScript's
 * function parameter contravariance prevents storing FC<ContentProps<"text">>
 * in a collection typed as FC<ContentProps<ContentFormat>>.
 *
 * Type safety is maintained at:
 * - Build time: Each renderer is individually typed
 * - Runtime: Dispatch matches format to correct renderer
 */
export interface RendererEntry {
  format: ContentFormat
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  Component: React.FC<any>
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
    // transformer options
    lineNumbers?: boolean
    highlightLines?: number[]
    startLine?: number
    transformers?: ShikiTransformer[]
  }
}

// **Note:** We import `ShikiTransformer` from `@shikijs/types` rather than defining our own. This ensures compatibility with `@shikijs/transformers` and future Shiki updates.

// ═══════════════════════════════════════════════════════════════════════════
// PLUGIN SYSTEM TYPES
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Plugin renderer extends base renderer with metadata
 *
 * The `meta` field provides:
 * - Plugin identification for debugging/logging
 * - Priority for conflict resolution (higher = preferred)
 * - Human-readable label for UI display
 */
export interface PluginRenderer<T extends ContentFormat = ContentFormat>
  extends Renderer<T> {
  meta: {
    /** Plugin that provides this renderer */
    pluginId: string
    /** Human-readable label for this renderer */
    label: string
    /** Priority for conflict resolution (higher wins, default: 0) */
    priority?: number
  }
}

/**
 * Plugin renderer registry - partial coverage of formats
 *
 * Plugins don't need to provide renderers for all formats.
 * They can target specific formats or subsets.
 */
export type PluginRendererRegistry = {
  [K in ContentFormat]?: PluginRenderer<K>
}

/**
 * Validation result from plugin validators
 */
export interface PluginValidationResult {
  valid: boolean
  errors: PluginValidationError[]
}

export interface PluginValidationError {
  code: string
  message: string
  path?: string // JSONPath to problematic field
  severity: "error" | "warning"
}

/**
 * Plugin interface - the core extensibility contract
 *
 * Plugins can:
 * - Provide custom renderers for specific formats
 * - Validate content before rendering
 * - Transform content before it reaches the renderer
 *
 * @template T - Subset of ContentFormat this plugin handles
 */
export interface Plugin<T extends ContentFormat = ContentFormat> {
  /** Unique plugin identifier (e.g., "katex", "mermaid", "custom-widgets") */
  id: string

  /** Plugin version for compatibility tracking */
  version?: string

  /** Human-readable plugin name */
  name?: string

  /** Plugin description */
  description?: string

  /**
   * Renderers provided by this plugin
   * Partial - plugins don't need to cover all formats
   */
  renderers?: Partial<PluginRendererRegistry>

  /**
   * Validate content before rendering
   *
   * Called before transform and render. Can return errors/warnings.
   * Returning errors does NOT block rendering by default (graceful degradation).
   *
   * @param content - The content to validate
   * @returns Validation result with any errors/warnings
   */
  validate?(content: Content<T>): PluginValidationResult

  /**
   * Transform content before rendering
   *
   * Applied in plugin priority order (highest first).
   * Transforms are chained: output of one becomes input to next.
   *
   * Common use cases:
   * - Preprocessing (e.g., macro expansion)
   * - Format conversion (e.g., custom markdown extensions)
   * - Content enrichment (e.g., auto-linking)
   *
   * @param content - The content to transform
   * @returns Transformed content (or original if no changes)
   */
  transform?(content: Content<T>): Content<T>

  /**
   * Plugin initialization hook
   *
   * Called when plugin is registered.
   * Can be async for lazy loading dependencies.
   */
  onRegister?(): void | Promise<void>

  /**
   * Plugin cleanup hook
   *
   * Called when plugin is unregistered.
   * Clean up any resources, event listeners, etc.
   */
  onUnregister?(): void
}

/**
 * Registered plugin with runtime state
 */
export interface RegisteredPlugin<T extends ContentFormat = ContentFormat>
  extends Plugin<T> {
  /** Registration timestamp */
  registeredAt: number
  /** Plugin status */
  status: "active" | "disabled" | "error"
  /** Error if status is "error" */
  error?: Error
}

/**
 * Plugin registration options
 */
export interface PluginRegistrationOptions {
  /** If true, don't call onRegister hook */
  skipInit?: boolean
  /** If true, replace existing plugin with same id */
  replace?: boolean
}

/**
 * Plugin resolution result
 */
export interface PluginResolutionResult {
  /** Resolved renderer (from plugin or core) */
  renderer: RendererEntry
  /** Plugin that provided the renderer (null if core) */
  plugin: RegisteredPlugin | null
  /** Whether plugin renderer overrode core */
  isOverride: boolean
}