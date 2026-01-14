/**
 * NodeEditorForm - Form for editing story node properties
 *
 * Features:
 * - Title input with auto-save on blur
 * - Content format selector
 * - Content editor (RichTextEditor for HTML, textarea for others)
 * - Start/End node checkboxes
 */

import { useState, useEffect } from "react"
import type { ContentFormat, StoryNodePublic } from "@/client"
import { useUpdateNode } from "@/hooks/stories/useStoryNodes"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Checkbox } from "@/components/ui/checkbox"
import RichTextEditor from "../../shared/RichTextEditor"

interface NodeEditorFormProps {
  node: StoryNodePublic
  storyId: string
}

const NodeEditorForm = ({ node, storyId }: NodeEditorFormProps) => {
  const updateNode = useUpdateNode(storyId, node.id)

  // Local state for form values
  const [title, setTitle] = useState(node.title)
  const [content, setContent] = useState(node.content || "")
  const [contentFormat, setContentFormat] = useState<ContentFormat>(
    node.content_format || "text"
  )
  const [isStartNode, setIsStartNode] = useState(node.is_start_node || false)
  const [isEndNode, setIsEndNode] = useState(node.is_end_node || false)

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
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="Select format" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="html">HTML (Rich Text)</SelectItem>
            <SelectItem value="text">Plain Text</SelectItem>
            <SelectItem value="markdown">Markdown</SelectItem>
            <SelectItem value="json">JSON</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Content Editor */}
      <div className="space-y-2">
        <Label>Content</Label>
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
            placeholder={
              contentFormat === "json"
                ? '{"key": "value"}'
                : "Enter content..."
            }
            className="min-h-[300px] font-mono"
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
