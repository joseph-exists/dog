# Phase 5 Implementation Guide: Plugin System

> "Make it work, make it right, make it fast."
> — Kent Beck

This guide provides step-by-step implementation instructions for Phase 5 of the ContentRenderer system. Phase 5 formalizes the **Plugin Interface** and establishes the **Plugin Registration API** for extensible content rendering.

---

## 1. Phase 5 Objectives

> **Traceability:** This guide implements Phase 5 as defined in `integrated-spec.md` Section 10 and Section 14.5.
> It assumes Phases 1-4 are complete.

From integrated-spec Section 14.5:

1. **Formalize `Plugin<T>` interface** - Define the contract for plugins
2. **Add plugin registration API** - Enable runtime plugin registration
3. **Document plugin authoring guide** - Enable third-party plugin development

### 1.1 Success Criteria

Phase 5 is successful when:

- [ ] `Plugin<T>` interface is defined and exported
- [ ] `PluginRenderer<T>` extends base `Renderer<T>` with metadata
- [ ] `pluginRegistry` manages plugin lifecycle
- [ ] `registerPlugin()` / `unregisterPlugin()` API works
- [ ] Plugin renderers can override core renderers
- [ ] Plugin priority system resolves conflicts
- [ ] Optional `validate()` and `transform()` hooks work
- [ ] Plugin authoring documentation is complete

---

## 2. Prerequisites Checklist

Before implementing, verify:

- [x] Phase 1 complete (core renderers)
- [x] Phase 2 complete (MDX + Shiki transformers)
- [x] Phase 3 complete (proving ground / demo)
- [x] Phase 4 complete (migration + Common re-exports)
- [x] Existing types: `Renderer<T>`, `RendererEntry`, `ContentProps<T>`
- [x] Existing registry: `rendererRegistry`, `getRenderer()`

### 2.1 Current Architecture

```
Current Flow (Pre-Plugin):
══════════════════════════════════════

ContentRenderer receives content
       │
       ▼
getRenderer(content.format)
       │
       ▼
rendererRegistry[format] → RendererEntry
       │
       ▼
<Component {...props} />
```

```
Target Flow (With Plugins):
══════════════════════════════════════

ContentRenderer receives content
       │
       ▼
resolveRenderer(content.format)
       │
       ├── Check pluginRegistry (priority order)
       │   └── Plugin renderers override core
       │
       ├── Fallback to rendererRegistry
       │
       ▼
Apply plugin transforms (if any)
       │
       ▼
<Component {...props} />
```

---

## 3. Implementation Order

```
Part A: Type Definitions
════════════════════════════════════════
1. types.ts - Add Plugin, PluginRenderer, PluginRegistry types
2. types.ts - Add PluginValidationResult type

Part B: Plugin Registry
════════════════════════════════════════
3. pluginRegistry.ts - Plugin storage and lifecycle
4. pluginRegistry.ts - Priority-based renderer resolution
5. pluginRegistry.ts - Validation and transform hooks

Part C: Integration
════════════════════════════════════════
6. registry.ts - Update getRenderer to check plugins first
7. ContentRenderer.tsx - Wire transform hooks
8. index.ts - Export plugin API

Part D: Documentation
════════════════════════════════════════
9. Create plugin-authoring-guide.md
```

---

## 4. Part A: Type Definitions

### 4.1 Update types.ts - Add Plugin Types [x] COMPLETE

**Location:** `types.ts`

**Changes:** Add plugin-related interfaces after existing types.

```typescript
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
```

### 4.2 Type System Design Rationale

```
★ Insight ─────────────────────────────────────
1. PluginRenderer extends Renderer to maintain type compatibility
   with existing registry while adding metadata for debugging.

2. Plugin<T> is generic over ContentFormat subset to allow
   type-safe plugins that only handle specific formats.

3. validate() returns structured errors rather than throwing
   to support graceful degradation and preview error display.
─────────────────────────────────────────────────
```

---

## 5. Part B: Plugin Registry

### 5.1 Create pluginRegistry.ts

**Location:** `pluginRegistry.ts` (new file)

**Purpose:** Manage plugin lifecycle, resolution, and hooks.

