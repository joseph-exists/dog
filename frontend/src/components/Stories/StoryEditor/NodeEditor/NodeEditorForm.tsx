/**
 * NodeEditorForm - Creative studio for a single story node
 *
 * Features:
 * - Compose tab with format-aware editing and snippet kit
 * - Design tab for preview controls (variant, safety, canvas feel)
 * - SVG Studio tab for layered SVG composition
 * - Preview tab with live ContentRenderer output
 * - Inspect tab with patch payload preview
 */

import {
  ArrowDown,
  ArrowUp,
  Eye,
  FileCode2,
  Layers,
  Paintbrush,
  Plus,
  Sparkles,
  Trash2,
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

type LayerBlendMode =
  | "normal"
  | "multiply"
  | "screen"
  | "overlay"
  | "darken"
  | "lighten"

type LayerFilterPreset = "none" | "softBlur" | "glow" | "distort" | "custom"

type FilterPrimitive =
  | "feGaussianBlur"
  | "feColorMatrix"
  | "feTurbulence"
  | "feDisplacementMap"
  | "feDropShadow"
  | "feMorphology"
  | "feConvolveMatrix"
  | "feBlend"
  | "feOffset"

interface LayerFilterStep {
  id: string
  primitive: FilterPrimitive
  attrs: string
  enabled: boolean
}

type SvgApplyMode = "replace" | "prepend" | "append" | "background"

interface SvgLayer {
  id: string
  name: string
  svg: string
  x: number
  y: number
  scale: number
  rotation: number
  opacity: number
  blendMode: LayerBlendMode
  visible: boolean
  filterPreset: LayerFilterPreset
  filterChain: LayerFilterStep[]
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

const SVG_LAYER_TEMPLATES: Array<Pick<SvgLayer, "name" | "svg">> = [
  {
    name: "Aura Field",
    svg: `<svg viewBox="0 0 600 360" xmlns="http://www.w3.org/2000/svg">\n  <defs>\n    <radialGradient id="grad-aura" cx="50%" cy="45%">\n      <stop offset="0%" stop-color="#22d3ee" stop-opacity="0.92"/>\n      <stop offset="70%" stop-color="#2563eb" stop-opacity="0.45"/>\n      <stop offset="100%" stop-color="#0f172a" stop-opacity="0"/>\n    </radialGradient>\n  </defs>\n  <rect width="600" height="360" fill="url(#grad-aura)"/>\n</svg>`,
  },
  {
    name: "Orbit Rings",
    svg: `<svg viewBox="0 0 600 360" xmlns="http://www.w3.org/2000/svg">\n  <g fill="none" stroke="#f8fafc" stroke-opacity="0.65">\n    <circle cx="300" cy="180" r="70" stroke-width="2" />\n    <circle cx="300" cy="180" r="120" stroke-width="1.6" />\n    <circle cx="300" cy="180" r="165" stroke-width="1.2" />\n  </g>\n</svg>`,
  },
  {
    name: "Signal Glyph",
    svg: `<svg viewBox="0 0 600 360" xmlns="http://www.w3.org/2000/svg">\n  <path d="M120 250 C210 80, 390 80, 480 250" stroke="#f97316" stroke-width="8" fill="none" stroke-linecap="round" />\n  <path d="M150 260 C230 120, 370 120, 450 260" stroke="#fdba74" stroke-width="4" fill="none" stroke-linecap="round" />\n</svg>`,
  },
]

const FILTER_PRIMITIVES: FilterPrimitive[] = [
  "feGaussianBlur",
  "feColorMatrix",
  "feTurbulence",
  "feDisplacementMap",
  "feDropShadow",
  "feMorphology",
  "feConvolveMatrix",
  "feBlend",
  "feOffset",
]

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
      return "# Heading\n\nContent here..."
    default:
      return "Enter content..."
  }
}

function toLineCount(value: string): number {
  if (!value) return 0
  return value.split(/\r\n|\r|\n/).length
}

function createId(prefix: string): string {
  return `${prefix}_${Math.random().toString(36).slice(2, 10)}`
}

function createFilterStep(
  primitive: FilterPrimitive = "feGaussianBlur",
  attrs = 'stdDeviation="2.4"',
): LayerFilterStep {
  return {
    id: createId("fstep"),
    primitive,
    attrs,
    enabled: true,
  }
}

