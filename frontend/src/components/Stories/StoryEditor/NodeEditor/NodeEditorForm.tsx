/**
 * NodeEditorForm - Creative studio for a single story node
 *
 * Features:
 * - Compose tab with format-aware editing and snippet kit
 * - Design tab for preview controls (variant, safety, canvas feel)
 * - Preview tab with live ContentRenderer output
 * - Inspect tab with patch payload preview
 */

import {
  Eye,
  FileCode2,
  Paintbrush,
  Sparkles,
  WandSparkles,
} from "lucide-react"
import { useEffect, useMemo, useState } from "react"
import type { ContentFormat, StoryNodePublic, StoryNodeUpdate } from "@/client"
import {
  type Content,
  type ContentVariant,
  ContentRenderer,
} from "@/components/Page/primitives/ContentRenderer"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
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
import { Switch } from "@/components/ui/switch"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Textarea } from "@/components/ui/textarea"
import { useUpdateNode } from "@/hooks/stories/useStoryNodes"
import RichTextEditor from "../../shared/RichTextEditor"

interface NodeEditorFormProps {
  node: StoryNodePublic
  storyId: string
}

interface CreativeSnippet {
  label: string
  description: string
  value: string
}

const FORMAT_INFO: Record<ContentFormat, { label: string; hint: string }> = {
  text: { label: "Plain Text", hint: "Simple text with whitespace preserved" },
  html: { label: "HTML (Rich Text)", hint: "Rich text with formatting" },
  markdown: {
    label: "Markdown",
    hint: "Markdown syntax with code highlighting",
  },
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

const PREVIEW_VARIANTS: ContentVariant[] = [
  "card",
  "page",
  "modal",
  "preview",
  "embed",
  "inline",
]

const SNIPPETS: Partial<Record<ContentFormat, CreativeSnippet[]>> = {
  text: [
    {
      label: "Beat",
      description: "Story beat with sensory details",
      value:
        "Scene goal: ...\nTension: ...\nSensory anchor: ...\nShift: ...\nReveal: ...",
    },
    {
      label: "NPC Voice",
      description: "Character dialogue seed",
      value:
        '"I can help you, but you are going to hate the cost."\n\n- Tone: controlled urgency\n- Subtext: fear masked as confidence',
    },
  ],
  markdown: [
    {
      label: "Callout",
      description: "Narrative alert block",
      value:
        "> [!NOTE]\n> The air hums before the lights fail.\n> You can feel the room deciding.",
    },
    {
      label: "Choice Lens",
      description: "Pros/cons comparison section",
      value:
        "## Decision Lens\n\n### Option A\n- Gain: ...\n- Risk: ...\n\n### Option B\n- Gain: ...\n- Risk: ...",
    },
  ],
  mdx: [
    {
      label: "Self-contained scene",
      description: "Scoped style and layout wrapper",
      value: `<style>{\`\n.scene-card {\n  border: 1px solid rgba(0,0,0,0.14);\n  border-radius: 18px;\n  padding: 1.25rem;\n  background: linear-gradient(155deg, #fff7ed 0%, #f8fafc 100%);\n}\n.scene-card h3 { margin-top: 0; }\n\`}</style>\n\n<div className="scene-card">\n  <h3>Signal Intercept</h3>\n  <p>We decoded a fragment that might not be human.</p>\n</div>`,
    },
    {
      label: "Kinetic CTA",
      description: "Button + momentum copy",
      value:
        "## Ready for the jump?\n\nPress forward only if you can absorb uncertainty.\n\n<button className=\"px-4 py-2 rounded bg-black text-white\">Commit</button>",
    },
  ],
  html: [
    {
      label: "Hero block",
      description: "Headline and supporting copy",
      value:
        "<section style=\"padding:20px;border-radius:16px;background:linear-gradient(145deg,#fef3c7,#dbeafe)\"><h2 style=\"margin-top:0\">Chapter Node</h2><p>Build momentum, reveal intent, and tee up a choice.</p></section>",
    },
    {
      label: "Two-column",
      description: "Split details and action",
      value:
        "<div style=\"display:grid;grid-template-columns:1fr 1fr;gap:16px\"><aside><h3>Signals</h3><ul><li>Temperature drop</li><li>Clock drift</li></ul></aside><main><h3>Action</h3><p>Stabilize the relay before opening the hatch.</p></main></div>",
    },
  ],
  code: [
    {
      label: "Pseudo logic",
      description: "Decision logic starter",
      value:
        "if (trust > threshold) {\n  route = 'inner-circle'\n} else {\n  route = 'proving-ground'\n}",
    },
  ],
  json: [
    {
      label: "State envelope",
      description: "Structured node metadata",
      value:
        '{\n  "mood": "volatile",\n  "stakes": 7,\n  "tags": ["mystery", "urgent"],\n  "flags": { "seen_intro": true }\n}',
    },
  ],
  svg: [
    {
      label: "Gradient sigil",
      description: "Simple visual motif",
      value:
        '<svg viewBox="0 0 220 120" xmlns="http://www.w3.org/2000/svg">\n  <defs>\n    <linearGradient id="g" x1="0" x2="1">\n      <stop offset="0%" stop-color="#0ea5e9"/>\n      <stop offset="100%" stop-color="#f97316"/>\n    </linearGradient>\n  </defs>\n  <rect x="0" y="0" width="220" height="120" rx="20" fill="url(#g)"/>\n  <text x="110" y="70" text-anchor="middle" font-size="24" fill="white">NODE</text>\n</svg>',
    },
  ],
  image: [
    {
      label: "Image URL",
      description: "Quick URL placeholder",
      value: "https://images.unsplash.com/photo-1518770660439-4636190af475",
    },
  ],
}

function getPlaceholder(contentFormat: ContentFormat): string {
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
      return "# Heading\\n\\nContent here..."
    default:
      return "Enter content..."
  }
}

