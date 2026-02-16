# Phase 3 Implementation Guide: Proving Ground

> "The proof of the pudding is in the eating."
> — Miguel de Cervantes

This guide provides step-by-step implementation instructions for Phase 3 of the ContentRenderer system. Phase 3 is the **Proving Ground** where we validate that all ContentRenderer functionality works correctly in real authoring and viewing contexts.

---

## 1. Phase 3 Objectives

> **Traceability:** This guide implements Phase 3 as defined in `integrated-spec.md` Section 14.3.
> It assumes Phase 1 (`status_phase1-implementation.md`) and Phase 2 (`phase2-implementation-guide.md`) are complete.

From integrated-spec Section 14.3:

1. **Demo page** - Create a dedicated demo showcasing all ContentRenderer formats
2. **StoryEditor integration** - Add ContentRenderer preview to the authoring experience
3. **Testing** - Validate all formats in authoring + viewing contexts
4. **Success validation** - Confirm success criteria are met

### 1.1 Success Criteria

Phase 3 is successful when:

- [ ] Author can use StoryEditor to add all content types to a story
- [ ] Viewer can play that story with smooth, well-designed rendering
- [ ] Experience is well-designed and sophisticated
- [ ] All 9 UX variants render correctly
- [ ] Shiki syntax highlighting works in markdown/code blocks
- [ ] MDX compiles and renders (runtime path)

---

## 2. Prerequisites Checklist

Before implementing, verify:

- [x] Phase 1 complete (core renderers)
- [x] Phase 2 complete (MDX + Shiki transformers)
- [x] Demo framework exists (`/routes/_layout/demo.$slug.tsx`, `/config/demos.ts`)
- [x] StoryEditor exists (`/components/Story/StoryEditor/`)

### 2.1 Assumption

All Phase 2 features are working (this phase validates them):

**Shiki Transformers (Phase 2 Part A):**
- `lineNumbers` displays line numbers in code blocks
- `highlightLines` visually highlights specified lines
- `startLine` offsets line number display
- CSS classes `.shiki-line-numbers` and `.shiki-highlighted` styled

**MDX Renderer (Phase 2 Part B):**
- `useMDXCompiler` hook compiles MDX at runtime
- `MDXRenderer` handles both runtime and compiled paths
- `MDXComponents` whitelist filters in safeMode
- Code blocks within MDX use Shiki highlighting

---

## 3. Implementation Order

```
Part A: Demo Infrastructure
════════════════════════════════════════
1. Create ContentRendererDemo component
2. Add demo config for "content-renderer"
3. Build interactive format showcase

Part B: StoryEditor Integration
════════════════════════════════════════
4. Add content preview to NodeEditorForm
5. Extend format selector with new formats
6. Wire ContentRenderer for live preview

Part C: Validation & Polish
════════════════════════════════════════
7. Manual testing checklist execution
8. Success criteria validation
9. Document findings & edge cases
```

---

## 4. Part A: Demo Infrastructure

### 4.1 Files to Create

Per scratchpad constraints, request human approval for new file locations:

```
@/components/Demo/
├── ContentRendererDemo.tsx    # NEW: Main demo component
└── ContentRendererExamples.ts # NEW: Sample content for each format
```

**Note:** The `/components/Demo/` directory exists; adding files requires human approval per scratchpad constraint #4.

### 4.2 ContentRendererExamples.ts

**Purpose:** Provide sample content for each ContentFormat to enable demo page testing.

```typescript
/**
 * ContentRendererExamples - Sample content for demo/testing
 *
 * Provides realistic examples of each ContentFormat with various
 * metadata options to demonstrate all capabilities.
 */
import type { Content, ContentVariant } from "@/components/Page/primitives/ContentRenderer"

// ═══════════════════════════════════════════════════════════════════════════
// TEXT EXAMPLES
// ═══════════════════════════════════════════════════════════════════════════

export const textExamples: Content<"text">[] = [
  {
    format: "text",
    value: "Hello, World! This is plain text content with no formatting.",
    metadata: { variant: "card" },
  },
  {
    format: "text",
    value: "A longer text block that demonstrates\nmultiple lines\nwith whitespace preserved.",
    metadata: { variant: "page" },
  },
  {
    format: "text",
    value: "Inline snippet",
    metadata: { variant: "inline" },
  },
]

// ═══════════════════════════════════════════════════════════════════════════
// MARKDOWN EXAMPLES
// ═══════════════════════════════════════════════════════════════════════════

export const markdownExamples: Content<"markdown">[] = [
  {
    format: "markdown",
    value: `# Markdown Heading