```typescript
/**
 * Plugin Registry - Plugin lifecycle and renderer resolution
 *
 * Features:
 * - Plugin registration/unregistration
 * - Priority-based renderer resolution
 * - Transform chain execution
 * - Validation aggregation
 */

import type { ContentFormat } from "@/client"
import type {
  Content,
  Plugin,
  RegisteredPlugin,
  PluginRegistrationOptions,
  PluginRenderer,
  PluginResolutionResult,
  PluginValidationResult,
  RendererEntry,
} from "./types"
import { rendererRegistry } from "./registry"

// ═══════════════════════════════════════════════════════════════════════════
// PLUGIN STORAGE
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Registered plugins indexed by id
 */
const plugins = new Map<string, RegisteredPlugin>()

/**
 * Event listeners for plugin lifecycle
 */
type PluginEventType = "register" | "unregister" | "error"
type PluginEventListener = (plugin: RegisteredPlugin, event: PluginEventType) => void
const eventListeners = new Set<PluginEventListener>()

// ═══════════════════════════════════════════════════════════════════════════
// REGISTRATION API
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Register a plugin
 *
 * @param plugin - Plugin to register
 * @param options - Registration options
 * @returns The registered plugin
 * @throws If plugin with same id exists and replace=false
 */
export async function registerPlugin<T extends ContentFormat>(
  plugin: Plugin<T>,
  options: PluginRegistrationOptions = {}
): Promise<RegisteredPlugin<T>> {
  const { skipInit = false, replace = false } = options

  // Check for existing plugin
  if (plugins.has(plugin.id) && !replace) {
    throw new Error(
      `Plugin "${plugin.id}" is already registered. Use replace: true to override.`
    )
  }

  // Unregister existing if replacing
  if (plugins.has(plugin.id)) {
    await unregisterPlugin(plugin.id)
  }

  // Create registered plugin
  const registered: RegisteredPlugin<T> = {
    ...plugin,
    registeredAt: Date.now(),
    status: "active",
  }

  // Call onRegister hook
  if (!skipInit && plugin.onRegister) {
    try {
      await plugin.onRegister()
    } catch (error) {
      registered.status = "error"
      registered.error = error instanceof Error ? error : new Error(String(error))
      console.error(`Plugin "${plugin.id}" registration failed:`, error)
    }
  }

  // Store plugin
  plugins.set(plugin.id, registered as RegisteredPlugin)

  // Notify listeners
  emitEvent(registered as RegisteredPlugin, "register")

  return registered
}

/**
 * Unregister a plugin
 *
 * @param pluginId - ID of plugin to unregister
 * @returns True if plugin was unregistered, false if not found
 */
export async function unregisterPlugin(pluginId: string): Promise<boolean> {
  const plugin = plugins.get(pluginId)
  if (!plugin) {
    return false
  }

  // Call onUnregister hook
  if (plugin.onUnregister) {
    try {
      plugin.onUnregister()
    } catch (error) {
      console.error(`Plugin "${pluginId}" cleanup failed:`, error)
    }
  }

  // Remove plugin
  plugins.delete(pluginId)

  // Notify listeners
  emitEvent(plugin, "unregister")

  return true
}

/**
 * Get a registered plugin by id
 */
export function getPlugin(pluginId: string): RegisteredPlugin | undefined {
  return plugins.get(pluginId)
}

/**
 * Get all registered plugins
 */
export function getAllPlugins(): RegisteredPlugin[] {
  return Array.from(plugins.values())
}

/**
 * Check if a plugin is registered
 */
export function hasPlugin(pluginId: string): boolean {
  return plugins.has(pluginId)
}

// ═══════════════════════════════════════════════════════════════════════════
// RENDERER RESOLUTION
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Resolve renderer for a format, checking plugins first
 *
 * Resolution order:
 * 1. Plugin renderers (sorted by priority, highest first)
 * 2. Core rendererRegistry
 *
 * @param format - Content format to resolve
 * @returns Resolution result with renderer and source info
 */
export function resolveRenderer(format: ContentFormat): PluginResolutionResult | null {
  // Collect plugin renderers for this format
  const pluginRenderers: Array<{
    plugin: RegisteredPlugin
    renderer: PluginRenderer
  }> = []

  for (const plugin of plugins.values()) {
    if (plugin.status !== "active") continue
    const renderer = plugin.renderers?.[format]
    if (renderer) {
      pluginRenderers.push({ plugin, renderer })
    }
  }

  // Sort by priority (highest first)
  pluginRenderers.sort((a, b) => {
    const priorityA = a.renderer.meta.priority ?? 0
    const priorityB = b.renderer.meta.priority ?? 0
    return priorityB - priorityA
  })

  // Return highest priority plugin renderer if any
  if (pluginRenderers.length > 0) {
    const { plugin, renderer } = pluginRenderers[0]
    return {
      renderer: {
        format: renderer.format,
        Component: renderer.Component,
      },
      plugin,
      isOverride: true,
    }
  }

  // Fallback to core registry
  const coreRenderer = rendererRegistry[format]
  if (coreRenderer) {
    return {
      renderer: coreRenderer,
      plugin: null,
      isOverride: false,
    }
  }

  return null
}

/**
 * Get all renderers for a format (plugin + core)
 *
 * Useful for debugging or UI that shows available renderers.
 */
export function getAllRenderersForFormat(format: ContentFormat): Array<{
  renderer: RendererEntry | PluginRenderer
  source: "core" | string // "core" or plugin id
  priority: number
}> {
  const result: Array<{
    renderer: RendererEntry | PluginRenderer
    source: "core" | string
    priority: number
  }> = []

  // Add core renderer
  const coreRenderer = rendererRegistry[format]
  if (coreRenderer) {
    result.push({
      renderer: coreRenderer,
      source: "core",
      priority: -1, // Core has lowest priority
    })
  }

  // Add plugin renderers
  for (const plugin of plugins.values()) {
    if (plugin.status !== "active") continue
    const renderer = plugin.renderers?.[format]
    if (renderer) {
      result.push({
        renderer,
        source: plugin.id,
        priority: renderer.meta.priority ?? 0,
      })
    }
  }

  // Sort by priority (highest first)
  result.sort((a, b) => b.priority - a.priority)

  return result
}

// ═══════════════════════════════════════════════════════════════════════════
// VALIDATION
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Run all plugin validators for content
 *
 * Aggregates validation results from all active plugins.
 * Does NOT throw - returns combined validation result.
 *
 * @param content - Content to validate
 * @returns Aggregated validation result
 */
export function validateContent(content: Content): PluginValidationResult {
  const errors: PluginValidationResult["errors"] = []

  for (const plugin of plugins.values()) {
    if (plugin.status !== "active") continue
    if (!plugin.validate) continue

    try {
      const result = plugin.validate(content)
      if (!result.valid) {
        // Prefix errors with plugin id for debugging
        const prefixedErrors = result.errors.map((error) => ({
          ...error,
          code: `${plugin.id}:${error.code}`,
        }))
        errors.push(...prefixedErrors)
      }
    } catch (error) {
      // Validator threw - add as error
      errors.push({
        code: `${plugin.id}:validator_error`,
        message: error instanceof Error ? error.message : String(error),
        severity: "error",
      })
    }
  }

  return {
    valid: errors.filter((e) => e.severity === "error").length === 0,
    errors,
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// TRANSFORM CHAIN
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Apply all plugin transforms to content
 *
 * Transforms are applied in priority order (highest first).
 * Each transform receives the output of the previous.
 *
 * @param content - Content to transform
 * @returns Transformed content
 */
export function transformContent<T extends ContentFormat>(
  content: Content<T>
): Content<T> {
  // Get plugins with transforms, sorted by priority
  const transformPlugins = Array.from(plugins.values())
    .filter((p) => p.status === "active" && p.transform)
    .sort((a, b) => {
      // Use highest renderer priority as plugin priority
      const getMaxPriority = (plugin: RegisteredPlugin): number => {
        if (!plugin.renderers) return 0
        return Math.max(
          0,
          ...Object.values(plugin.renderers).map((r) => r?.meta.priority ?? 0)
        )
      }
      return getMaxPriority(b) - getMaxPriority(a)
    })

  // Apply transforms in chain
  let result = content
  for (const plugin of transformPlugins) {
    try {
      result = plugin.transform!(result) as Content<T>
    } catch (error) {
      console.error(`Plugin "${plugin.id}" transform failed:`, error)
      // Continue with untransformed content on error
    }
  }

  return result
}

// ═══════════════════════════════════════════════════════════════════════════
// EVENT SYSTEM
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Subscribe to plugin lifecycle events
 */
export function onPluginEvent(listener: PluginEventListener): () => void {
  eventListeners.add(listener)
  return () => eventListeners.delete(listener)
}

function emitEvent(plugin: RegisteredPlugin, event: PluginEventType): void {
  for (const listener of eventListeners) {
    try {
      listener(plugin, event)
    } catch (error) {
      console.error("Plugin event listener error:", error)
    }
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// UTILITIES
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Clear all plugins (useful for testing)
 */
export function clearPlugins(): void {
  for (const pluginId of plugins.keys()) {
    unregisterPlugin(pluginId)
  }
}

/**
 * Disable a plugin without unregistering
 */
export function disablePlugin(pluginId: string): boolean {
  const plugin = plugins.get(pluginId)
  if (!plugin) return false
  plugin.status = "disabled"
  return true
}

/**
 * Enable a previously disabled plugin
 */
export function enablePlugin(pluginId: string): boolean {
  const plugin = plugins.get(pluginId)
  if (!plugin) return false
  if (plugin.status === "error") return false // Can't enable errored plugins
  plugin.status = "active"
  return true
}
```