function toLineCount(value: string): number {
  if (!value) return 0
  return value.split(/\r\n|\r|\n/).length
}

const NodeEditorForm = ({ node, storyId }: NodeEditorFormProps) => {
  const updateNode = useUpdateNode(storyId, node.id)

  const [title, setTitle] = useState(node.title)
  const [content, setContent] = useState(node.content || "")
  const [nodeType, setNodeType] = useState(node.node_type || "")
  const [contentFormat, setContentFormat] = useState<ContentFormat>(
    node.content_format || "text",
  )
  const [isStartNode, setIsStartNode] = useState(node.is_start_node || false)
  const [isEndNode, setIsEndNode] = useState(node.is_end_node || false)

  // Local creative preview controls (do not alter node payload)
  const [previewVariant, setPreviewVariant] = useState<ContentVariant>("card")
  const [previewSafeMode, setPreviewSafeMode] = useState(true)
  const [previewFrame, setPreviewFrame] = useState<"compact" | "standard" | "wide">(
    "standard",
  )
  const [previewSurface, setPreviewSurface] = useState<
    "neutral" | "glass" | "ink"
  >("neutral")

  useEffect(() => {
    setTitle(node.title)
    setContent(node.content || "")
    setNodeType(node.node_type || "")
    setContentFormat(node.content_format || "text")
    setIsStartNode(node.is_start_node || false)
    setIsEndNode(node.is_end_node || false)
  }, [node])

  const handleTitleBlur = () => {
    if (title !== node.title) {
      updateNode.mutate({ title })
    }
  }

  const handleNodeTypeBlur = () => {
    const nextNodeType = nodeType.trim()
    const currentNodeType = node.node_type || ""

    if (nextNodeType !== currentNodeType) {
      updateNode.mutate({ node_type: nextNodeType || null })
    }
  }

  const handleContentSave = () => {
    if (content !== (node.content || "")) {
      updateNode.mutate({ content })
    }
  }

  const handleContentFormatChange = (format: ContentFormat) => {
    setContentFormat(format)
    if (format !== node.content_format) {
      updateNode.mutate({ content_format: format })
    }
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

  const previewContent: Content = useMemo(
    () => ({
      format: contentFormat,
      value: content,
      metadata: { variant: previewVariant },
    }),
    [content, contentFormat, previewVariant],
  )

  const snippets = SNIPPETS[contentFormat] || []

  const applySnippet = (snippet: string) => {
    setContent((prev) => {
      if (!prev.trim()) return snippet
      return `${prev}\n\n${snippet}`
    })
  }

  const frameClass =
    previewFrame === "compact"
      ? "max-w-xl"
      : previewFrame === "wide"
        ? "max-w-none"
        : "max-w-3xl"

  const surfaceClass =
    previewSurface === "glass"
      ? "border-white/40 bg-white/60 backdrop-blur"
      : previewSurface === "ink"
        ? "border-zinc-700 bg-zinc-950 text-zinc-50"
        : "border-border bg-background"

  const contentLines = toLineCount(content)
  const patchPreview: StoryNodeUpdate = {
    title,
    content,
    content_format: contentFormat,
    node_type: nodeType.trim() || null,
    is_start_node: isStartNode,
    is_end_node: isEndNode,
  }

  return (
    <div className="space-y-4">
      <Tabs defaultValue="compose" className="w-full">
        <TabsList className="grid h-auto w-full grid-cols-4">
          <TabsTrigger value="compose">Compose</TabsTrigger>
          <TabsTrigger value="design">Design</TabsTrigger>
          <TabsTrigger value="preview">Preview</TabsTrigger>
          <TabsTrigger value="inspect">Inspect</TabsTrigger>
        </TabsList>

        <TabsContent value="compose" className="space-y-6">
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

          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="content_format">Content Format</Label>
              <Select
                value={contentFormat}
                onValueChange={handleContentFormatChange}
              >
                <SelectTrigger id="content_format" className="w-full">
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

            <div className="space-y-2">
              <Label htmlFor="node_type">Node Archetype</Label>
              <Input
                id="node_type"
                value={nodeType}
                onChange={(e) => setNodeType(e.target.value)}
                onBlur={handleNodeTypeBlur}
                placeholder="scene | puzzle | reveal | encounter"
              />
              <p className="text-xs text-muted-foreground">
                Lightweight semantic tag for creative organization.
              </p>
            </div>
          </div>

          <div className="space-y-3 rounded-lg border bg-muted/20 p-3">
            <div className="flex items-center gap-2 text-sm font-medium">
              <WandSparkles className="h-4 w-4" />
              Creative Kit
            </div>
            {snippets.length === 0 ? (
              <p className="text-xs text-muted-foreground">
                No snippets for this format yet.
              </p>
            ) : (
              <div className="grid gap-2 md:grid-cols-2">
                {snippets.map((snippet) => (
                  <Button
                    key={snippet.label}
                    type="button"
                    variant="outline"
                    className="h-auto items-start justify-start p-3 text-left"
                    onClick={() => applySnippet(snippet.value)}
                  >
                    <div>
                      <p className="text-sm font-medium">{snippet.label}</p>
                      <p className="text-xs text-muted-foreground">
                        {snippet.description}
                      </p>
                    </div>
                  </Button>
                ))}
              </div>
            )}
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label>Content</Label>
              <div className="flex items-center gap-2">
                <Badge variant="outline">{content.length} chars</Badge>
                <Badge variant="outline">{contentLines} lines</Badge>
              </div>
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
                onBlur={handleContentSave}
                placeholder={getPlaceholder(contentFormat)}
                className="min-h-[260px] font-mono text-sm"
              />
            )}

            <div className="flex justify-end">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={handleContentSave}
                disabled={updateNode.isPending}
              >
                {updateNode.isPending ? "Saving..." : "Save Content"}
              </Button>
            </div>
          </div>

          <div className="space-y-3 border-t border-border pt-4">
            <Label className="text-sm font-medium">Node Type Flags</Label>
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
        </TabsContent>

        <TabsContent value="design" className="space-y-6">
          <div className="rounded-lg border bg-muted/20 p-4">
            <div className="mb-3 flex items-center gap-2 text-sm font-medium">
              <Paintbrush className="h-4 w-4" />
              Preview Design Controls
            </div>
            <p className="text-xs text-muted-foreground">
              These controls shape the preview sandbox only, so you can explore
              composition rapidly before committing structure into content.
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label>Variant</Label>
              <Select
                value={previewVariant}
                onValueChange={(value) =>
                  setPreviewVariant(value as ContentVariant)
                }
              >
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {PREVIEW_VARIANTS.map((variant) => (
                    <SelectItem key={variant} value={variant}>
                      {variant}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Frame Width</Label>
              <Select
                value={previewFrame}
                onValueChange={(value) =>
                  setPreviewFrame(value as "compact" | "standard" | "wide")
                }
              >
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="compact">Compact</SelectItem>
                  <SelectItem value="standard">Standard</SelectItem>
                  <SelectItem value="wide">Wide</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label>Surface</Label>
              <Select
                value={previewSurface}
                onValueChange={(value) =>
                  setPreviewSurface(value as "neutral" | "glass" | "ink")
                }
              >
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="neutral">Neutral</SelectItem>
                  <SelectItem value="glass">Glass</SelectItem>
                  <SelectItem value="ink">Ink</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center justify-between rounded-md border bg-background px-3 py-2">
              <div>
                <Label htmlFor="safe_mode">Safe Mode</Label>
                <p className="text-xs text-muted-foreground">
                  Restricts risky MDX component surfaces in preview.
                </p>
              </div>
              <Switch
                id="safe_mode"
                checked={previewSafeMode}
                onCheckedChange={setPreviewSafeMode}
              />
            </div>
          </div>
        </TabsContent>

        <TabsContent value="preview" className="space-y-4">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Eye className="h-4 w-4" />
            Live node preview with current compose + design settings.
          </div>

          <div className={`mx-auto w-full ${frameClass}`}>
            <div className={`rounded-lg border p-4 shadow-sm ${surfaceClass}`}>
              <ContentRenderer
                content={previewContent}
                variant={previewVariant}
                safeMode={previewSafeMode}
              />
            </div>
          </div>
        </TabsContent>

        <TabsContent value="inspect" className="space-y-4">
          <div className="flex items-center gap-2 text-sm font-medium">
            <FileCode2 className="h-4 w-4" />
            Node Patch Preview
          </div>
          <p className="text-xs text-muted-foreground">
            Useful for understanding exactly what shape is being sent to the API.
          </p>

          <Textarea
            readOnly
            value={JSON.stringify(patchPreview, null, 2)}
            className="min-h-[280px] font-mono text-xs"
          />

          <div className="rounded-lg border bg-muted/20 p-3">
            <div className="mb-2 flex items-center gap-2 text-sm font-medium">
              <Sparkles className="h-4 w-4" />
              Runtime snapshot
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs text-muted-foreground md:grid-cols-4">
              <div>format: {contentFormat}</div>
              <div>variant: {previewVariant}</div>
              <div>safeMode: {previewSafeMode ? "on" : "off"}</div>
              <div>lines: {contentLines}</div>
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default NodeEditorForm