This is a **bold** statement with *italic* emphasis.

## Code Block

\`\`\`typescript
function greet(name: string): string {
  return \`Hello, \${name}!\`;
}
\`\`\`

## List

- Item one
- Item two
- Item three

> A blockquote for emphasis.
`,
    metadata: { variant: "page" },
  },
  {
    format: "markdown",
    value: "**Bold** and *italic* inline markdown",
    metadata: { variant: "inline" },
  },
]

// ═══════════════════════════════════════════════════════════════════════════
// CODE EXAMPLES
// ═══════════════════════════════════════════════════════════════════════════

export const codeExamples: Content<"code">[] = [
  {
    format: "code",
    value: `function fibonacci(n: number): number {
  if (n <= 1) return n;
  return fibonacci(n - 1) + fibonacci(n - 2);
}

// Calculate first 10 Fibonacci numbers
for (let i = 0; i < 10; i++) {
  console.log(fibonacci(i));
}`,
    metadata: {
      variant: "card",
      options: {
        language: "typescript",
        lineNumbers: true,
        copyable: true,
        filename: "fibonacci.ts",
      },
    },
  },
  {
    format: "code",
    value: `const highlighted = true;
const notHighlighted = false;
const alsoHighlighted = true;`,
    metadata: {
      variant: "card",
      options: {
        language: "typescript",
        highlightLines: [1, 3],
        lineNumbers: true,
      },
    },
  },
  {
    format: "code",
    value: `// Starting from line 100
export function important() {
  return "This line is 102";
}`,
    metadata: {
      variant: "card",
      options: {
        language: "typescript",
        lineNumbers: true,
        startLine: 100,
      },
    },
  },
]

// ═══════════════════════════════════════════════════════════════════════════
// HTML EXAMPLES
// ═══════════════════════════════════════════════════════════════════════════

export const htmlExamples: Content<"html">[] = [
  {
    format: "html",
    value: `<article>
  <h2>HTML Content</h2>
  <p>This is <strong>sanitized HTML</strong> with <em>emphasis</em>.</p>
  <ul>
    <li>List item one</li>
    <li>List item two</li>
  </ul>
</article>`,
    metadata: { variant: "card" },
  },
  {
    format: "html",
    value: `<span style="color: blue;">Styled inline HTML</span>`,
    metadata: { variant: "inline" },
  },
]

// ═══════════════════════════════════════════════════════════════════════════
// JSON EXAMPLES
// ═══════════════════════════════════════════════════════════════════════════

export const jsonExamples: Content<"json">[] = [
  {
    format: "json",
    value: JSON.stringify({
      name: "ContentRenderer",
      version: "1.0.0",
      formats: ["text", "markdown", "html", "json", "code", "svg", "image", "mdx"],
      features: {
        variants: 9,
        themeSupport: true,
        safeMode: true,
      },
    }),
    metadata: {
      variant: "card",
      options: { viewMode: "text" },
    },
  },
  {
    format: "json",
    value: JSON.stringify({ status: "ok", count: 42 }),
    metadata: {
      variant: "inline",
      options: { viewMode: "text" },
    },
  },
]

// ═══════════════════════════════════════════════════════════════════════════
// SVG EXAMPLES
// ═══════════════════════════════════════════════════════════════════════════

export const svgExamples: Content<"svg">[] = [
  {
    format: "svg",
    value: `<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
  <circle cx="50" cy="50" r="40" fill="#3b82f6" />
  <text x="50" y="55" text-anchor="middle" fill="white" font-size="12">SVG</text>
</svg>`,
    metadata: {
      variant: "card",
      options: { inline: true },
    },
  },
  {
    format: "svg",
    value: `<svg viewBox="0 0 200 100" xmlns="http://www.w3.org/2000/svg">
  <rect x="10" y="10" width="80" height="80" fill="#ef4444" rx="8"/>
  <rect x="110" y="10" width="80" height="80" fill="#22c55e" rx="8"/>
</svg>`,
    metadata: {
      variant: "background",
      options: { inline: true },
    },
  },
]

