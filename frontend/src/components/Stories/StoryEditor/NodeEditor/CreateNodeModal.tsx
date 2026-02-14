/**
 * CreateNodeModal - Dialog for creating a new story node
 *
 * Features:
 * - Title input
 * - Content format selector
 * - Start/End node toggles (start disabled if one exists)
 */

import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import { z } from "zod"
import type { ContentFormat } from "@/client"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useCreateNode } from "@/hooks/stories/useStoryNodes"


// if you need to edit this file, you'll need to edit the dupe over in Story.
// added the enum below after adding to contentformat db - we can call that directly, and it's exposed throug the client types - this is awkward to have here I think.
const createNodeSchema = z.object({
  title: z.string().min(1, "Title is required"),
  // content_format: z.enum(["text", "html", "markdown", "json"]),
  content_format: z.enum(["text", "html", "markdown", "json","yaml","mdx","code","svg","image","audio","video","empty","unknown","test"]),
  is_start_node: z.boolean(),
  is_end_node: z.boolean(),
})
// neat we have this in both the Story tree and the Stories tree, exactly the same.  I wonder if this entire file is the same.

type CreateNodeFormData = z.infer<typeof createNodeSchema>

interface CreateNodeModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  storyId: string
  storyVersion: number
  hasStartNode: boolean
}

const CreateNodeModal = ({
  open,
  onOpenChange,
  storyId,
  storyVersion,
  hasStartNode,
}: CreateNodeModalProps) => {
  const createNode = useCreateNode(storyId)

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<CreateNodeFormData>({
    resolver: zodResolver(createNodeSchema),
    defaultValues: {
      title: "",
      content_format: "html",
      is_start_node: false,
      is_end_node: false,
    },
  })

  const contentFormat = watch("content_format")
  const isStartNode = watch("is_start_node")
  const isEndNode = watch("is_end_node")

  const onSubmit = async (data: CreateNodeFormData) => {
    await createNode.mutateAsync({
      title: data.title,
      content_format: data.content_format as ContentFormat,
      is_start_node: data.is_start_node,
      is_end_node: data.is_end_node,
      story_id: storyId,
      story_version: storyVersion,
    })
    reset()
    onOpenChange(false)
  }

  const handleClose = () => {
    reset()
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Create Node</DialogTitle>
          <DialogDescription>Add a new node to your story</DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* Title */}
          <div className="space-y-2">
            <Label htmlFor="title">Title</Label>
            <Input id="title" placeholder="Node title" {...register("title")} />
            {errors.title && (
              <p className="text-destructive text-sm">{errors.title.message}</p>
            )}
          </div>

          {/* Content Format */}
          <div className="space-y-2">
            <Label htmlFor="content_format">Content Format</Label>
            <Select
              value={contentFormat}
              onValueChange={(val) =>
                setValue("content_format", val as ContentFormat)
              }
            >
              <SelectTrigger>
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

          {/* Node Type Checkboxes */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <Checkbox
                id="is_start_node"
                checked={isStartNode}
                disabled={hasStartNode}
                onCheckedChange={(checked) => {
                  setValue("is_start_node", !!checked)
                  if (checked) setValue("is_end_node", false)
                }}
              />
              <Label
                htmlFor="is_start_node"
                className={hasStartNode ? "text-muted-foreground" : ""}
              >
                Start Node
                {hasStartNode && " (already exists)"}
              </Label>
            </div>

            <div className="flex items-center gap-2">
              <Checkbox
                id="is_end_node"
                checked={isEndNode}
                onCheckedChange={(checked) => {
                  setValue("is_end_node", !!checked)
                  if (checked) setValue("is_start_node", false)
                }}
              />
              <Label htmlFor="is_end_node">End Node</Label>
            </div>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={handleClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Creating..." : "Create Node"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export default CreateNodeModal