### 5.2 Plugin Registry Design Notes

```
★ Insight ─────────────────────────────────────
1. Priority resolution ensures predictable override behavior:
   - Higher priority plugins always win
   - Equal priority resolves to registration order

2. Transform chain is ordered by priority, not format:
   - Allows cross-format transforms (e.g., markdown preprocessing)
   - Each transform must handle all formats it claims to support

3. Validation is aggregative, not blocking:
   - All validators run regardless of individual failures
   - Graceful degradation: warnings don't prevent rendering
─────────────────────────────────────────────────
```

---

## 6. Part C: Integration

### 6.1 Update registry.ts

**Location:** `registry.ts`

**Changes:** Add resolveRenderer export that checks plugins first.

```typescript
/**
 * Renderer Registry - Format to renderer mapping
 *
 * UPDATED for Phase 5:
 * - getRenderer now checks plugin registry first
 * - Added resolveRenderer for full resolution info
 */

import type { ContentFormat } from "@/client"
import type { RendererEntry, PluginResolutionResult } from "./types"

import { TextRenderer } from "./renderers/TextRenderer"
import { CodeRenderer } from "./renderers/CodeRenderer"
import { HTMLRenderer } from "./renderers/HTMLRenderer"
import { JSONRenderer } from "./renderers/JSONRenderer"
import { SVGRenderer } from "./renderers/SVGRenderer"
import { ImageRenderer } from "./renderers/ImageRenderer"
import { MarkdownRenderer } from "./renderers/MarkdownRenderer"
import { MDXRenderer } from "./renderers/MDXRenderer"

// Import plugin resolution (lazy to avoid circular deps)
import { resolveRenderer as pluginResolveRenderer } from "./pluginRegistry"

/**
 * Core registry mapping ContentFormat to renderer components
 */
export const rendererRegistry: Partial<Record<ContentFormat, RendererEntry>> = {
  text: { format: "text", Component: TextRenderer },
  code: { format: "code", Component: CodeRenderer },
  html: { format: "html", Component: HTMLRenderer },
  json: { format: "json", Component: JSONRenderer },
  svg: { format: "svg", Component: SVGRenderer },
  image: { format: "image", Component: ImageRenderer },
  markdown: { format: "markdown", Component: MarkdownRenderer },
  mdx: { format: "mdx", Component: MDXRenderer },
}

/**
 * Get renderer for a given format
 *
 * UPDATED: Checks plugin registry first, then falls back to core.
 */
export function getRenderer(format: ContentFormat): RendererEntry | undefined {
  // Check plugins first
  const resolved = pluginResolveRenderer(format)
  if (resolved) {
    return resolved.renderer
  }

  // Fallback to core registry (shouldn't reach here if pluginResolveRenderer
  // already checks core, but kept for safety)
  return rendererRegistry[format]
}

/**
 * Get full resolution info including plugin source
 *
 * Use this when you need to know which plugin provided the renderer.
 */
export function resolveRenderer(format: ContentFormat): PluginResolutionResult | null {
  return pluginResolveRenderer(format)
}
```