// ═══════════════════════════════════════════════════════════════════════════
// IMAGE EXAMPLES
// ═══════════════════════════════════════════════════════════════════════════

export const imageExamples: Content<"image">[] = [
  {
    format: "image",
    value: "https://picsum.photos/400/300",
    metadata: {
      variant: "card",
      options: {
        alt: "Random image from Picsum",
        loading: "lazy",
      },
    },
  },
  {
    format: "image",
    value: "https://picsum.photos/100/100",
    metadata: {
      variant: "thumbnail",
      options: {
        alt: "Thumbnail image",
      },
    },
  },
]

// ═══════════════════════════════════════════════════════════════════════════
// MDX EXAMPLES
// ═══════════════════════════════════════════════════════════════════════════

export const mdxExamples: Content<"mdx">[] = [
  {
    format: "mdx",
    value: `# MDX Content

This is **MDX** with embedded components.

\`\`\`typescript
const greeting = "Hello from MDX!";
console.log(greeting);
\`\`\`

The code above will be syntax highlighted with Shiki.

## Features

- Markdown syntax
- JSX components (when enabled)
- Code highlighting
`,
    metadata: { variant: "page" },
  },
]

// ═══════════════════════════════════════════════════════════════════════════
// ALL EXAMPLES GROUPED
// ═══════════════════════════════════════════════════════════════════════════

export const allExamples = {
  text: textExamples,
  markdown: markdownExamples,
  code: codeExamples,
  html: htmlExamples,
  json: jsonExamples,
  svg: svgExamples,
  image: imageExamples,
  mdx: mdxExamples,
}

// ═══════════════════════════════════════════════════════════════════════════
// VARIANT DEMONSTRATION
// ═══════════════════════════════════════════════════════════════════════════

export const variantDemos: Array<{ variant: ContentVariant; description: string }> = [
  { variant: "inline", description: "Inline: compact, no scroll" },
  { variant: "card", description: "Card: bounded height, scrollable" },
  { variant: "page", description: "Page: full layout with headings" },
  { variant: "tooltip", description: "Tooltip: very small, truncated" },
  { variant: "preview", description: "Preview: medium size, read-only" },
  { variant: "embed", description: "Embed: nested context" },
  { variant: "modal", description: "Modal: centered, backdrop" },
  { variant: "thumbnail", description: "Thumbnail: fixed dimensions" },
  { variant: "background", description: "Background: decorative layer" },
]
```

### 4.3 ContentRendererDemo.tsx

**Purpose:** Interactive demo page for exploring all ContentRenderer capabilities.

```typescript
/**
 * ContentRendererDemo - Interactive showcase of ContentRenderer
 *
 * Features:
 * - Format selector tabs
 * - Variant picker
 * - Live preview with actual ContentRenderer
 * - Theme toggle (dark/light affects code themes)
 * - Safe mode toggle
 */
import { useState } from "react"
import {
  ContentRenderer,
  type Content,
  type ContentVariant,
  type ContentFormat,
} from "@/components/Page/primitives/ContentRenderer"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  allExamples,
  variantDemos,
} from "./ContentRendererExamples"

const FORMAT_TABS: Array<{ value: ContentFormat; label: string }> = [
  { value: "text", label: "Text" },
  { value: "markdown", label: "Markdown" },
  { value: "code", label: "Code" },
  { value: "html", label: "HTML" },
  { value: "json", label: "JSON" },
  { value: "svg", label: "SVG" },
  { value: "image", label: "Image" },
  { value: "mdx", label: "MDX" },
]