function presetFilterChain(preset: LayerFilterPreset): LayerFilterStep[] {
  switch (preset) {
    case "softBlur":
      return [createFilterStep("feGaussianBlur", 'stdDeviation="2.4"')]
    case "glow":
      return [createFilterStep("feDropShadow", 'dx="0" dy="0" stdDeviation="4" flood-color="#a78bfa" flood-opacity="0.8"')]
    case "distort":
      return [
        createFilterStep(
          "feTurbulence",
          'type="fractalNoise" baseFrequency="0.02" numOctaves="2" seed="12" result="noise"',
        ),
        createFilterStep("feDisplacementMap", 'in2="noise" scale="24"'),
      ]
    case "custom":
    case "none":
    default:
      return []
  }
}

function createSvgLayer(templateIndex = 0): SvgLayer {
  const template = SVG_LAYER_TEMPLATES[templateIndex] ?? SVG_LAYER_TEMPLATES[0]
  return {
    id: createId("layer"),
    name: template.name,
    svg: template.svg,
    x: 0,
    y: 0,
    scale: 1,
    rotation: 0,
    opacity: 1,
    blendMode: "normal",
    visible: true,
    filterPreset: "none",
    filterChain: [],
  }
}

function stripOuterSvg(rawSvg: string): string {
  const trimmed = rawSvg.trim()
  const matched = trimmed.match(/^<svg[\s\S]*?>([\s\S]*?)<\/svg>\s*$/i)
  if (matched?.[1]) return matched[1]
  return trimmed
}

function filterDefForLayer(layer: SvgLayer): string {
  const filterId = `layer-filter-${layer.id}`
  const chain =
    layer.filterChain.length > 0
      ? layer.filterChain
      : presetFilterChain(layer.filterPreset)
  const enabledSteps = chain.filter((step) => step.enabled)

  if (enabledSteps.length === 0) {
    return ""
  }

  let previousResult = "SourceGraphic"
  const primitiveNodes = enabledSteps
    .map((step, index) => {
      const attrs = step.attrs.trim()
      const hasInAttr = /\bin=/.test(attrs)
      const hasResultAttr = /\bresult=/.test(attrs)
      const explicitResult = attrs.match(/\bresult=["']([^"']+)["']/)?.[1]
      const fallbackResult = `s${index}`
      const resultName = explicitResult || fallbackResult

      const canUseInAttr = step.primitive !== "feTurbulence"
      const inPrefix = canUseInAttr && !hasInAttr ? `in="${previousResult}" ` : ""
      const resultSuffix = hasResultAttr ? "" : ` result="${resultName}"`

      if (step.primitive !== "feBlend") {
        previousResult = resultName
      } else {
        previousResult = explicitResult || fallbackResult
      }

      return `<${step.primitive} ${inPrefix}${attrs}${resultSuffix} />`
    })
    .join("")

  return `<filter id="${filterId}" x="-30%" y="-30%" width="160%" height="160%">${primitiveNodes}</filter>`
}

function buildCompositeSvg(layers: SvgLayer[], canvasWidth: number, canvasHeight: number): string {
  const visibleLayers = layers.filter((layer) => layer.visible)
  const layersWithFilters = visibleLayers.map((layer) => ({
    layer,
    filterDef: filterDefForLayer(layer),
  }))

  const defs = layersWithFilters
    .map(({ filterDef }) => filterDef)
    .filter(Boolean)
    .join("\n")

  const groups = layersWithFilters
    .map(({ layer, filterDef }) => {
      const filterId = `layer-filter-${layer.id}`
      const filterAttr = filterDef ? ` filter=\"url(#${filterId})\"` : ""
      const transform = `translate(${layer.x} ${layer.y}) rotate(${layer.rotation}) scale(${layer.scale})`

      return `<g transform="${transform}" opacity="${layer.opacity}" style="mix-blend-mode:${layer.blendMode}"${filterAttr}>${stripOuterSvg(layer.svg)}</g>`
    })
    .join("\n")

  return `<svg viewBox="0 0 ${canvasWidth} ${canvasHeight}" xmlns="http://www.w3.org/2000/svg">${defs ? `<defs>${defs}</defs>` : ""}${groups}</svg>`
}