### 6.2 Update ContentRenderer.tsx

**Location:** `ContentRenderer.tsx`

**Changes:** Wire transform and validation hooks.

```typescript
/**
 * ContentRenderer - Main polymorphic content renderer
 *
 * UPDATED for Phase 5:
 * - Applies plugin transforms before rendering
 * - Runs plugin validators (results available via context)
 */

import { useMemo } from "react"
import type { ContentRendererProps, Content, PluginValidationResult } from "./types"
import { resolveRenderer } from "./registry"
import { transformContent, validateContent } from "./pluginRegistry"
import { FallbackRenderer } from "./components/FallbackRenderer"
import { useThemeResolution } from "./hooks/useThemeResolution"

export function ContentRenderer({
  content,
  variant,
  safeMode = true,
  fallback: FallbackComponent = FallbackRenderer,
  decorationHint,
  theme,
  className,
}: ContentRendererProps) {
  // Resolve variant from content metadata or prop
  const resolvedVariant = variant ?? content.metadata?.variant ?? "card"

  // Theme resolution
  const { codeTheme } = useThemeResolution({ content, theme, decorationHint })

  // Apply plugin transforms
  const transformedContent = useMemo(() => {
    return transformContent(content)
  }, [content])

  // Run plugin validators (for debugging/preview - doesn't block render)
  const validation = useMemo<PluginValidationResult>(() => {
    return validateContent(transformedContent)
  }, [transformedContent])

  // Log validation warnings in development
  if (process.env.NODE_ENV === "development" && validation.errors.length > 0) {
    console.warn("ContentRenderer validation issues:", validation.errors)
  }

  // Resolve renderer (plugins first, then core)
  const resolution = resolveRenderer(transformedContent.format)

  if (!resolution) {
    return <FallbackComponent content={transformedContent} />
  }

  const { renderer, plugin, isOverride } = resolution
  const RendererComponent = renderer.Component

  // Debug logging in development
  if (process.env.NODE_ENV === "development" && isOverride) {
    console.debug(
      `ContentRenderer: Using plugin "${plugin?.id}" for format "${transformedContent.format}"`
    )
  }

  return (
    <RendererComponent
      content={transformedContent}
      variant={resolvedVariant}
      safeMode={safeMode}
      className={className}
    />
  )
}
```