export function ContentRendererDemo() {
  const [activeFormat, setActiveFormat] = useState<ContentFormat>("text")
  const [selectedVariant, setSelectedVariant] = useState<ContentVariant>("card")
  const [safeMode, setSafeMode] = useState(true)
  const [exampleIndex, setExampleIndex] = useState(0)

  // Get examples for current format
  const examples = allExamples[activeFormat as keyof typeof allExamples] || []
  const currentExample = examples[exampleIndex] as Content | undefined

  // Create content with selected variant override
  const displayContent: Content | null = currentExample
    ? {
        ...currentExample,
        metadata: {
          ...currentExample.metadata,
          variant: selectedVariant,
        },
      }
    : null

  return (
    <div className="container mx-auto py-8 space-y-8">
      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-3xl font-bold">ContentRenderer Demo</h1>
        <p className="text-muted-foreground">
          Interactive showcase of all ContentRenderer formats and variants.
        </p>
      </div>

      {/* Controls */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Controls</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-6">
          {/* Variant Selector */}
          <div className="space-y-2">
            <Label>Variant</Label>
            <Select
              value={selectedVariant}
              onValueChange={(v) => setSelectedVariant(v as ContentVariant)}
            >
              <SelectTrigger className="w-[180px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {variantDemos.map(({ variant, description }) => (
                  <SelectItem key={variant} value={variant}>
                    {variant}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Example Selector */}
          <div className="space-y-2">
            <Label>Example</Label>
            <Select
              value={String(exampleIndex)}
              onValueChange={(v) => setExampleIndex(Number(v))}
            >
              <SelectTrigger className="w-[120px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {examples.map((_, i) => (
                  <SelectItem key={i} value={String(i)}>
                    Example {i + 1}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Safe Mode Toggle */}
          <div className="flex items-center space-x-2">
            <Switch
              id="safe-mode"
              checked={safeMode}
              onCheckedChange={setSafeMode}
            />
            <Label htmlFor="safe-mode">Safe Mode</Label>
          </div>
        </CardContent>
      </Card>

      {/* Format Tabs */}
      <Tabs
        value={activeFormat}
        onValueChange={(v) => {
          setActiveFormat(v as ContentFormat)
          setExampleIndex(0)
        }}
      >
        <TabsList className="flex-wrap h-auto">
          {FORMAT_TABS.map(({ value, label }) => (
            <TabsTrigger key={value} value={value}>
              {label}
            </TabsTrigger>
          ))}
        </TabsList>

        {FORMAT_TABS.map(({ value }) => (
          <TabsContent key={value} value={value} className="mt-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Preview */}
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">Preview</CardTitle>
                    <Badge variant="outline">{selectedVariant}</Badge>
                  </div>
                </CardHeader>
                <CardContent
                  className={
                    selectedVariant === "background"
                      ? "relative min-h-[200px]"
                      : ""
                  }
                >
                  {displayContent ? (
                    <ContentRenderer
                      content={displayContent}
                      safeMode={safeMode}
                    />
                  ) : (
                    <p className="text-muted-foreground">
                      No examples for this format.
                    </p>
                  )}
                </CardContent>
              </Card>

              {/* Source */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Source</CardTitle>
                </CardHeader>
                <CardContent>
                  <pre className="bg-muted p-4 rounded-md overflow-auto text-xs font-mono max-h-[400px]">
                    {displayContent
                      ? JSON.stringify(displayContent, null, 2)
                      : "null"}
                  </pre>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        ))}
      </Tabs>

      {/* Variant Gallery */}
      <Card>
        <CardHeader>
          <CardTitle>All Variants Gallery</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {variantDemos.map(({ variant, description }) => (
            <div key={variant} className="border rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <Badge>{variant}</Badge>
                <span className="text-sm text-muted-foreground">
                  {description}
                </span>
              </div>
              <div
                className={
                  variant === "background"
                    ? "relative h-24 border rounded"
                    : ""
                }
              >
                {currentExample && (
                  <ContentRenderer
                    content={{
                      ...currentExample,
                      metadata: {
                        ...currentExample.metadata,
                        variant,
                      },
                    }}
                    safeMode={safeMode}
                  />
                )}
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  )
}
```

### 4.4 Update demos.ts Config

**Location:** `@/config/demos.ts`

**Changes:** Add content-renderer demo config.

```typescript
// ADD to DEMOS record
"content-renderer": {
  slug: "content-renderer",
  title: "ContentRenderer Demo",
  description: "Interactive showcase of all ContentRenderer formats and variants.",
  roomId: "", // Not used for this demo
  autoRespond: false,
},
```

**Note:** This demo doesn't use the standard DemoPage component. We need either:
- Option A: Create a new route `/routes/_layout/content-renderer-demo.tsx`
- Option B: Modify DemoPage to conditionally render ContentRendererDemo

**Recommended:** Option A (new route) to avoid coupling.

### 4.5 Create Demo Route (Option A)

**Location:** `@/routes/_layout/content-renderer-demo.tsx`

```typescript
import { createFileRoute } from "@tanstack/react-router"
import { ContentRendererDemo } from "@/components/Demo/ContentRendererDemo"

export const Route = createFileRoute("/_layout/content-renderer-demo")({
  component: ContentRendererDemo,
})
```

---

## 5. Part B: StoryEditor Integration

### 5.1 Integration Points

The StoryEditor authoring experience needs ContentRenderer for:

1. **Live preview** while editing node content
2. **Extended format support** (code, svg, image, mdx)
3. **Format-specific editors** (different input UI per format)

### 5.2 Update NodeEditorForm.tsx

**Location:** `@/components/Story/StoryEditor/NodeEditor/NodeEditorForm.tsx`

**Current state:** Supports html, text, markdown, json with Select dropdown.

**Changes needed:**
1. Add new format options to Select
2. Add ContentRenderer preview panel
3. Wire format-specific input components

```typescript
/**
 * NodeEditorForm - Form for editing story node properties
 *
 * UPDATED for Phase 3:
 * - Extended format selector (text, html, markdown, json, code, svg, image, mdx)
 * - Live preview using ContentRenderer
 * - Format-specific hints
 */

import { useEffect, useState } from "react"
import type { ContentFormat, StoryNodePublic } from "@/client"
import { Checkbox } from "@/components/ui/checkbox"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { useUpdateNode } from "@/hooks/stories/useStoryNodes"
import RichTextEditor from "../../shared/RichTextEditor"
// NEW: Import ContentRenderer
import { ContentRenderer, type Content } from "@/components/Page/primitives/ContentRenderer"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import { ChevronDown, ChevronUp, Eye } from "lucide-react"
import { Button } from "@/components/ui/button"

interface NodeEditorFormProps {
  node: StoryNodePublic
  storyId: string
}

// Format descriptions for help text
const FORMAT_INFO: Record<ContentFormat, { label: string; hint: string }> = {
  text: { label: "Plain Text", hint: "Simple text with whitespace preserved" },
  html: { label: "HTML (Rich Text)", hint: "Rich text with formatting" },
  markdown: { label: "Markdown", hint: "Markdown syntax with code highlighting" },
  json: { label: "JSON", hint: "Structured data in JSON format" },
  code: { label: "Code", hint: "Syntax-highlighted code block" },
  svg: { label: "SVG", hint: "Scalable vector graphics" },
  image: { label: "Image", hint: "Image URL (external or data URI)" },
  mdx: { label: "MDX", hint: "Markdown with JSX components" },
  yaml: { label: "YAML", hint: "YAML configuration (future)" },
  audio: { label: "Audio", hint: "Audio content (future)" },
  video: { label: "Video", hint: "Video content (future)" },
  empty: { label: "Empty", hint: "No content" },
  unknown: { label: "Unknown", hint: "Unknown format" },
  test: { label: "Test", hint: "For testing purposes" },
}

// Formats available for selection (subset of all)
const SELECTABLE_FORMATS: ContentFormat[] = [
  "text",
  "html",
  "markdown",
  "json",
  "code",
  "svg",
  "image",
  "mdx",
]

const NodeEditorForm = ({ node, storyId }: NodeEditorFormProps) => {
  const updateNode = useUpdateNode(storyId, node.id)

  // Local state
  const [title, setTitle] = useState(node.title)
  const [content, setContent] = useState(node.content || "")
  const [contentFormat, setContentFormat] = useState<ContentFormat>(
    node.content_format || "text",
  )
  const [isStartNode, setIsStartNode] = useState(node.is_start_node || false)
  const [isEndNode, setIsEndNode] = useState(node.is_end_node || false)
  const [showPreview, setShowPreview] = useState(false)

  // Reset form when node changes
  useEffect(() => {
    setTitle(node.title)
    setContent(node.content || "")
    setContentFormat(node.content_format || "text")
    setIsStartNode(node.is_start_node || false)
    setIsEndNode(node.is_end_node || false)
  }, [node])

  // Auto-save handlers
  const handleTitleBlur = () => {
    if (title !== node.title) {
      updateNode.mutate({ title })
    }
  }

  const handleContentBlur = () => {
    if (content !== node.content) {
      updateNode.mutate({ content })
    }
  }

  const handleContentFormatChange = (format: ContentFormat) => {
    setContentFormat(format)
    updateNode.mutate({ content_format: format })
  }

  const handleStartNodeChange = (checked: boolean) => {
    setIsStartNode(checked)
    if (checked) setIsEndNode(false)
    updateNode.mutate({
      is_start_node: checked,
      is_end_node: checked ? false : isEndNode,
    })
  }

  const handleEndNodeChange = (checked: boolean) => {
    setIsEndNode(checked)
    if (checked) setIsStartNode(false)
    updateNode.mutate({
      is_end_node: checked,
      is_start_node: checked ? false : isStartNode,
    })
  }

  // Build Content object for preview
  const previewContent: Content = {
    format: contentFormat,
    value: content,
    metadata: { variant: "card" },
  }

  // Get placeholder based on format
  const getPlaceholder = (): string => {
    switch (contentFormat) {
      case "json":
        return '{"key": "value"}'
      case "code":
        return "// Enter your code here"
      case "svg":
        return '<svg viewBox="0 0 100 100">...</svg>'
      case "image":
        return "https://example.com/image.jpg"
      case "markdown":
      case "mdx":
        return "# Heading\n\nContent here..."
      default:
        return "Enter content..."
    }
  }

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="space-y-2">
        <Label htmlFor="title">Title</Label>
        <Input
          id="title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          onBlur={handleTitleBlur}
          placeholder="Node title"
        />
      </div>

      {/* Content Format */}
      <div className="space-y-2">
        <Label htmlFor="content_format">Content Format</Label>
        <Select value={contentFormat} onValueChange={handleContentFormatChange}>
          <SelectTrigger className="w-[250px]">
            <SelectValue placeholder="Select format" />
          </SelectTrigger>
          <SelectContent>
            {SELECTABLE_FORMATS.map((fmt) => (
              <SelectItem key={fmt} value={fmt}>
                {FORMAT_INFO[fmt]?.label || fmt}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <p className="text-xs text-muted-foreground">
          {FORMAT_INFO[contentFormat]?.hint}
        </p>
      </div>

      {/* Content Editor */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label>Content</Label>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowPreview(!showPreview)}
          >
            <Eye className="h-4 w-4 mr-1" />
            {showPreview ? "Hide" : "Show"} Preview
          </Button>
        </div>

        {contentFormat === "html" ? (
          <RichTextEditor
            content={content}
            onChange={(html) => {
              setContent(html)
            }}
          />
        ) : (
          <Textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            onBlur={handleContentBlur}
            placeholder={getPlaceholder()}
            className="min-h-[200px] font-mono text-sm"
          />
        )}

        {contentFormat === "html" && (
          <div className="flex justify-end">
            <button
              type="button"
              onClick={handleContentBlur}
              className="text-sm text-muted-foreground hover:text-foreground"
            >
              {updateNode.isPending ? "Saving..." : "Save content"}
            </button>
          </div>
        )}
      </div>

      {/* Live Preview */}
      <Collapsible open={showPreview} onOpenChange={setShowPreview}>
        <CollapsibleContent>
          <div className="border rounded-lg p-4 bg-muted/30">
            <p className="text-xs text-muted-foreground mb-2 uppercase font-medium">
              Preview
            </p>
            <div className="bg-background rounded p-4">
              <ContentRenderer content={previewContent} safeMode={true} />
            </div>
          </div>
        </CollapsibleContent>
      </Collapsible>

      {/* Node Type Checkboxes */}
      <div className="space-y-3 pt-4 border-t border-border">
        <Label className="text-sm font-medium">Node Type</Label>
        <div className="flex items-center gap-2">
          <Checkbox
            id="is_start_node"
            checked={isStartNode}
            onCheckedChange={handleStartNodeChange}
          />
          <Label htmlFor="is_start_node" className="font-normal">
            Start Node (entry point for the story)
          </Label>
        </div>

        <div className="flex items-center gap-2">
          <Checkbox
            id="is_end_node"
            checked={isEndNode}
            onCheckedChange={handleEndNodeChange}
          />
          <Label htmlFor="is_end_node" className="font-normal">
            End Node (story ending)
          </Label>
        </div>
      </div>
    </div>
  )
}

export default NodeEditorForm
```

### 5.3 Import Requirements

The updated NodeEditorForm requires importing from ContentRenderer:

```typescript
import {
  ContentRenderer,
  type Content,
} from "@/components/Page/primitives/ContentRenderer"
```

Per scratchpad constraint, if this import doesn't resolve, **request human to add the import path**.

---

## 6. Part C: Validation & Polish

### 6.1 Manual Testing Checklist

Execute this checklist to validate Phase 3:

#### 6.1.1 Demo Page Testing

| Test | Format | Expected Result | Status |
|------|--------|-----------------|--------|
| Navigate to demo | - | Demo page loads | [ ] |
| Tab: Text | text | Plain text renders | [ ] |
| Tab: Markdown | markdown | Headings, bold, code blocks | [ ] |
| Tab: Code | code | Syntax highlighting with Shiki | [ ] |
| Tab: Code line numbers | code | Line numbers display (Phase 2 transformer) | [ ] |
| Tab: Code highlight | code | Lines 1,3 highlighted (Phase 2 transformer) | [ ] |
| Tab: Code startLine | code | Line numbers start at 100 (Phase 2 transformer) | [ ] |
| Tab: HTML | html | Sanitized HTML renders | [ ] |
| Tab: JSON | json | Formatted JSON in pre block | [ ] |
| Tab: SVG | svg | SVG renders inline | [ ] |
| Tab: Image | image | Image loads with lazy loading | [ ] |
| Tab: MDX | mdx | MDX compiles and renders | [ ] |
| Variant: inline | all | Compact, no scroll | [ ] |
| Variant: card | all | Bounded height | [ ] |
| Variant: page | all | Full layout | [ ] |
| Variant: tooltip | all | Very small | [ ] |
| Variant: background | all | Absolute positioned | [ ] |
| Safe mode toggle | html/mdx | Sanitization changes | [ ] |

#### 6.1.2 StoryEditor Testing

| Test | Action | Expected Result | Status |
|------|--------|-----------------|--------|
| Open editor | Navigate to story edit | NodeEditorForm loads | [ ] |
| Format selector | Click dropdown | All 8 formats available | [ ] |
| Select: code | Choose code | Placeholder changes | [ ] |
| Preview toggle | Click eye icon | Preview panel shows | [ ] |
| Live preview | Type code | Preview updates | [ ] |
| Format: markdown | Switch to markdown | Code blocks highlight | [ ] |
| Format: mdx | Switch to mdx | MDX compiles | [ ] |
| Save content | Blur textarea | Content saves | [ ] |

#### 6.1.3 Story Playback Testing

| Test | Precondition | Expected Result | Status |
|------|--------------|-----------------|--------|
| Play story | Story has mixed formats | All formats render | [ ] |
| Code node | Node has code content | Syntax highlighted | [ ] |
| Markdown node | Node has markdown | Prose styling applied | [ ] |
| MDX node | Node has mdx | MDX renders | [ ] |
| Transitions | Navigate choices | Content updates smoothly | [ ] |

### 6.2 Success Criteria Validation

| Criterion | Evidence | Validated |
|-----------|----------|-----------|
| Author can add all content types | Format selector has 8 formats | [ ] |
| Viewer plays story smoothly | No errors, transitions work | [ ] |
| Well-designed experience | Consistent styling, clear UI | [ ] |
| UX variants work | All 9 variants render correctly | [ ] |
| Shiki highlighting works | Code blocks colored | [ ] |
| Shiki transformers work (Phase 2) | Line numbers, highlighting, startLine | [ ] |
| MDX compiles (Phase 2) | MDX content displays, components render | [ ] |
| MDX safeMode works (Phase 2) | Custom components filtered when safeMode=true | [ ] |

### 6.3 Document Findings

Create a findings document at completion:

**Location:** `@/components/Page/docs/phase3-findings.md`

Record:
- Any edge cases discovered
- Performance observations
- UI/UX feedback
- Bugs or issues to address in Phase 4

---

## 7. Files Modified Summary

| File | Action | Purpose |
|------|--------|---------|
| `Demo/ContentRendererExamples.ts` | CREATE | Sample content |
| `Demo/ContentRendererDemo.tsx` | CREATE | Demo component |
| `routes/_layout/content-renderer-demo.tsx` | CREATE | Demo route |
| `config/demos.ts` | UPDATE | Add demo config |
| `Story/StoryEditor/NodeEditor/NodeEditorForm.tsx` | UPDATE | Add preview + formats |

---

## 8. Phase 3 Completion Checklist

**Demo Infrastructure (Part A):**
- [ ] ContentRendererDemo component created
- [ ] ContentRendererExamples.ts with sample content
- [ ] Demo route accessible at `/content-renderer-demo`
- [ ] All 8 formats testable in demo
- [ ] All 9 variants testable in demo

**StoryEditor Integration (Part B):**
- [ ] NodeEditorForm extended with code, svg, image, mdx formats
- [ ] Live preview works in editor (ContentRenderer integration)
- [ ] Format-specific placeholders display correctly

**Validation (Part C):**
- [ ] Manual testing checklist complete (Section 6.1)
- [ ] Success criteria validated (Section 6.2)
- [ ] Phase 2 features confirmed working:
  - [ ] Shiki line numbers
  - [ ] Shiki line highlighting
  - [ ] Shiki startLine offset
  - [ ] MDX runtime compilation
  - [ ] MDX safeMode component filtering
- [ ] Findings documented at `phase3-findings.md`

---

## 9. Transition to Phase 4

With Phase 3 complete:

1. **ContentRenderer is proven** in demo and editor contexts
2. **Author workflow validated** with extended format support
3. **Viewer experience confirmed** with live preview
4. **Ready for migration** of existing content rendering code

### 9.1 Phase 4 Scope (from integrated-spec Section 14)

Phase 4 migration work:

1. **Create re-export layer:**
   ```
   @/components/Common/ContentRenderer/
   ├── index.ts              # Re-exports from Page/primitives/
   └── renderContent.ts      # Compatibility helper
   ```

2. **Export compatibility helper:**
   ```typescript
   // renderContent.ts - for gradual migration
   export function renderContent(
     value: string,
     format: ContentFormat,
     options?: ContentMetadata
   ): ReactNode {
     return <ContentRenderer content={{ format, value, metadata: options }} />
   }
   ```

3. **Migrate existing files:**
   - `StoryContent.tsx` - Replace `renderContent()` function (lines 30-78)
   - `StoryPreview.tsx` - Same pattern
   - `StoryPlayer.tsx` - Same pattern
   - `Page/panels/StoryPanel/NodeDisplay.tsx`
   - `Room/panels/StoryPanel/NodeDisplay.tsx`

4. **Update import pattern:**
   ```typescript
   // Old pattern
   import { renderContent } from "./utils"

   // New pattern (preferred)
   import { ContentRenderer } from "@/components/Common/ContentRenderer"

   // Migration pattern (gradual)
   import { renderContent } from "@/components/Common/ContentRenderer"
   ```

### 9.2 Phase 4 Prerequisites

Before starting Phase 4, ensure:

- [ ] All Phase 3 success criteria validated
- [ ] Phase 3 findings documented
- [ ] No critical bugs from testing
- [ ] Team review of Phase 3 implementation

---

*Phase 3 Implementation Guide. Builds on Phase 2 foundation. The proving ground for ContentRenderer.*
