import { useEffect } from "react"
import { useForm, Controller } from "react-hook-form"
import {
  Box,
  Button,
  Heading,
  HStack,
  Separator,
  Textarea,
  VStack,
  NativeSelectRoot,
  NativeSelectField,
} from "@chakra-ui/react"
import { Checkbox } from "@/components/ui/checkbox"
import { Field } from "@/components/ui/field"
import type { StoryNodePublic, StoryNodeUpdate, ContentFormat } from "@/client"
import { useUpdateNode } from "@/hooks/stories/useStoryNodes"
import RichTextEditor from "@/components/Stories/shared/RichTextEditor"

interface NodeEditorFormProps {
  node: StoryNodePublic
  storyId: string
}

interface NodeFormData {
  title: string
  content: string
  content_format: ContentFormat
  is_start_node: boolean
  is_end_node: boolean
}

const NodeEditorForm = ({ node, storyId }: NodeEditorFormProps) => {
  const updateMutation = useUpdateNode(storyId, node.id)

  const {
    register,
    handleSubmit,
    reset,
    watch,
    setValue,
    control,
    formState: { errors, isDirty, isSubmitting },
  } = useForm<NodeFormData>({
    mode: "onBlur",
    defaultValues: {
      title: node.title,
      content: node.content || "",
      content_format: node.content_format || "html",
      is_start_node: node.is_start_node || false,
      is_end_node: node.is_end_node || false,
    },
  })

  const isStartNode = watch("is_start_node")
  const isEndNode = watch("is_end_node")
  const contentFormat = watch("content_format")
  const currentContent = watch("content")

  // Reset form when node changes
  useEffect(() => {
    reset({
      title: node.title,
      content: node.content || "",
      content_format: node.content_format || "html",
      is_start_node: node.is_start_node || false,
      is_end_node: node.is_end_node || false,
    })
  }, [node.id, node.title, node.content, node.content_format, node.is_start_node, node.is_end_node, reset])

  const onSubmit = (data: NodeFormData) => {
    const updateData: StoryNodeUpdate = {
      title: data.title,
      content: data.content,
      content_format: data.content_format,
      is_start_node: data.is_start_node,
      is_end_node: data.is_end_node,
    }

    updateMutation.mutate(updateData, {
      onSuccess: () => {
        reset(data) // Reset dirty state
      },
    })
  }

  const handleFormatChange = (newFormat: ContentFormat) => {
    if (currentContent && currentContent.length > 0) {
      const confirmed = window.confirm(
        "Changing format may affect how your content is displayed. Continue?"
      )
      if (!confirmed) return
    }
    setValue("content_format", newFormat, { shouldDirty: true })
  }


  return (
    <Box as="form" onSubmit={handleSubmit(onSubmit)}>
      <VStack align="stretch" gap={6}>
        {/* Title Field */}
        <Field
          label="Node Title"
          required
          invalid={!!errors.title}
          errorText={errors.title?.message}
        >
          <Textarea
            {...register("title", {
              required: "Title is required",
              maxLength: { value: 200, message: "Title must be 200 characters or less" },
            })}
            placeholder="Enter node title..."
            size="md"
            rows={1}
            resize="none"
            fontSize="lg"
            fontWeight="bold"
          />
        </Field>

        {/* Content Format Selector */}
        <Field label="Content Format" helperText="Choose how content is stored and edited">
          <Controller
            name="content_format"
            control={control}
            render={({ field }) => (
              <NativeSelectRoot size="md">
                <NativeSelectField
                  value={field.value}
                  onChange={(e) => handleFormatChange(e.target.value as ContentFormat)}
                >
                  <option value="html">Rich Text (HTML)</option>
                  <option value="text">Plain Text</option>
                  <option value="json">JSON (Advanced)</option>
                </NativeSelectField>
              </NativeSelectRoot>
            )}
          />
        </Field>

        {/* Node Type Flags */}
        <Box>
          <Heading size="sm" mb={3}>
            Node Properties
          </Heading>
          <VStack align="stretch" gap={2}>
            <Checkbox
              checked={isStartNode}
              onCheckedChange={(e) => setValue("is_start_node", !!e.checked, { shouldDirty: true })}
            >
              Mark as Start Node (story entry point)
            </Checkbox>
            <Checkbox
              checked={isEndNode}
              onCheckedChange={(e) => setValue("is_end_node", !!e.checked, { shouldDirty: true })}
            >
              Mark as End Node (story conclusion)
            </Checkbox>
          </VStack>
        </Box>

        <Separator />

        {/* Content Field */}
        <Field
          label="Node Content"
          required
          invalid={!!errors.content}
          errorText={errors.content?.message}
          helperText={
            contentFormat === "html"
              ? "Use the toolbar to format your story text"
              : contentFormat === "json"
              ? "Enter valid JSON structure for programmatic content"
              : "Plain text content for simple nodes"
          }
        >
          <Controller
            name="content"
            control={control}
            rules={{
              required: "Content is required",
              maxLength: { value: 10000, message: "Content must be 10000 characters or less" },
            }}
            render={({ field }) => {
              if (contentFormat === "html") {
                return (
                  <RichTextEditor
                    content={field.value}
                    onChange={field.onChange}
                  />
                )
              } else if (contentFormat === "json") {
                return (
                  <Textarea
                    value={field.value}
                    onChange={field.onChange}
                    placeholder='{"type": "doc", "content": [...]}'
                    minH="300px"
                    resize="vertical"
                    fontFamily="monospace"
                    fontSize="sm"
                  />
                )
              } else {
                // TEXT format
                return (
                  <Textarea
                    value={field.value}
                    onChange={field.onChange}
                    placeholder="Enter the story content for this node..."
                    minH="300px"
                    resize="vertical"
                  />
                )
              }
            }}
          />
        </Field>
        {/* Save Button */}
        <HStack justify="flex-end">
          <Button
            type="submit"
            colorPalette="blue"
            disabled={!isDirty}
            loading={isSubmitting || updateMutation.isPending}
          >
            Save Changes
          </Button>
        </HStack>
      </VStack>
    </Box>
  )
}

export default NodeEditorForm