### 6.3 Update index.ts - Export Plugin API

**Location:** `index.ts`

**Changes:** Export plugin types and registry functions.

```typescript
/**
 * ContentRenderer - Public Exports
 *
 * UPDATED for Phase 5:
 * - Added plugin types
 * - Added plugin registry API
 */

// TODO JOSEP THIS IS WHERE YOU AT
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
  MDXContentOptions,
  // CodeHighlight
  CodeHighlightProps,
  ShikiTransformer,
  MDXComponents,
  MDXCompiledResult,
  MDXCompilationState,
  // Registry types
  Renderer,
  RendererEntry,
  // Plugin types (NEW)
  Plugin,
  PluginRenderer,
  PluginRendererRegistry,
  PluginValidationResult,
  PluginValidationError,
  RegisteredPlugin,
  PluginRegistrationOptions,
  PluginResolutionResult,
} from "./types"

// Registry (for advanced use cases)
export { rendererRegistry, getRenderer, resolveRenderer } from "./registry"

// Plugin registry (NEW)
export {
  registerPlugin,
  unregisterPlugin,
  getPlugin,
  getAllPlugins,
  hasPlugin,
  validateContent,
  transformContent,
  onPluginEvent,
  clearPlugins,
  disablePlugin,
  enablePlugin,
  getAllRenderersForFormat,
} from "./pluginRegistry"

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
export { useMDXCompiler, clearMDXCache } from "./hooks/useMDXCompiler"
```

---

## 7. Part D: Documentation

### 7.1 Create Plugin Authoring Guide

**Location:** `plugin-authoring-guide.md` (separate document)

This guide will be created alongside implementation (see Section 10).

---

## 8. Example Plugins

### 8.1 Simple Override Plugin

```typescript
/**
 * Example: Custom JSON Renderer Plugin
 *
 * Demonstrates:
 * - Overriding core renderer
 * - Priority-based resolution
 */
import { registerPlugin, type Plugin, type ContentProps } from "@/components/Page/primitives/ContentRenderer"

// Custom JSON renderer with tree view
const JsonTreeRenderer: React.FC<ContentProps<"json">> = ({ content, className }) => {
  const data = typeof content.value === "string"
    ? JSON.parse(content.value)
    : content.value

  return (
    <div className={className}>
      <JsonTreeView data={data} />
    </div>
  )
}

const jsonTreePlugin: Plugin<"json"> = {
  id: "json-tree",
  name: "JSON Tree Viewer",
  version: "1.0.0",
  renderers: {
    json: {
      format: "json",
      Component: JsonTreeRenderer,
      meta: {
        pluginId: "json-tree",
        label: "Interactive JSON Tree",
        priority: 10, // Override core JSON renderer
      },
    },
  },
}

// Register plugin
registerPlugin(jsonTreePlugin)
```

### 8.2 Transform Plugin