function escapeForTemplateLiteral(value: string): string {
  return value
    .replace(/\\/g, "\\\\")
    .replace(/`/g, "\\`")
    .replace(/\$\{/g, "\\${")
}

function buildLayeredMdx(compositeSvg: string, canvasWidth: number, canvasHeight: number): string {
  const style = `<style>{\`\n.svg-layer-scene {\n  position: relative;\n  width: 100%;\n  max-width: ${canvasWidth}px;\n  min-height: ${canvasHeight}px;\n  overflow: hidden;\n  border-radius: 16px;\n}\n.svg-layer-scene .svg-layer {\n  position: absolute;\n  inset: 0;\n  transform-origin: center;\n}\n.svg-layer-scene .svg-layer > svg {\n  width: 100%;\n  height: 100%;\n}\n\`}</style>`
  const html = `<div class="svg-layer-scene">${compositeSvg}</div>`
  return `${style}\n\n<div dangerouslySetInnerHTML={{ __html: \`${escapeForTemplateLiteral(html)}\` }} />`
}

function encodeSvgDataUrl(svg: string): string {
  return encodeURIComponent(svg)
}

function buildBackgroundContainerMdx(
  compositeSvg: string,
  bodyMdx: string,
  minHeightPx: number,
): string {
  const encoded = encodeSvgDataUrl(compositeSvg)
  return `<div style={{
  backgroundImage: "url('data:image/svg+xml;utf8,${encoded}')",
  backgroundSize: "cover",
  backgroundPosition: "center",
  minHeight: "${minHeightPx}px",
  borderRadius: "16px",
  padding: "1.25rem"
}}>
${bodyMdx || "Your Content"}
</div>`
}

function escapeCodeFence(value: string): string {
  return value.replace(/```/g, "``\\`")
}

function convertNodeBodyToMdx(source: string, format: ContentFormat): string {
  if (!source.trim()) return ""

  switch (format) {
    case "mdx":
      return source
    case "markdown":
    case "text":
      return source
    case "html":
      return `<div dangerouslySetInnerHTML={{ __html: \`${escapeForTemplateLiteral(source)}\` }} />`
    case "image":
      return `![Node Image](${source.trim()})`
    default:
      return `### Existing ${format} body\n\n\`\`\`${format}\n${escapeCodeFence(source)}\n\`\`\``
  }
}

interface SvgApplyPlan {
  nextContent: string
  nextFormat: ContentFormat
  overwritesBody: boolean
  convertedToMdx: boolean
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

  const [previewVariant, setPreviewVariant] = useState<ContentVariant>("card")
  const [previewSafeMode, setPreviewSafeMode] = useState(true)
  const [previewFrame, setPreviewFrame] = useState<"compact" | "standard" | "wide">(
    "standard",
  )
  const [previewSurface, setPreviewSurface] = useState<
    "neutral" | "glass" | "ink"
  >("neutral")
  const [activeTab, setActiveTab] = useState("compose")
  const [lastSavedAt, setLastSavedAt] = useState<string | null>(null)

  const [svgCanvasWidth, setSvgCanvasWidth] = useState(960)
  const [svgCanvasHeight, setSvgCanvasHeight] = useState(560)
  const [svgLayers, setSvgLayers] = useState<SvgLayer[]>([
    createSvgLayer(0),
    createSvgLayer(1),
  ])
  const [activeLayerId, setActiveLayerId] = useState<string>(svgLayers[0]?.id ?? "")
  const [svgApplyMode, setSvgApplyMode] = useState<SvgApplyMode>("replace")
  const [svgApplyTargetPreview, setSvgApplyTargetPreview] = useState<
    "svg" | "mdx"
  >("mdx")
  const [svgBackgroundMinHeight, setSvgBackgroundMinHeight] = useState(320)

  useEffect(() => {
    setTitle(node.title)
    setContent(node.content || "")
    setNodeType(node.node_type || "")
    setContentFormat(node.content_format || "text")
    setIsStartNode(node.is_start_node || false)
    setIsEndNode(node.is_end_node || false)
    setLastSavedAt(null)
  }, [node])

  const activeLayer =
    svgLayers.find((layer) => layer.id === activeLayerId) ?? svgLayers[0] ?? null

  useEffect(() => {
    if (!activeLayer && svgLayers.length > 0) {
      setActiveLayerId(svgLayers[0].id)
    }
  }, [activeLayer, svgLayers])

  const mutateNode = (patch: StoryNodeUpdate) => {
    if (Object.keys(patch).length === 0) return
    updateNode.mutate(patch, {
      onSuccess: () => {
        setLastSavedAt(new Date().toISOString())
      },
    })
  }

  const dirtyPatch = useMemo<StoryNodeUpdate>(() => {
    const patch: StoryNodeUpdate = {}
    const nextNodeType = nodeType.trim()
    const currentNodeType = node.node_type || ""

    if (title !== node.title) patch.title = title
    if (content !== (node.content || "")) patch.content = content
    if (contentFormat !== (node.content_format || "text")) {
      patch.content_format = contentFormat
    }
    if (nextNodeType !== currentNodeType) {
      patch.node_type = nextNodeType || null
    }
    if (isStartNode !== (node.is_start_node || false)) {
      patch.is_start_node = isStartNode
    }
    if (isEndNode !== (node.is_end_node || false)) {
      patch.is_end_node = isEndNode
    }

    return patch
  }, [
    content,
    contentFormat,
    isEndNode,
    isStartNode,
    node,
    nodeType,
    title,
  ])

  const hasUnsavedChanges = Object.keys(dirtyPatch).length > 0

  const handleTitleBlur = () => {
    if (title !== node.title) {
      mutateNode({ title })
    }
  }

  const handleNodeTypeBlur = () => {
    const nextNodeType = nodeType.trim()
    const currentNodeType = node.node_type || ""

    if (nextNodeType !== currentNodeType) {
      mutateNode({ node_type: nextNodeType || null })
    }
  }

  const handleContentSave = () => {
    if (content !== (node.content || "")) {
      mutateNode({ content })
    }
  }

  const handleContentFormatChange = (format: ContentFormat) => {
    setContentFormat(format)
    if (format !== node.content_format) {
      mutateNode({ content_format: format })
    }
  }

  const handleStartNodeChange = (checked: boolean) => {
    setIsStartNode(checked)
    if (checked) setIsEndNode(false)
    mutateNode({
      is_start_node: checked,
      is_end_node: checked ? false : isEndNode,
    })
  }

  const handleEndNodeChange = (checked: boolean) => {
    setIsEndNode(checked)
    if (checked) setIsStartNode(false)
    mutateNode({
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

  const compositeSvg = useMemo(
    () => buildCompositeSvg(svgLayers, svgCanvasWidth, svgCanvasHeight),
    [svgCanvasHeight, svgCanvasWidth, svgLayers],
  )

  const svgStudioPreviewContent: Content = useMemo(
    () => ({
      format: "svg",
      value: compositeSvg,
      metadata: {
        variant: "card",
        options: { inline: true },
      },
    }),
    [compositeSvg],
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

  const upsertActiveLayer = (patch: Partial<SvgLayer>) => {
    if (!activeLayer) return

    setSvgLayers((prev) =>
      prev.map((layer) => (layer.id === activeLayer.id ? { ...layer, ...patch } : layer)),
    )
  }

  const updateActiveLayerFilterChain = (
    mutate: (prev: LayerFilterStep[]) => LayerFilterStep[],
  ) => {
    if (!activeLayer) return

    setSvgLayers((prev) =>
      prev.map((layer) => {
        if (layer.id !== activeLayer.id) return layer
        return {
          ...layer,
          filterPreset: "custom",
          filterChain: mutate(layer.filterChain),
        }
      }),
    )
  }

  const addLayer = (templateIndex = 0) => {
    const layer = createSvgLayer(templateIndex)
    setSvgLayers((prev) => [...prev, layer])
    setActiveLayerId(layer.id)
  }

  const removeLayer = (layerId: string) => {
    setSvgLayers((prev) => {
      const next = prev.filter((layer) => layer.id !== layerId)
      if (activeLayerId === layerId) {
        setActiveLayerId(next[0]?.id ?? "")
      }
      return next
    })
  }

  const moveLayer = (layerId: string, direction: "up" | "down") => {
    setSvgLayers((prev) => {
      const index = prev.findIndex((layer) => layer.id === layerId)
      if (index < 0) return prev

      const nextIndex = direction === "up" ? index - 1 : index + 1
      if (nextIndex < 0 || nextIndex >= prev.length) return prev

      const next = [...prev]
      const [layer] = next.splice(index, 1)
      next.splice(nextIndex, 0, layer)
      return next
    })
  }

  const moveFilterStep = (stepId: string, direction: "up" | "down") => {
    updateActiveLayerFilterChain((prev) => {
      const index = prev.findIndex((step) => step.id === stepId)
      if (index < 0) return prev

      const nextIndex = direction === "up" ? index - 1 : index + 1
      if (nextIndex < 0 || nextIndex >= prev.length) return prev

      const next = [...prev]
      const [step] = next.splice(index, 1)
      next.splice(nextIndex, 0, step)
      return next
    })
  }

  const applyFilterPresetToActiveLayer = (preset: LayerFilterPreset) => {
    if (!activeLayer) return
    const nextChain = presetFilterChain(preset)
    upsertActiveLayer({ filterPreset: preset, filterChain: nextChain })
  }

  const buildSvgApplyPlan = (
    targetFormat: "svg" | "mdx",
    mode: SvgApplyMode,
  ): SvgApplyPlan => {
    if (targetFormat === "svg") {
      return {
        nextContent: compositeSvg,
        nextFormat: "svg",
        overwritesBody: true,
        convertedToMdx: false,
      }
    }

    const sceneMdx = buildLayeredMdx(compositeSvg, svgCanvasWidth, svgCanvasHeight)
    const normalizedMode = mode
    const shouldMerge = normalizedMode !== "replace"

    if (normalizedMode === "background") {
      const existingBody = convertNodeBodyToMdx(content, contentFormat)
      const backgroundMdx = buildBackgroundContainerMdx(
        compositeSvg,
        existingBody,
        svgBackgroundMinHeight,
      )
      return {
        nextContent: backgroundMdx,
        nextFormat: "mdx",
        overwritesBody: false,
        convertedToMdx: contentFormat !== "mdx",
      }
    }

    if (!shouldMerge) {
      return {
        nextContent: sceneMdx,
        nextFormat: "mdx",
        overwritesBody: true,
        convertedToMdx: contentFormat !== "mdx",
      }
    }

    const existingBody = convertNodeBodyToMdx(content, contentFormat)
    const merged =
      normalizedMode === "prepend"
        ? `${sceneMdx}\n\n${existingBody}`.trim()
        : `${existingBody}\n\n${sceneMdx}`.trim()

    return {
      nextContent: merged,
      nextFormat: "mdx",
      overwritesBody: false,
      convertedToMdx: contentFormat !== "mdx",
    }
  }

  const svgApplyPreview = useMemo(
    () => buildSvgApplyPlan(svgApplyTargetPreview, svgApplyMode),
    [
      svgApplyMode,
      svgApplyTargetPreview,
      compositeSvg,
      svgCanvasHeight,
      svgCanvasWidth,
      content,
      contentFormat,
      svgBackgroundMinHeight,
    ],
  )

  const applySvgLayersToContent = (targetFormat: "svg" | "mdx") => {
    const plan = buildSvgApplyPlan(targetFormat, svgApplyMode)
    const hasExistingBody = Boolean(content.trim())

    if (
      plan.overwritesBody &&
      hasExistingBody &&
      targetFormat !== "svg" &&
      svgApplyMode === "replace"
    ) {
      const confirmed = window.confirm(
        "Replace current node body with SVG composition? This will overwrite existing content text.",
      )
      if (!confirmed) return
    }

    if (targetFormat === "svg" && svgApplyMode !== "replace" && hasExistingBody) {
      const confirmed = window.confirm(
        "SVG format supports replace-only apply. Continue and replace existing body?",
      )
      if (!confirmed) return
    }

    setContent(plan.nextContent)
    const patch: StoryNodeUpdate = { content: plan.nextContent }
    if (contentFormat !== plan.nextFormat || node.content_format !== plan.nextFormat) {
      setContentFormat(plan.nextFormat)
      patch.content_format = plan.nextFormat
    }
    mutateNode(patch)
  }

  const reloadLocalFromNode = () => {
    setTitle(node.title)
    setContent(node.content || "")
    setNodeType(node.node_type || "")
    setContentFormat(node.content_format || "text")
    setIsStartNode(node.is_start_node || false)
    setIsEndNode(node.is_end_node || false)
  }

  const saveAllChanges = () => {
    mutateNode(dirtyPatch)
  }

  const handleTabChange = (nextTab: string) => {
    if (nextTab !== activeTab && hasUnsavedChanges) {
      saveAllChanges()
    }
    setActiveTab(nextTab)
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2 rounded-md border bg-muted/20 px-3 py-2">
        <div className="text-xs text-muted-foreground">
          {hasUnsavedChanges ? "Unsaved changes" : "Synced"}
          {lastSavedAt && !hasUnsavedChanges
            ? ` | last save ${new Date(lastSavedAt).toLocaleTimeString()}`
            : ""}
        </div>
        <div className="flex items-center gap-2">
          <Button
            type="button"
            size="sm"
            variant="outline"
            onClick={reloadLocalFromNode}
            disabled={!hasUnsavedChanges || updateNode.isPending}
          >
            Reload
          </Button>
          <Button
            type="button"
            size="sm"
            onClick={saveAllChanges}
            disabled={!hasUnsavedChanges || updateNode.isPending}
          >
            {updateNode.isPending ? "Saving..." : "Save Node"}
          </Button>
        </div>
      </div>

      <Tabs
        value={activeTab}
        onValueChange={handleTabChange}
        className="w-full"
      >
        <TabsList className="grid h-auto w-full grid-cols-5">
          <TabsTrigger value="compose">Compose</TabsTrigger>
          <TabsTrigger value="design">Design</TabsTrigger>
          <TabsTrigger value="svg-studio">SVG Studio</TabsTrigger>
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

        <TabsContent value="svg-studio" className="space-y-5">
          <div className="rounded-lg border bg-muted/20 p-4">
            <div className="mb-2 flex items-center gap-2 text-sm font-medium">
              <Layers className="h-4 w-4" />
              Layered SVG Composer
            </div>
            <p className="text-xs text-muted-foreground">
              Build multi-layer SVG scenes with transform, blend, and filter chains,
              then export directly into node content as `svg` or `mdx`.
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            <div className="space-y-2">
              <Label>Canvas Width</Label>
              <Input
                type="number"
                value={svgCanvasWidth}
                min={200}
                onChange={(e) => setSvgCanvasWidth(Number(e.target.value) || 960)}
              />
            </div>
            <div className="space-y-2">
              <Label>Canvas Height</Label>
              <Input
                type="number"
                value={svgCanvasHeight}
                min={120}
                onChange={(e) => setSvgCanvasHeight(Number(e.target.value) || 560)}
              />
            </div>
            <div className="space-y-2">
              <Label>Layer Template</Label>
              <Select
                value="0"
                onValueChange={(value) => addLayer(Number(value))}
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Add layer from template" />
                </SelectTrigger>
                <SelectContent>
                  {SVG_LAYER_TEMPLATES.map((template, index) => (
                    <SelectItem key={template.name} value={String(index)}>
                      + {template.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="grid gap-4 lg:grid-cols-5">
            <div className="space-y-2 lg:col-span-2">
              <div className="flex items-center justify-between">
                <Label>Layer Stack</Label>
                <Button type="button" size="sm" variant="outline" onClick={() => addLayer()}>
                  <Plus className="mr-1 h-4 w-4" />
                  Add
                </Button>
              </div>

              <div className="max-h-[320px] space-y-2 overflow-auto rounded-md border p-2">
                {svgLayers.map((layer, index) => (
                  <button
                    type="button"
                    key={layer.id}
                    onClick={() => setActiveLayerId(layer.id)}
                    className={`w-full rounded-md border p-2 text-left ${
                      activeLayer?.id === layer.id
                        ? "border-primary bg-primary/5"
                        : "border-border"
                    }`}
                  >
                    <div className="mb-2 flex items-center justify-between gap-2">
                      <p className="truncate text-sm font-medium">{layer.name}</p>
                      <Badge variant="outline">{index + 1}</Badge>
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {!layer.visible && <Badge variant="secondary">hidden</Badge>}
                      {layer.filterPreset !== "none" && (
                        <Badge variant="secondary">{layer.filterPreset}</Badge>
                      )}
                      {layer.blendMode !== "normal" && (
                        <Badge variant="secondary">{layer.blendMode}</Badge>
                      )}
                    </div>
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-3 lg:col-span-3">
              {!activeLayer ? (
                <div className="rounded-md border border-dashed p-4 text-sm text-muted-foreground">
                  Create a layer to begin.
                </div>
              ) : (
                <>
                  <div className="grid gap-3 md:grid-cols-2">
                    <div className="space-y-2">
                      <Label>Layer Name</Label>
                      <Input
                        value={activeLayer.name}
                        onChange={(e) => upsertActiveLayer({ name: e.target.value })}
                      />
                    </div>
                    <div className="flex items-end gap-2">
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => moveLayer(activeLayer.id, "up")}
                      >
                        <ArrowUp className="mr-1 h-4 w-4" />
                        Up
                      </Button>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => moveLayer(activeLayer.id, "down")}
                      >
                        <ArrowDown className="mr-1 h-4 w-4" />
                        Down
                      </Button>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => upsertActiveLayer({ visible: !activeLayer.visible })}
                      >
                        {activeLayer.visible ? "Hide" : "Show"}
                      </Button>
                      <Button
                        type="button"
                        variant="destructive"
                        size="sm"
                        onClick={() => removeLayer(activeLayer.id)}
                        disabled={svgLayers.length <= 1}
                      >
                        <Trash2 className="mr-1 h-4 w-4" />
                        Remove
                      </Button>
                    </div>
                  </div>

                  <div className="grid gap-3 md:grid-cols-3">
                    <div className="space-y-2">
                      <Label>X Offset</Label>
                      <Input
                        type="number"
                        value={activeLayer.x}
                        onChange={(e) =>
                          upsertActiveLayer({ x: Number(e.target.value) || 0 })
                        }
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Y Offset</Label>
                      <Input
                        type="number"
                        value={activeLayer.y}
                        onChange={(e) =>
                          upsertActiveLayer({ y: Number(e.target.value) || 0 })
                        }
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Scale</Label>
                      <Input
                        type="number"
                        step="0.05"
                        value={activeLayer.scale}
                        onChange={(e) =>
                          upsertActiveLayer({
                            scale: Number(e.target.value) || 1,
                          })
                        }
                      />
                    </div>
                  </div>

                  <div className="grid gap-3 md:grid-cols-3">
                    <div className="space-y-2">
                      <Label>Rotation (deg)</Label>
                      <Input
                        type="number"
                        value={activeLayer.rotation}
                        onChange={(e) =>
                          upsertActiveLayer({
                            rotation: Number(e.target.value) || 0,
                          })
                        }
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Opacity</Label>
                      <Input
                        type="number"
                        min={0}
                        max={1}
                        step="0.05"
                        value={activeLayer.opacity}
                        onChange={(e) =>
                          upsertActiveLayer({
                            opacity: Math.min(
                              1,
                              Math.max(0, Number(e.target.value) || 0),
                            ),
                          })
                        }
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Blend</Label>
                      <Select
                        value={activeLayer.blendMode}
                        onValueChange={(value) =>
                          upsertActiveLayer({ blendMode: value as LayerBlendMode })
                        }
                      >
                        <SelectTrigger className="w-full">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="normal">normal</SelectItem>
                          <SelectItem value="multiply">multiply</SelectItem>
                          <SelectItem value="screen">screen</SelectItem>
                          <SelectItem value="overlay">overlay</SelectItem>
                          <SelectItem value="darken">darken</SelectItem>
                          <SelectItem value="lighten">lighten</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label>Filter Preset</Label>
                    <Select
                      value={activeLayer.filterPreset}
                      onValueChange={(value) =>
                        applyFilterPresetToActiveLayer(value as LayerFilterPreset)
                      }
                    >
                      <SelectTrigger className="w-full">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">none</SelectItem>
                        <SelectItem value="softBlur">softBlur</SelectItem>
                        <SelectItem value="glow">glow</SelectItem>
                        <SelectItem value="distort">distort</SelectItem>
                        <SelectItem value="custom">custom</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2 rounded-md border p-3">
                    <div className="flex items-center justify-between">
                      <Label>Filter Chain</Label>
                      <Button
                        type="button"
                        size="sm"
                        variant="outline"
                        onClick={() =>
                          updateActiveLayerFilterChain((prev) => [
                            ...prev,
                            createFilterStep(),
                          ])
                        }
                      >
                        <Plus className="mr-1 h-4 w-4" />
                        Add Step
                      </Button>
                    </div>

                    {(activeLayer.filterChain.length === 0 ||
                      activeLayer.filterPreset !== "custom") && (
                      <p className="text-xs text-muted-foreground">
                        Preset-driven chain. Switch to `custom` or add a step to
                        fully edit primitive order and attributes.
                      </p>
                    )}

                    {activeLayer.filterChain.length > 0 && (
                      <div className="space-y-2">
                        {activeLayer.filterChain.map((step, index) => (
                          <div
                            key={step.id}
                            className="space-y-2 rounded-md border bg-muted/20 p-2"
                          >
                            <div className="flex flex-wrap items-center gap-2">
                              <Badge variant="outline">#{index + 1}</Badge>
                              <Switch
                                checked={step.enabled}
                                onCheckedChange={(checked) =>
                                  updateActiveLayerFilterChain((prev) =>
                                    prev.map((candidate) =>
                                      candidate.id === step.id
                                        ? { ...candidate, enabled: checked }
                                        : candidate,
                                    ),
                                  )
                                }
                              />
                              <Select
                                value={step.primitive}
                                onValueChange={(value) =>
                                  updateActiveLayerFilterChain((prev) =>
                                    prev.map((candidate) =>
                                      candidate.id === step.id
                                        ? {
                                            ...candidate,
                                            primitive: value as FilterPrimitive,
                                          }
                                        : candidate,
                                    ),
                                  )
                                }
                              >
                                <SelectTrigger className="h-8 w-[200px]">
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  {FILTER_PRIMITIVES.map((primitive) => (
                                    <SelectItem
                                      key={primitive}
                                      value={primitive}
                                    >
                                      {primitive}
                                    </SelectItem>
                                  ))}
                                </SelectContent>
                              </Select>
                              <Button
                                type="button"
                                size="sm"
                                variant="ghost"
                                onClick={() => moveFilterStep(step.id, "up")}
                              >
                                <ArrowUp className="h-4 w-4" />
                              </Button>
                              <Button
                                type="button"
                                size="sm"
                                variant="ghost"
                                onClick={() => moveFilterStep(step.id, "down")}
                              >
                                <ArrowDown className="h-4 w-4" />
                              </Button>
                              <Button
                                type="button"
                                size="sm"
                                variant="ghost"
                                className="text-destructive"
                                onClick={() =>
                                  updateActiveLayerFilterChain((prev) =>
                                    prev.filter(
                                      (candidate) => candidate.id !== step.id,
                                    ),
                                  )
                                }
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </div>
                            <Input
                              value={step.attrs}
                              onChange={(e) =>
                                updateActiveLayerFilterChain((prev) =>
                                  prev.map((candidate) =>
                                    candidate.id === step.id
                                      ? {
                                          ...candidate,
                                          attrs: e.target.value,
                                        }
                                      : candidate,
                                  ),
                                )
                              }
                              placeholder='stdDeviation="2.4" | in2="noise" scale="24"'
                              className="font-mono text-xs"
                            />
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label>Raw SVG Markup</Label>
                    <Textarea
                      value={activeLayer.svg}
                      onChange={(e) => upsertActiveLayer({ svg: e.target.value })}
                      className="min-h-[220px] font-mono text-xs"
                    />
                  </div>
                </>
              )}
            </div>
          </div>

          <div className="space-y-3 rounded-lg border p-4">
            <div className="grid gap-3 md:grid-cols-3">
              <div className="space-y-2">
                <Label>Apply Mode</Label>
                <Select
                  value={svgApplyMode}
                  onValueChange={(value) => setSvgApplyMode(value as SvgApplyMode)}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="replace">replace body</SelectItem>
                    <SelectItem value="prepend">prepend to body</SelectItem>
                    <SelectItem value="append">append to body</SelectItem>
                    <SelectItem value="background">background wrapper</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Preview Target</Label>
                <Select
                  value={svgApplyTargetPreview}
                  onValueChange={(value) =>
                    setSvgApplyTargetPreview(value as "svg" | "mdx")
                  }
                >
                  <SelectTrigger className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="mdx">mdx</SelectItem>
                    <SelectItem value="svg">svg</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="rounded-md border bg-muted/20 p-3 text-xs text-muted-foreground">
                <p>
                  {svgApplyPreview.overwritesBody
                    ? "This apply plan overwrites node body."
                    : "This apply plan preserves existing node body."}
                </p>
                <p>
                  Output format:{" "}
                  <span className="font-medium">{svgApplyPreview.nextFormat}</span>
                </p>
                {svgApplyPreview.convertedToMdx && (
                  <p>Existing body will be converted to MDX-compatible form.</p>
                )}
              </div>
            </div>

            {svgApplyMode === "background" && (
              <div className="grid gap-3 md:grid-cols-3">
                <div className="space-y-2">
                  <Label>Background Min Height (px)</Label>
                  <Input
                    type="number"
                    min={120}
                    value={svgBackgroundMinHeight}
                    onChange={(e) =>
                      setSvgBackgroundMinHeight(Number(e.target.value) || 320)
                    }
                  />
                </div>
              </div>
            )}

            <div className="grid gap-3 md:grid-cols-2">
              <div className="space-y-2">
                <Label>Before (current body)</Label>
                <Textarea
                  readOnly
                  value={content}
                  className="min-h-[160px] font-mono text-xs"
                />
              </div>
              <div className="space-y-2">
                <Label>After (apply result)</Label>
                <Textarea
                  readOnly
                  value={svgApplyPreview.nextContent}
                  className="min-h-[160px] font-mono text-xs"
                />
              </div>
            </div>

            <div className="flex items-center justify-between">
              <Label>Composite Preview</Label>
              <div className="flex flex-wrap gap-2">
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  onClick={() => applySvgLayersToContent("svg")}
                  disabled={svgApplyMode !== "replace"}
                >
                  Apply to Content (SVG)
                </Button>
                <Button
                  type="button"
                  size="sm"
                  onClick={() => applySvgLayersToContent("mdx")}
                >
                  Apply to Content (MDX)
                </Button>
              </div>
            </div>

            <div className="rounded-md border bg-background p-3">
              <ContentRenderer
                content={svgStudioPreviewContent}
                safeMode={false}
                variant="card"
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
