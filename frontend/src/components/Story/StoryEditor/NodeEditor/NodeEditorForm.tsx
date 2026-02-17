/**
 * NodeEditorForm - Form for editing story node properties
 *
 * Features:
 * - Title input with auto-save on blur
 * - Content format selector
 * - Content editor (RichTextEditor for HTML, textarea for others)
 * - Start/End node checkboxes
 */

import { useEffect, useState } from "react"
import{ ContentRenderer, type Content
} from "@/components/Page/primitives/ContentRenderer"
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
import {
  Collapsible,
  CollapsibleContent,
  // CollapsibleTrigger,
} from "@/components/ui/collapsible"
import { Eye } from "lucide-react"
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

  // Local state for form values
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
        <Label htmlFor="content_format">Contents Fermat</Label>
        <Select value={contentFormat} onValueChange={handleContentFormatChange}>
          <SelectTrigger className="w-[200px]">
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
            <Eye/>
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