```typescript
/**
 * Example: Math Expression Plugin
 *
 * Demonstrates:
 * - Content transformation
 * - Format-specific processing
 */
import { registerPlugin, type Plugin, type Content } from "@/components/Page/primitives/ContentRenderer"

const mathPlugin: Plugin<"markdown" | "mdx"> = {
  id: "katex",
  name: "KaTeX Math",
  version: "1.0.0",

  // Transform: Convert $...$ to KaTeX-rendered spans
  transform(content: Content<"markdown" | "mdx">) {
    if (typeof content.value !== "string") return content

    // Simple inline math: $...$ → katex rendered
    const transformed = content.value.replace(
      /\$([^$]+)\$/g,
      (_, math) => `<span class="katex">${renderKatex(math)}</span>`
    )

    return {
      ...content,
      value: transformed,
    }
  },

  // Validate: Check for balanced delimiters
  validate(content: Content<"markdown" | "mdx">) {
    if (typeof content.value !== "string") {
      return { valid: true, errors: [] }
    }

    const value = content.value
    const singleCount = (value.match(/\$/g) || []).length
    const doubleCount = (value.match(/\$\$/g) || []).length * 2

    const unbalanced = (singleCount - doubleCount) % 2 !== 0

    if (unbalanced) {
      return {
        valid: false,
        errors: [{
          code: "unbalanced_delimiters",
          message: "Math delimiters ($) are not balanced",
          severity: "warning",
        }],
      }
    }

    return { valid: true, errors: [] }
  },
}

registerPlugin(mathPlugin)
```

### 8.3 Validation Plugin

```typescript
/**
 * Example: Content Security Plugin
 *
 * Demonstrates:
 * - Validation without rendering
 * - Security checks
 */
import { registerPlugin, type Plugin, type Content } from "@/components/Page/primitives/ContentRenderer"

const securityPlugin: Plugin = {
  id: "content-security",
  name: "Content Security Validator",
  version: "1.0.0",

  validate(content: Content) {
    const errors: PluginValidationError[] = []

    // Check for script injection in HTML
    if (content.format === "html" && typeof content.value === "string") {
      if (/<script/i.test(content.value)) {
        errors.push({
          code: "script_detected",
          message: "Script tags are not allowed in HTML content",
          severity: "error",
        })
      }
      if (/on\w+=/i.test(content.value)) {
        errors.push({
          code: "event_handler_detected",
          message: "Inline event handlers are not allowed",
          severity: "error",
        })
      }
    }

    // Check for external image references
    if (content.format === "image" && typeof content.value === "string") {
      if (!content.value.startsWith("https://")) {
        errors.push({
          code: "insecure_url",
          message: "Image URLs must use HTTPS",
          severity: "warning",
        })
      }
    }

    return {
      valid: errors.filter(e => e.severity === "error").length === 0,
      errors,
    }
  },
}

registerPlugin(securityPlugin)
```

---

## 9. Testing Strategy

### 9.1 Unit Tests

