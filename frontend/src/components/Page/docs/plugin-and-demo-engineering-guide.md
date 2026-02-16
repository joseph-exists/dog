# ContentRenderer: Plugin & Demo Engineering Guide

> "The best way to predict the future is to invent it."
> — Alan Kay

This guide provides comprehensive instructions for creating plugins and demos that showcase the full power of the ContentRenderer system. It assumes Phase 5 (Plugin System) is complete and available.

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Creating Demos](#2-creating-demos)
3. [Creating Plugins](#3-creating-plugins)
4. [Advanced Plugin Patterns](#4-advanced-plugin-patterns)
5. [Integration Showcase Recipes](#5-integration-showcase-recipes)
6. [Performance & Best Practices](#6-performance--best-practices)
7. [Plugin Distribution](#7-plugin-distribution)

---

## 1. System Overview

### 1.1 Architecture Summary

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        ContentRenderer System                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐              │
│  │   Content    │───▶│  Transform   │───▶│   Validate   │              │
│  │   Input      │    │   Chain      │    │   Pipeline   │              │
│  └──────────────┘    └──────────────┘    └──────────────┘              │
│                              │                   │                       │
│                              ▼                   ▼                       │
│                     ┌──────────────────────────────────┐                │
│                     │       Renderer Resolution        │                │
│                     │  (Plugin Registry → Core Registry)│                │
│                     └──────────────────────────────────┘                │
│                              │                                           │
│         ┌────────────────────┼────────────────────┐                     │
│         ▼                    ▼                    ▼                     │
│  ┌─────────────┐    ┌─────────────────┐    ┌─────────────┐             │
│  │ Core        │    │ Plugin          │    │ Fallback    │             │
│  │ Renderers   │    │ Renderers       │    │ Renderer    │             │
│  │ (8 formats) │    │ (extensible)    │    │             │             │
│  └─────────────┘    └─────────────────┘    └─────────────┘             │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Extension Points

| Extension Point | What It Enables | Use Cases |
|-----------------|-----------------|-----------|
| **Custom Renderer** | New format visualization | Interactive charts, 3D models |
| **Transform Hook** | Content preprocessing | Math notation, macro expansion |
| **Validation Hook** | Content verification | Security scanning, schema validation |
| **Variant Handling** | Layout customization | Full-bleed images, responsive code |

### 1.3 Core Imports

```typescript
import {
  // Core component
  ContentRenderer,

  // Plugin API
  registerPlugin,
  unregisterPlugin,
  getAllPlugins,

  // Types
  type Plugin,
  type PluginRenderer,
  type Content,
  type ContentFormat,
  type ContentVariant,
  type ContentProps,
  type PluginValidationResult,
} from "@/components/Common/ContentRenderer"
```

---

## 2. Creating Demos

### 2.1 Demo Architecture

Demos showcase ContentRenderer capabilities in isolated, interactive environments.

```
@/components/Demo/
├── ContentRendererDemo.tsx      # Main demo component
├── ContentRendererExamples.ts   # Sample content library
├── PluginShowcase/              # Plugin-specific demos
│   ├── index.tsx
│   ├── MathDemo.tsx
│   ├── DiagramDemo.tsx
│   ├── InteractiveDemo.tsx
│   └── ThemeDemo.tsx
└── test-files/                  # Static test assets
    ├── *.svg
    ├── *.md
    └── *.json
```

### 2.2 Basic Demo Template

```typescript
/**
 * Demo Template - Showcases a specific ContentRenderer capability
 */
import { useState } from "react"
import {
  ContentRenderer,
  type Content,
  type ContentVariant,
} from "@/components/Common/ContentRenderer"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

interface DemoExample {
  id: string
  label: string
  content: Content
  description: string
}

interface DemoProps {
  title: string
  description: string
  examples: DemoExample[]
}

export function FeatureDemo({ title, description, examples }: DemoProps) {
  const [activeExample, setActiveExample] = useState(examples[0]?.id)
  const [variant, setVariant] = useState<ContentVariant>("card")

  const current = examples.find((e) => e.id === activeExample)

  return (
    <div className="space-y-6">
      <header>
        <h2 className="text-2xl font-bold">{title}</h2>
        <p className="text-muted-foreground">{description}</p>
      </header>

      <Tabs value={activeExample} onValueChange={setActiveExample}>
        <TabsList>
          {examples.map((ex) => (
            <TabsTrigger key={ex.id} value={ex.id}>
              {ex.label}
            </TabsTrigger>
          ))}
        </TabsList>

        {examples.map((ex) => (
          <TabsContent key={ex.id} value={ex.id}>
            <div className="grid gap-6 lg:grid-cols-2">
              {/* Live Preview */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Preview</CardTitle>
                </CardHeader>
                <CardContent>
                  <ContentRenderer
                    content={{ ...ex.content, metadata: { ...ex.content.metadata, variant } }}
                    safeMode={true}
                  />
                </CardContent>
              </Card>

              {/* Source View */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Source</CardTitle>
                </CardHeader>
                <CardContent>
                  <pre className="bg-muted p-4 rounded text-xs overflow-auto">
                    {JSON.stringify(ex.content, null, 2)}
                  </pre>
                </CardContent>
              </Card>
            </div>

            <p className="mt-4 text-sm text-muted-foreground">
              {ex.description}
            </p>
          </TabsContent>
        ))}
      </Tabs>
    </div>
  )
}
```

### 2.3 Interactive Demo with Live Editing

```typescript
/**
 * Interactive Demo - Live editing with instant preview
 */
import { useState, useMemo } from "react"
import {
  ContentRenderer,
  type Content,
  type ContentFormat,
} from "@/components/Common/ContentRenderer"
import { Textarea } from "@/components/ui/textarea"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

const EDITABLE_FORMATS: ContentFormat[] = [
  "text",
  "markdown",
  "html",
  "json",
  "code",
  "svg",
  "mdx",
]

const STARTER_CONTENT: Record<ContentFormat, string> = {
  text: "Hello, ContentRenderer!",
  markdown: "# Hello World\n\nThis is **markdown** with `code`.",
  html: "<h1>Hello</h1><p>This is <strong>HTML</strong> content.</p>",
  json: '{\n  "message": "Hello",\n  "count": 42\n}',
  code: 'function greet(name: string) {\n  return `Hello, ${name}!`;\n}',
  svg: '<svg viewBox="0 0 100 100"><circle cx="50" cy="50" r="40" fill="blue"/></svg>',
  mdx: "# MDX Content\n\nThis is **MDX** with code:\n\n```ts\nconst x = 1;\n```",
  image: "https://picsum.photos/400/300",
  yaml: "key: value",
  audio: "",
  video: "",
  empty: "",
  unknown: "",
  test: "",
}

export function InteractiveDemo() {
  const [format, setFormat] = useState<ContentFormat>("markdown")
  const [value, setValue] = useState(STARTER_CONTENT.markdown)
  const [error, setError] = useState<string | null>(null)

  // Build content object
  const content = useMemo<Content>(() => ({
    format,
    value,
    metadata: {
      variant: "card",
      options: format === "code" ? { language: "typescript", lineNumbers: true } : undefined,
    },
  }), [format, value])

  // Handle format change
  const handleFormatChange = (newFormat: ContentFormat) => {
    setFormat(newFormat)
    setValue(STARTER_CONTENT[newFormat] || "")
    setError(null)
  }

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      {/* Editor Panel */}
      <div className="space-y-4">
        <div className="flex gap-4">
          <Select value={format} onValueChange={handleFormatChange}>
            <SelectTrigger className="w-[180px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {EDITABLE_FORMATS.map((f) => (
                <SelectItem key={f} value={f}>
                  {f.toUpperCase()}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <Textarea
          value={value}
          onChange={(e) => setValue(e.target.value)}
          className="min-h-[400px] font-mono text-sm"
          placeholder={`Enter ${format} content...`}
        />

        {error && (
          <div className="text-sm text-destructive">{error}</div>
        )}
      </div>

      {/* Preview Panel */}
      <div className="border rounded-lg p-4 bg-background">
        <div className="text-xs text-muted-foreground uppercase mb-2">
          Live Preview
        </div>
        <ContentRenderer content={content} safeMode={true} />
      </div>
    </div>
  )
}
```

### 2.4 Variant Gallery Demo

```typescript
/**
 * Variant Gallery - Shows all 9 variants for a single content piece
 */
import {
  ContentRenderer,
  type Content,
  type ContentVariant,
} from "@/components/Common/ContentRenderer"
import { Badge } from "@/components/ui/badge"

const ALL_VARIANTS: Array<{ variant: ContentVariant; description: string }> = [
  { variant: "inline", description: "Compact, no scroll" },
  { variant: "card", description: "Bounded height, scrollable" },
  { variant: "page", description: "Full layout, headings" },
  { variant: "tooltip", description: "Very small, truncated" },
  { variant: "preview", description: "Medium size, read-only" },
  { variant: "embed", description: "Nested context" },
  { variant: "modal", description: "Centered, backdrop" },
  { variant: "thumbnail", description: "Fixed dimensions" },
  { variant: "background", description: "Decorative layer" },
]

interface VariantGalleryProps {
  content: Content
}

export function VariantGallery({ content }: VariantGalleryProps) {
  return (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold">All Variants</h3>

      <div className="grid gap-4">
        {ALL_VARIANTS.map(({ variant, description }) => (
          <div
            key={variant}
            className={`border rounded-lg p-4 ${
              variant === "background" ? "relative min-h-[100px]" : ""
            }`}
          >
            <div className="flex items-center gap-2 mb-3">
              <Badge>{variant}</Badge>
              <span className="text-sm text-muted-foreground">{description}</span>
            </div>

            <ContentRenderer
              content={{
                ...content,
                metadata: { ...content.metadata, variant },
              }}
              safeMode={true}
            />
          </div>
        ))}
      </div>
    </div>
  )
}
```

### 2.5 Plugin Showcase Demo

```typescript
/**
 * Plugin Showcase - Demonstrates registered plugins
 */
import { useEffect, useState } from "react"
import {
  ContentRenderer,
  getAllPlugins,
  type RegisteredPlugin,
  type Content,
} from "@/components/Common/ContentRenderer"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

export function PluginShowcase() {
  const [plugins, setPlugins] = useState<RegisteredPlugin[]>([])

  useEffect(() => {
    setPlugins(getAllPlugins())
  }, [])

  if (plugins.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        No plugins registered. Register a plugin to see it here.
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Registered Plugins</h2>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {plugins.map((plugin) => (
          <Card key={plugin.id}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">
                  {plugin.name || plugin.id}
                </CardTitle>
                <Badge variant={plugin.status === "active" ? "default" : "secondary"}>
                  {plugin.status}
                </Badge>
              </div>
              {plugin.version && (
                <span className="text-sm text-muted-foreground">
                  v{plugin.version}
                </span>
              )}
            </CardHeader>
            <CardContent>
              {plugin.description && (
                <p className="text-sm text-muted-foreground mb-4">
                  {plugin.description}
                </p>
              )}

              {/* Show supported formats */}
              {plugin.renderers && (
                <div className="space-y-2">
                  <span className="text-xs uppercase text-muted-foreground">
                    Formats
                  </span>
                  <div className="flex flex-wrap gap-1">
                    {Object.keys(plugin.renderers).map((format) => (
                      <Badge key={format} variant="outline" className="text-xs">
                        {format}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {/* Show capabilities */}
              <div className="flex gap-2 mt-4">
                {plugin.transform && (
                  <Badge variant="outline" className="text-xs">Transform</Badge>
                )}
                {plugin.validate && (
                  <Badge variant="outline" className="text-xs">Validate</Badge>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
```

---

## 3. Creating Plugins

### 3.1 Plugin Anatomy

Every plugin implements the `Plugin<T>` interface:

```typescript
interface Plugin<T extends ContentFormat = ContentFormat> {
  // Identity
  id: string                    // Unique identifier
  version?: string              // Semantic version
  name?: string                 // Display name
  description?: string          // What this plugin does

  // Capabilities
  renderers?: Partial<PluginRendererRegistry>  // Custom renderers
  validate?(content: Content<T>): PluginValidationResult
  transform?(content: Content<T>): Content<T>

  // Lifecycle
  onRegister?(): void | Promise<void>
  onUnregister?(): void
}
```

### 3.2 Minimal Plugin Template

```typescript
/**
 * Minimal Plugin - Starting point for new plugins
 */
import { registerPlugin, type Plugin } from "@/components/Common/ContentRenderer"

const myPlugin: Plugin = {
  id: "my-plugin",
  version: "1.0.0",
  name: "My Plugin",
  description: "A minimal example plugin",
}

// Register on module load
registerPlugin(myPlugin)

export { myPlugin }
```

### 3.3 Renderer Plugin Template

```typescript
/**
 * Renderer Plugin - Provides custom format rendering
 */
import { registerPlugin, type Plugin, type ContentProps } from "@/components/Common/ContentRenderer"

// Custom renderer component
const CustomRenderer: React.FC<ContentProps<"json">> = ({
  content,
  variant,
  className,
}) => {
  const data = typeof content.value === "string"
    ? JSON.parse(content.value)
    : content.value

  return (
    <div className={className}>
      {/* Custom visualization */}
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </div>
  )
}

const rendererPlugin: Plugin<"json"> = {
  id: "json-enhanced",
  version: "1.0.0",
  name: "Enhanced JSON Viewer",
  description: "Interactive JSON tree with search and filtering",

  renderers: {
    json: {
      format: "json",
      Component: CustomRenderer,
      meta: {
        pluginId: "json-enhanced",
        label: "Enhanced JSON",
        priority: 10, // Higher than core (priority -1)
      },
    },
  },
}

registerPlugin(rendererPlugin)
export { rendererPlugin }
```

### 3.4 Transform Plugin Template

```typescript
/**
 * Transform Plugin - Preprocesses content before rendering
 */
import {
  registerPlugin,
  type Plugin,
  type Content,
} from "@/components/Common/ContentRenderer"

// Transform function
function expandMacros(content: Content<"markdown" | "mdx">): Content<"markdown" | "mdx"> {
  if (typeof content.value !== "string") return content

  // Example: Expand [[DATE]] to current date
  const expanded = content.value.replace(
    /\[\[DATE\]\]/g,
    new Date().toLocaleDateString()
  )

  // Example: Expand [[USER:name]] to link
  const withLinks = expanded.replace(
    /\[\[USER:(\w+)\]\]/g,
    (_, name) => `[@${name}](/users/${name})`
  )

  return {
    ...content,
    value: withLinks,
  }
}

const macroPlugin: Plugin<"markdown" | "mdx"> = {
  id: "macro-expander",
  version: "1.0.0",
  name: "Macro Expander",
  description: "Expands [[MACRO]] syntax in markdown/mdx",

  transform: expandMacros,
}

registerPlugin(macroPlugin)
export { macroPlugin }
```

### 3.5 Validation Plugin Template

```typescript
/**
 * Validation Plugin - Checks content before rendering
 */
import {
  registerPlugin,
  type Plugin,
  type Content,
  type PluginValidationResult,
  type PluginValidationError,
} from "@/components/Common/ContentRenderer"

function validateContent(content: Content): PluginValidationResult {
  const errors: PluginValidationError[] = []

  // Check for empty content
  if (!content.value || (typeof content.value === "string" && !content.value.trim())) {
    errors.push({
      code: "empty_content",
      message: "Content is empty",
      severity: "warning",
    })
  }

  // Check JSON validity
  if (content.format === "json" && typeof content.value === "string") {
    try {
      JSON.parse(content.value)
    } catch {
      errors.push({
        code: "invalid_json",
        message: "JSON syntax error",
        severity: "error",
      })
    }
  }

  // Check for forbidden patterns
  if (typeof content.value === "string") {
    if (/<script/i.test(content.value)) {
      errors.push({
        code: "script_detected",
        message: "Script tags are not allowed",
        severity: "error",
      })
    }
  }

  return {
    valid: errors.filter((e) => e.severity === "error").length === 0,
    errors,
  }
}

const securityPlugin: Plugin = {
  id: "content-security",
  version: "1.0.0",
  name: "Content Security",
  description: "Validates content for security issues",

  validate: validateContent,
}

registerPlugin(securityPlugin)
export { securityPlugin }
```

### 3.6 Full-Featured Plugin Template

```typescript
/**
 * Full-Featured Plugin - All capabilities demonstrated
 */
import { registerPlugin, type Plugin, type ContentProps } from "@/components/Common/ContentRenderer"

// State for this plugin
let renderCount = 0

// Custom renderer
const DebugRenderer: React.FC<ContentProps<"text">> = ({ content, variant }) => {
  renderCount++

  return (
    <div className="border-2 border-dashed border-yellow-500 p-4">
      <div className="text-xs text-yellow-600 mb-2">
        Debug Renderer | Render #{renderCount} | Variant: {variant}
      </div>
      <div className="whitespace-pre-wrap">{String(content.value)}</div>
    </div>
  )
}

const debugPlugin: Plugin<"text"> = {
  id: "debug-renderer",
  version: "1.0.0",
  name: "Debug Renderer",
  description: "Shows debug information around text content",

  renderers: {
    text: {
      format: "text",
      Component: DebugRenderer,
      meta: {
        pluginId: "debug-renderer",
        label: "Debug Text",
        priority: 100, // Very high priority for debugging
      },
    },
  },

  transform(content) {
    // Add transform timestamp
    return {
      ...content,
      value: `[${new Date().toISOString()}]\n${content.value}`,
    }
  },

  validate(content) {
    const errors = []

    if (typeof content.value === "string" && content.value.length > 10000) {
      errors.push({
        code: "content_too_long",
        message: "Content exceeds 10,000 characters",
        severity: "warning" as const,
      })
    }

    return { valid: true, errors }
  },

  onRegister() {
    console.log("Debug plugin registered")
    renderCount = 0
  },

  onUnregister() {
    console.log(`Debug plugin unregistered. Total renders: ${renderCount}`)
  },
}

registerPlugin(debugPlugin)
export { debugPlugin }
```

---

## 4. Advanced Plugin Patterns

### 4.1 Lazy-Loading Plugin Dependencies

```typescript
/**
 * Lazy-Loading Plugin - Loads heavy dependencies only when needed
 */
import { registerPlugin, type Plugin, type ContentProps } from "@/components/Common/ContentRenderer"
import { Suspense, lazy, useState, useEffect } from "react"

// Lazy-load the heavy component
const HeavyVisualization = lazy(() => import("./HeavyVisualization"))

// Wrapper that handles loading state
const LazyRenderer: React.FC<ContentProps<"json">> = (props) => {
  return (
    <Suspense fallback={<div className="animate-pulse h-32 bg-muted rounded" />}>
      <HeavyVisualization {...props} />
    </Suspense>
  )
}

const lazyPlugin: Plugin<"json"> = {
  id: "lazy-viz",
  name: "Lazy Visualization",

  renderers: {
    json: {
      format: "json",
      Component: LazyRenderer,
      meta: {
        pluginId: "lazy-viz",
        label: "Data Visualization",
        priority: 5,
      },
    },
  },

  async onRegister() {
    // Preload the module in the background
    import("./HeavyVisualization").catch(() => {
      console.warn("Failed to preload visualization module")
    })
  },
}

registerPlugin(lazyPlugin)
```

### 4.2 Stateful Plugin with React Context

```typescript
/**
 * Stateful Plugin - Maintains state across renders
 */
import { createContext, useContext, useState, type ReactNode } from "react"
import { registerPlugin, type Plugin, type ContentProps } from "@/components/Common/ContentRenderer"

// Plugin state context
interface PluginState {
  theme: "light" | "dark"
  setTheme: (theme: "light" | "dark") => void
  expandedIds: Set<string>
  toggleExpanded: (id: string) => void
}

const PluginContext = createContext<PluginState | null>(null)

// Provider component (wrap your app)
export function PluginStateProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<"light" | "dark">("light")
  const [expandedIds, setExpandedIds] = useState(new Set<string>())

  const toggleExpanded = (id: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

  return (
    <PluginContext.Provider value={{ theme, setTheme, expandedIds, toggleExpanded }}>
      {children}
    </PluginContext.Provider>
  )
}

// Renderer that uses plugin state
const StatefulRenderer: React.FC<ContentProps<"json">> = ({ content }) => {
  const state = useContext(PluginContext)

  if (!state) {
    return <div>Plugin state provider not found</div>
  }

  const contentId = content.id || "default"
  const isExpanded = state.expandedIds.has(contentId)

  return (
    <div className={state.theme === "dark" ? "bg-gray-900 text-white" : "bg-white"}>
      <button onClick={() => state.toggleExpanded(contentId)}>
        {isExpanded ? "Collapse" : "Expand"}
      </button>
      {isExpanded && (
        <pre>{JSON.stringify(content.value, null, 2)}</pre>
      )}
    </div>
  )
}

const statefulPlugin: Plugin<"json"> = {
  id: "stateful-json",
  renderers: {
    json: {
      format: "json",
      Component: StatefulRenderer,
      meta: { pluginId: "stateful-json", label: "Stateful JSON", priority: 15 },
    },
  },
}

registerPlugin(statefulPlugin)
```

### 4.3 Chain-Aware Transform Plugin

```typescript
/**
 * Chain-Aware Transform - Respects transform order and previous transforms
 */
import { registerPlugin, type Plugin, type Content } from "@/components/Common/ContentRenderer"

// Marker to track transform chain
const TRANSFORM_MARKER = "__transforms__"

interface TransformMetadata {
  [TRANSFORM_MARKER]?: string[]
}

function chainAwareTransform(content: Content<"markdown">): Content<"markdown"> {
  if (typeof content.value !== "string") return content

  // Get previous transforms
  const metadata = (content.metadata || {}) as TransformMetadata
  const previousTransforms = metadata[TRANSFORM_MARKER] || []

  // Skip if a conflicting transform ran
  if (previousTransforms.includes("conflicting-plugin")) {
    console.log("Skipping transform due to conflict")
    return content
  }

  // Apply transform
  const transformed = content.value.toUpperCase()

  // Mark our transform
  return {
    ...content,
    value: transformed,
    metadata: {
      ...content.metadata,
      [TRANSFORM_MARKER]: [...previousTransforms, "uppercase-transform"],
    },
  }
}

const chainPlugin: Plugin<"markdown"> = {
  id: "uppercase-transform",
  name: "Uppercase Transform",
  transform: chainAwareTransform,
}

registerPlugin(chainPlugin)
```

### 4.4 Multi-Format Plugin

```typescript
/**
 * Multi-Format Plugin - Handles multiple formats with shared logic
 */
import { registerPlugin, type Plugin, type ContentProps, type ContentFormat } from "@/components/Common/ContentRenderer"

// Shared rendering logic
function createWrapper(format: ContentFormat) {
  const WrappedRenderer: React.FC<ContentProps<typeof format>> = ({
    content,
    variant,
    className,
  }) => {
    return (
      <div className={`plugin-wrapper format-${format} ${className || ""}`}>
        <div className="plugin-header">
          Format: {format} | Variant: {variant}
        </div>
        <div className="plugin-content">
          {typeof content.value === "string" ? content.value : JSON.stringify(content.value)}
        </div>
      </div>
    )
  }

  return WrappedRenderer
}

const multiFormatPlugin: Plugin<"text" | "markdown" | "html"> = {
  id: "multi-format-wrapper",
  name: "Multi-Format Wrapper",
  description: "Adds consistent wrapper to multiple formats",

  renderers: {
    text: {
      format: "text",
      Component: createWrapper("text"),
      meta: { pluginId: "multi-format-wrapper", label: "Wrapped Text", priority: 5 },
    },
    markdown: {
      format: "markdown",
      Component: createWrapper("markdown"),
      meta: { pluginId: "multi-format-wrapper", label: "Wrapped Markdown", priority: 5 },
    },
    html: {
      format: "html",
      Component: createWrapper("html"),
      meta: { pluginId: "multi-format-wrapper", label: "Wrapped HTML", priority: 5 },
    },
  },
}

registerPlugin(multiFormatPlugin)
```

---

## 5. Integration Showcase Recipes

### 5.1 Math Rendering (KaTeX)

```typescript
/**
 * KaTeX Math Plugin - Renders LaTeX math expressions
 */
import { registerPlugin, type Plugin, type ContentProps } from "@/components/Common/ContentRenderer"
import katex from "katex"
import "katex/dist/katex.min.css"

// Transform: Convert $...$ to KaTeX HTML
function transformMath(content) {
  if (typeof content.value !== "string") return content

  let transformed = content.value

  // Block math: $$...$$
  transformed = transformed.replace(
    /\$\$([^$]+)\$\$/g,
    (_, math) => {
      try {
        return `<div class="katex-block">${katex.renderToString(math, { displayMode: true })}</div>`
      } catch {
        return `<span class="katex-error">${math}</span>`
      }
    }
  )

  // Inline math: $...$
  transformed = transformed.replace(
    /\$([^$]+)\$/g,
    (_, math) => {
      try {
        return katex.renderToString(math, { displayMode: false })
      } catch {
        return `<span class="katex-error">${math}</span>`
      }
    }
  )

  return { ...content, value: transformed }
}

const katexPlugin: Plugin<"markdown" | "mdx"> = {
  id: "katex-math",
  version: "1.0.0",
  name: "KaTeX Math",
  description: "Renders LaTeX math expressions with KaTeX",
  transform: transformMath,
}

registerPlugin(katexPlugin)
```

### 5.2 Diagram Rendering (Mermaid)

```typescript
/**
 * Mermaid Diagram Plugin - Renders diagrams from text
 */
import { registerPlugin, type Plugin, type ContentProps } from "@/components/Common/ContentRenderer"
import { useEffect, useRef, useState } from "react"
import mermaid from "mermaid"

// Initialize mermaid
mermaid.initialize({
  startOnLoad: false,
  theme: "default",
  securityLevel: "strict",
})

const MermaidRenderer: React.FC<ContentProps<"code">> = ({ content, className }) => {
  const containerRef = useRef<HTMLDivElement>(null)
  const [svg, setSvg] = useState<string>("")
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const renderDiagram = async () => {
      if (!containerRef.current) return

      const code = typeof content.value === "string" ? content.value : ""

      try {
        const { svg } = await mermaid.render(
          `mermaid-${Date.now()}`,
          code
        )
        setSvg(svg)
        setError(null)
      } catch (err) {
        setError(err instanceof Error ? err.message : "Render failed")
      }
    }

    renderDiagram()
  }, [content.value])

  if (error) {
    return (
      <div className="border border-destructive p-4 rounded">
        <div className="text-sm text-destructive mb-2">Diagram Error</div>
        <pre className="text-xs">{error}</pre>
      </div>
    )
  }

  return (
    <div
      ref={containerRef}
      className={className}
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  )
}

// Validate mermaid syntax
function validateMermaid(content) {
  if (typeof content.value !== "string") {
    return { valid: true, errors: [] }
  }

  const errors = []
  const code = content.value.trim()

  // Basic syntax checks
  const validStarts = ["graph", "flowchart", "sequenceDiagram", "classDiagram", "stateDiagram", "erDiagram", "gantt", "pie", "journey"]
  const startsWithValid = validStarts.some((s) => code.startsWith(s))

  if (!startsWithValid) {
    errors.push({
      code: "invalid_diagram_type",
      message: `Diagram must start with: ${validStarts.join(", ")}`,
      severity: "error",
    })
  }

  return { valid: errors.length === 0, errors }
}

const mermaidPlugin: Plugin<"code"> = {
  id: "mermaid-diagrams",
  version: "1.0.0",
  name: "Mermaid Diagrams",
  description: "Renders Mermaid diagrams from code blocks",

  renderers: {
    code: {
      format: "code",
      Component: MermaidRenderer,
      meta: {
        pluginId: "mermaid-diagrams",
        label: "Mermaid Diagram",
        priority: 20, // Only activates for mermaid language
      },
    },
  },

  validate: validateMermaid,
}

registerPlugin(mermaidPlugin)
```

### 5.3 Interactive Code Playground

```typescript
/**
 * Code Playground Plugin - Execute and visualize code
 */
import { registerPlugin, type Plugin, type ContentProps } from "@/components/Common/ContentRenderer"
import { useState, useCallback } from "react"

const PlaygroundRenderer: React.FC<ContentProps<"code">> = ({ content, className }) => {
  const [output, setOutput] = useState<string>("")
  const [isRunning, setIsRunning] = useState(false)

  const code = typeof content.value === "string" ? content.value : ""
  const language = (content.metadata?.options as any)?.language || "javascript"

  const runCode = useCallback(async () => {
    setIsRunning(true)
    setOutput("")

    try {
      // Capture console.log output
      const logs: string[] = []
      const originalLog = console.log
      console.log = (...args) => logs.push(args.map(String).join(" "))

      // Execute (simplified - real implementation needs sandbox)
      if (language === "javascript" || language === "typescript") {
        // WARNING: This is unsafe - use a proper sandbox in production
        const fn = new Function(code)
        fn()
      }

      console.log = originalLog
      setOutput(logs.join("\n") || "(no output)")
    } catch (err) {
      setOutput(`Error: ${err instanceof Error ? err.message : String(err)}`)
    } finally {
      setIsRunning(false)
    }
  }, [code, language])

  return (
    <div className={`border rounded-lg overflow-hidden ${className || ""}`}>
      {/* Code display */}
      <div className="bg-muted p-4">
        <pre className="text-sm font-mono">{code}</pre>
      </div>

      {/* Controls */}
      <div className="flex items-center gap-2 p-2 border-t bg-background">
        <button
          onClick={runCode}
          disabled={isRunning}
          className="px-3 py-1 bg-primary text-primary-foreground rounded text-sm"
        >
          {isRunning ? "Running..." : "▶ Run"}
        </button>
        <span className="text-xs text-muted-foreground">{language}</span>
      </div>

      {/* Output */}
      {output && (
        <div className="p-4 border-t bg-black text-green-400 font-mono text-sm">
          <pre>{output}</pre>
        </div>
      )}
    </div>
  )
}

const playgroundPlugin: Plugin<"code"> = {
  id: "code-playground",
  version: "1.0.0",
  name: "Code Playground",
  description: "Interactive code execution environment",

  renderers: {
    code: {
      format: "code",
      Component: PlaygroundRenderer,
      meta: {
        pluginId: "code-playground",
        label: "Playground",
        priority: 15,
      },
    },
  },
}

registerPlugin(playgroundPlugin)
```

### 5.4 Collaborative Annotations

```typescript
/**
 * Annotations Plugin - Add comments and highlights to content
 */
import { registerPlugin, type Plugin, type ContentProps } from "@/components/Common/ContentRenderer"
import { useState } from "react"

interface Annotation {
  id: string
  startOffset: number
  endOffset: number
  text: string
  author: string
  timestamp: number
}

const AnnotatedRenderer: React.FC<ContentProps<"text" | "markdown">> = ({
  content,
  className,
}) => {
  const [annotations, setAnnotations] = useState<Annotation[]>([])
  const [selection, setSelection] = useState<{ start: number; end: number } | null>(null)

  const value = typeof content.value === "string" ? content.value : ""

  const handleMouseUp = () => {
    const sel = window.getSelection()
    if (sel && sel.rangeCount > 0) {
      const range = sel.getRangeAt(0)
      setSelection({
        start: range.startOffset,
        end: range.endOffset,
      })
    }
  }

  const addAnnotation = (text: string) => {
    if (!selection) return

    setAnnotations((prev) => [
      ...prev,
      {
        id: `ann-${Date.now()}`,
        startOffset: selection.start,
        endOffset: selection.end,
        text,
        author: "User",
        timestamp: Date.now(),
      },
    ])
    setSelection(null)
  }

  return (
    <div className={className}>
      {/* Content with annotation highlights */}
      <div
        onMouseUp={handleMouseUp}
        className="prose prose-sm"
      >
        {value}
      </div>

      {/* Selection popup */}
      {selection && (
        <div className="fixed bg-popover border rounded shadow-lg p-2">
          <input
            type="text"
            placeholder="Add annotation..."
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                addAnnotation(e.currentTarget.value)
              }
            }}
            className="text-sm p-1 border rounded"
          />
        </div>
      )}

      {/* Annotations sidebar */}
      {annotations.length > 0 && (
        <div className="mt-4 border-t pt-4">
          <h4 className="text-sm font-medium mb-2">Annotations</h4>
          {annotations.map((ann) => (
            <div key={ann.id} className="text-xs bg-muted p-2 rounded mb-1">
              <span className="font-medium">{ann.author}:</span> {ann.text}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

const annotationsPlugin: Plugin<"text" | "markdown"> = {
  id: "annotations",
  version: "1.0.0",
  name: "Collaborative Annotations",
  description: "Add comments and highlights to content",

  renderers: {
    text: {
      format: "text",
      Component: AnnotatedRenderer,
      meta: { pluginId: "annotations", label: "Annotated Text", priority: 10 },
    },
    markdown: {
      format: "markdown",
      Component: AnnotatedRenderer,
      meta: { pluginId: "annotations", label: "Annotated Markdown", priority: 10 },
    },
  },
}

registerPlugin(annotationsPlugin)
```

---

## 6. Performance & Best Practices

### 6.1 Plugin Performance Guidelines

```typescript
/**
 * Performance Best Practices
 */

// ✅ DO: Memoize expensive computations
const OptimizedRenderer: React.FC<ContentProps<"json">> = ({ content }) => {
  const parsed = useMemo(() => {
    return typeof content.value === "string"
      ? JSON.parse(content.value)
      : content.value
  }, [content.value])

  return <JsonTree data={parsed} />
}

// ✅ DO: Use React.memo for pure renderers
const PureRenderer = React.memo<ContentProps<"text">>(({ content }) => {
  return <div>{content.value}</div>
})

// ✅ DO: Lazy-load heavy dependencies
const LazyComponent = lazy(() => import("./HeavyComponent"))

// ❌ DON'T: Parse on every render
const BadRenderer: React.FC<ContentProps<"json">> = ({ content }) => {
  const parsed = JSON.parse(String(content.value)) // Parses every render!
  return <JsonTree data={parsed} />
}

// ❌ DON'T: Create functions in render
const BadRenderer2: React.FC<ContentProps<"text">> = ({ content }) => {
  return (
    <button onClick={() => console.log(content.value)}> {/* New function every render */}
      Click
    </button>
  )
}
```

### 6.2 Transform Performance

```typescript
/**
 * Transform Performance Best Practices
 */

// ✅ DO: Short-circuit early
function efficientTransform(content: Content): Content {
  // Skip non-applicable formats immediately
  if (content.format !== "markdown") return content

  // Skip if already processed
  if ((content.metadata as any)?.__transformed) return content

  // Do the work
  return transformContent(content)
}

// ✅ DO: Use caching for expensive transforms
const transformCache = new Map<string, Content>()

function cachedTransform(content: Content): Content {
  const cacheKey = `${content.format}:${hashContent(content.value)}`

  if (transformCache.has(cacheKey)) {
    return transformCache.get(cacheKey)!
  }

  const result = expensiveTransform(content)
  transformCache.set(cacheKey, result)

  // Limit cache size
  if (transformCache.size > 100) {
    const firstKey = transformCache.keys().next().value
    transformCache.delete(firstKey)
  }

  return result
}

// ❌ DON'T: Do expensive work unconditionally
function slowTransform(content: Content): Content {
  // This runs for ALL content, even non-applicable formats
  const parsed = expensiveParse(content.value)
  // ...
}
```

### 6.3 Validation Performance

```typescript
/**
 * Validation Performance Best Practices
 */

// ✅ DO: Return early on first error if that's sufficient
function fastValidation(content: Content): PluginValidationResult {
  if (!content.value) {
    return {
      valid: false,
      errors: [{ code: "empty", message: "Content is empty", severity: "error" }],
    }
  }

  // Only continue if basic check passes
  return thoroughValidation(content)
}

// ✅ DO: Use severity levels appropriately
function prioritizedValidation(content: Content): PluginValidationResult {
  const errors: PluginValidationError[] = []

  // Critical errors first (stop rendering)
  if (isMalformed(content)) {
    errors.push({ code: "malformed", message: "...", severity: "error" })
    return { valid: false, errors } // Don't check more
  }

  // Warnings last (don't stop rendering)
  if (isSuboptimal(content)) {
    errors.push({ code: "suboptimal", message: "...", severity: "warning" })
  }

  return { valid: true, errors }
}
```

---

## 7. Plugin Distribution

### 7.1 Package Structure

```
my-content-plugin/
├── package.json
├── README.md
├── src/
│   ├── index.ts          # Main exports
│   ├── plugin.ts         # Plugin definition
│   ├── renderers/        # Custom renderers
│   │   └── MyRenderer.tsx
│   ├── transforms/       # Transform functions
│   │   └── myTransform.ts
│   └── validators/       # Validation functions
│       └── myValidator.ts
├── dist/                 # Built files
└── examples/             # Usage examples
```

### 7.2 Package.json Template

```json
{
  "name": "@my-org/content-plugin-example",
  "version": "1.0.0",
  "description": "Example plugin for ContentRenderer",
  "main": "dist/index.js",
  "module": "dist/index.mjs",
  "types": "dist/index.d.ts",
  "exports": {
    ".": {
      "import": "./dist/index.mjs",
      "require": "./dist/index.js",
      "types": "./dist/index.d.ts"
    }
  },
  "peerDependencies": {
    "react": "^18.0.0",
    "@your-org/content-renderer": "^1.0.0"
  },
  "keywords": [
    "content-renderer",
    "plugin"
  ]
}
```

### 7.3 Plugin Registration Patterns

```typescript
/**
 * Auto-Register Pattern
 * Plugin registers itself on import
 */
// my-plugin/src/index.ts
import { registerPlugin } from "@your-org/content-renderer"
import { myPlugin } from "./plugin"

// Auto-register on import
registerPlugin(myPlugin)

export { myPlugin }
export * from "./types"

// Usage:
// import "@my-org/content-plugin-example" // Auto-registers
```

```typescript
/**
 * Manual Register Pattern
 * Consumer controls when plugin registers
 */
// my-plugin/src/index.ts
import { registerPlugin } from "@your-org/content-renderer"
import { myPlugin } from "./plugin"

export function register() {
  return registerPlugin(myPlugin)
}

export function unregister() {
  return unregisterPlugin(myPlugin.id)
}

export { myPlugin }

// Usage:
// import { register } from "@my-org/content-plugin-example"
// register() // Explicit registration
```

```typescript
/**
 * Configurable Plugin Pattern
 * Plugin accepts configuration
 */
// my-plugin/src/index.ts
import { registerPlugin, type Plugin } from "@your-org/content-renderer"

interface PluginConfig {
  theme?: "light" | "dark"
  maxLength?: number
}

export function createPlugin(config: PluginConfig = {}): Plugin {
  return {
    id: "configurable-plugin",
    // ... use config in implementation
  }
}

export function register(config?: PluginConfig) {
  return registerPlugin(createPlugin(config))
}

// Usage:
// import { register } from "@my-org/content-plugin-example"
// register({ theme: "dark", maxLength: 5000 })
```

---

## Appendix A: Quick Reference

### Import Cheat Sheet

```typescript
// Core
import { ContentRenderer } from "@/components/Common/ContentRenderer"

// Plugin API
import {
  registerPlugin,
  unregisterPlugin,
  getPlugin,
  getAllPlugins,
  hasPlugin,
  disablePlugin,
  enablePlugin,
} from "@/components/Common/ContentRenderer"

// Types
import type {
  Plugin,
  PluginRenderer,
  RegisteredPlugin,
  Content,
  ContentFormat,
  ContentVariant,
  ContentProps,
  PluginValidationResult,
  PluginValidationError,
} from "@/components/Common/ContentRenderer"
```

### Plugin Lifecycle

```
registerPlugin() called
       │
       ▼
  onRegister() hook
       │
       ▼
  Plugin status: "active"
       │
       ├── (Content renders) ──▶ transform() ──▶ validate() ──▶ Renderer
       │
       ▼ (when unregistering)
  onUnregister() hook
       │
       ▼
  Plugin removed from registry
```

### Priority Resolution

```
Priority: Higher number = wins conflict

-1    Core renderers (always lowest)
 0    Default plugin priority
1-10  Low priority plugins
11-50 Normal priority plugins
51+   High priority plugins (debugging, override)
```

---

*Plugin & Demo Engineering Guide. For ContentRenderer v1 with Phase 5 Plugin System.*