```typescript
// pluginRegistry.test.ts

import {
  registerPlugin,
  unregisterPlugin,
  getPlugin,
  resolveRenderer,
  validateContent,
  transformContent,
  clearPlugins,
} from "./pluginRegistry"

describe("Plugin Registry", () => {
  afterEach(() => {
    clearPlugins()
  })

  describe("registerPlugin", () => {
    it("registers a plugin successfully", async () => {
      const plugin = { id: "test", renderers: {} }
      const registered = await registerPlugin(plugin)

      expect(registered.id).toBe("test")
      expect(registered.status).toBe("active")
      expect(getPlugin("test")).toBeDefined()
    })

    it("throws on duplicate registration", async () => {
      await registerPlugin({ id: "test", renderers: {} })

      await expect(
        registerPlugin({ id: "test", renderers: {} })
      ).rejects.toThrow("already registered")
    })

    it("allows replacement with replace: true", async () => {
      await registerPlugin({ id: "test", version: "1.0" })
      await registerPlugin({ id: "test", version: "2.0" }, { replace: true })

      expect(getPlugin("test")?.version).toBe("2.0")
    })
  })

  describe("resolveRenderer", () => {
    it("returns core renderer when no plugins", () => {
      const result = resolveRenderer("text")

      expect(result?.plugin).toBeNull()
      expect(result?.isOverride).toBe(false)
    })

    it("returns plugin renderer when available", async () => {
      const CustomRenderer = () => <div>Custom</div>
      await registerPlugin({
        id: "custom",
        renderers: {
          text: {
            format: "text",
            Component: CustomRenderer,
            meta: { pluginId: "custom", label: "Custom" },
          },
        },
      })

      const result = resolveRenderer("text")

      expect(result?.plugin?.id).toBe("custom")
      expect(result?.isOverride).toBe(true)
    })

    it("respects priority order", async () => {
      await registerPlugin({
        id: "low",
        renderers: {
          text: {
            format: "text",
            Component: () => <div>Low</div>,
            meta: { pluginId: "low", label: "Low", priority: 1 },
          },
        },
      })
      await registerPlugin({
        id: "high",
        renderers: {
          text: {
            format: "text",
            Component: () => <div>High</div>,
            meta: { pluginId: "high", label: "High", priority: 10 },
          },
        },
      })

      const result = resolveRenderer("text")

      expect(result?.plugin?.id).toBe("high")
    })
  })

  describe("transformContent", () => {
    it("applies transforms in priority order", async () => {
      await registerPlugin({
        id: "first",
        renderers: {
          text: {
            format: "text",
            Component: () => null,
            meta: { pluginId: "first", label: "First", priority: 10 },
          },
        },
        transform: (c) => ({ ...c, value: c.value + " [first]" }),
      })
      await registerPlugin({
        id: "second",
        renderers: {
          text: {
            format: "text",
            Component: () => null,
            meta: { pluginId: "second", label: "Second", priority: 5 },
          },
        },
        transform: (c) => ({ ...c, value: c.value + " [second]" }),
      })

      const result = transformContent({
        format: "text",
        value: "hello",
      })

      // First (priority 10) runs before Second (priority 5)
      expect(result.value).toBe("hello [first] [second]")
    })
  })

  describe("validateContent", () => {
    it("aggregates errors from multiple plugins", async () => {
      await registerPlugin({
        id: "validator1",
        validate: () => ({
          valid: false,
          errors: [{ code: "err1", message: "Error 1", severity: "error" }],
        }),
      })
      await registerPlugin({
        id: "validator2",
        validate: () => ({
          valid: false,
          errors: [{ code: "err2", message: "Error 2", severity: "warning" }],
        }),
      })

      const result = validateContent({ format: "text", value: "test" })

      expect(result.errors).toHaveLength(2)
      expect(result.errors[0].code).toBe("validator1:err1")
      expect(result.errors[1].code).toBe("validator2:err2")
    })
  })
})
```

### 9.2 Integration Tests

```typescript
// ContentRenderer.plugin.test.tsx

import { render, screen } from "@testing-library/react"
import { ContentRenderer, registerPlugin, clearPlugins } from "./index"

describe("ContentRenderer with plugins", () => {
  afterEach(() => {
    clearPlugins()
  })

  it("uses plugin renderer over core", async () => {
    const CustomText = () => <div data-testid="custom">Custom!</div>

    await registerPlugin({
      id: "custom-text",
      renderers: {
        text: {
          format: "text",
          Component: CustomText,
          meta: { pluginId: "custom-text", label: "Custom Text" },
        },
      },
    })

    render(
      <ContentRenderer content={{ format: "text", value: "Hello" }} />
    )

    expect(screen.getByTestId("custom")).toBeInTheDocument()
  })

  it("applies plugin transforms before rendering", async () => {
    await registerPlugin({
      id: "uppercase",
      transform: (content) => ({
        ...content,
        value: String(content.value).toUpperCase(),
      }),
    })

    render(
      <ContentRenderer content={{ format: "text", value: "hello" }} />
    )

    // Text should be uppercased by transform
    expect(screen.getByText("HELLO")).toBeInTheDocument()
  })
})
```

### 9.3 Manual Testing Checklist

| Test | Expected Result | Status |
|------|-----------------|--------|
| Register plugin | Plugin appears in getAllPlugins() | [ ] |
| Unregister plugin | Plugin removed, renderer falls back | [ ] |
| Plugin override | Plugin renderer used instead of core | [ ] |
| Priority resolution | Higher priority plugin wins | [ ] |
| Transform chain | Transforms applied in order | [ ] |
| Validation errors | Errors aggregated from all plugins | [ ] |
| Disable plugin | Plugin renderer no longer used | [ ] |
| Enable plugin | Plugin renderer restored | [ ] |
| onRegister hook | Hook called on registration | [ ] |
| onUnregister hook | Hook called on unregistration | [ ] |
| Error in hook | Plugin marked as error status | [ ] |
| Replace option | Existing plugin replaced | [ ] |

---

## 10. Plugin Authoring Guide (Summary)

The full plugin authoring guide will be created as `plugin-authoring-guide.md`.

**Key sections:**

1. **Quick Start** - Minimal plugin template
2. **Plugin Interface Reference** - Complete API documentation
3. **Renderer Guidelines** - How to create custom renderers
4. **Transform Best Practices** - Safe content transformation
5. **Validation Patterns** - Common validation scenarios
6. **Testing Plugins** - Unit and integration testing
7. **Distribution** - Packaging and sharing plugins
8. **Security Considerations** - Safe plugin development

---

## 11. Files Modified Summary

| File | Action | Purpose |
|------|--------|---------|
| `types.ts` | UPDATE | Add Plugin types |
| `pluginRegistry.ts` | CREATE | Plugin lifecycle management |
| `registry.ts` | UPDATE | Add plugin-aware resolution |
| `ContentRenderer.tsx` | UPDATE | Wire transform/validation |
| `index.ts` | UPDATE | Export plugin API |
| `plugin-authoring-guide.md` | CREATE | Developer documentation |

---

## 12. Phase 5 Completion Checklist

**Type Definitions (Part A):**
- [ ] `Plugin<T>` interface defined
- [ ] `PluginRenderer<T>` extends `Renderer<T>`
- [ ] `PluginValidationResult` type defined
- [ ] `RegisteredPlugin` runtime type defined

**Plugin Registry (Part B):**
- [ ] `pluginRegistry.ts` created
- [ ] `registerPlugin()` / `unregisterPlugin()` work
- [ ] Priority-based renderer resolution
- [ ] Transform chain execution
- [ ] Validation aggregation
- [ ] Event system for lifecycle hooks

**Integration (Part C):**
- [ ] `registry.ts` checks plugins first
- [ ] `ContentRenderer.tsx` applies transforms
- [ ] All plugin exports in `index.ts`

**Documentation (Part D):**
- [ ] Plugin authoring guide complete
- [ ] Example plugins documented
- [ ] Testing guide included

---

## 13. Transition to Future Phases

With Phase 5 complete:

1. **Plugin system is operational** for third-party extensions
2. **Core architecture is extensible** without modifying source
3. **Transform pipeline ready** for preprocessing plugins (math, diagrams)
4. **Validation framework ready** for content security plugins

### 13.1 Potential Future Plugins

| Plugin | Format | Purpose |
|--------|--------|---------|
| KaTeX | markdown/mdx | Math rendering |
| Mermaid | markdown/mdx | Diagrams |
| Prism | code | Alternative highlighter |
| PlantUML | svg | UML diagrams |
| ReactPlayer | video | Video embedding |
| Excalidraw | svg | Whiteboard diagrams |

---

## 14. Review Against Previous Phases

### 14.1 Phase 1 Alignment

| Phase 1 Feature | Phase 5 Impact |
|----------------|----------------|
| Core renderers | Preserved, plugins can override |
| Registry pattern | Extended with plugin layer |
| Format dispatch | Now checks plugins first |

### 14.2 Phase 2 Alignment

| Phase 2 Feature | Phase 5 Impact |
|----------------|----------------|
| Shiki transformers | Transform hook could be alternative |
| MDX compilation | Plugins could provide alternative compilers |
| CodeHighlight | Can be overridden by plugin |

### 14.3 Phase 3 Alignment

| Phase 3 Feature | Phase 5 Impact |
|----------------|----------------|
| Demo page | Add plugin demo section |
| StoryEditor preview | Plugins work in preview |
| All variants | Plugins receive variant prop |

### 14.4 Phase 4 Alignment

| Phase 4 Feature | Phase 5 Impact |
|----------------|----------------|
| Common re-exports | Plugin API should also re-export |
| Migration helpers | Plugins work with migrated code |
| renderContent compat | Transforms apply to compat helper |

---

## 15. Coherence Updates

Based on review of previous phases, these updates ensure coherence:

### 15.1 Update Common/ContentRenderer/index.ts

Add plugin re-exports to the Common re-export layer:

```typescript
// Re-export everything from Page/primitives for convenience
export * from "@/components/Page/primitives/ContentRenderer"
```

### 15.2 Update integrated-spec.md Section 10

Add implementation status:

```
### Phase 5: Plugin System [X] COMPLETE

1. ✅ Formalized `Plugin<T>` interface
2. ✅ Plugin registration API (registerPlugin/unregisterPlugin)
3. ✅ Priority-based renderer resolution
4. ✅ Transform and validation hooks
5. ✅ Plugin authoring guide
```

---

*Phase 5 Implementation Guide. Builds on Phases 1-4 foundation. Establishes the plugin extensibility system for ContentRenderer.*
