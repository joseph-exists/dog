import {
  Button,
  DialogActionTrigger,
  Input,
  NativeSelectField,
  NativeSelectRoot,
  Text,
  Textarea,
  VStack,
} from "@chakra-ui/react"
import { useState } from "react"
import { Controller, type SubmitHandler, useForm } from "react-hook-form"
import { FaPlus } from "react-icons/fa"

import type { ContentFormat, StoryNodeCreate } from "@/client"
import { Checkbox } from "@/components/ui/checkbox"
import {
  DialogBody,
  DialogCloseTrigger,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogRoot,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Field } from "@/components/ui/field"
import { useCreateNode } from "@/hooks/stories/useStoryNodes"

interface CreateNodeModalProps {
  storyId: string
  storyVersion: number
  onSuccess?: (nodeId: string) => void
  existingStartNode?: boolean
}

const CreateNodeModal = ({
  storyId,
  storyVersion,
  onSuccess,
  existingStartNode = false,
}: CreateNodeModalProps) => {
  const [isOpen, setIsOpen] = useState(false)
  const mutation = useCreateNode(storyId)

  const {
    control,
    register,
    handleSubmit,
    reset,
    watch,
    setValue,
    formState: { errors, isValid, isSubmitting },
  } = useForm<StoryNodeCreate>({
    mode: "onBlur",
    defaultValues: {
      title: "",
      content: "",
      content_format: "html" as ContentFormat,
      node_type: "text",
      is_start_node: false,
      is_end_node: false,
      story_id: storyId,
      story_version: storyVersion,
    },
  })

  const isStartNode = watch("is_start_node")
  const contentFormat = watch("content_format")

  const onSubmit: SubmitHandler<StoryNodeCreate> = (data) => {
    mutation.mutate(data, {
      onSuccess: (result) => {
        reset()
        setIsOpen(false)
        onSuccess?.(result.id)
      },
    })
  }

  return (
    <DialogRoot
      size={{ base: "xs", md: "lg" }}
      placement="center"
      open={isOpen}
      onOpenChange={({ open }) => {
        setIsOpen(open)
        if (!open) reset()
      }}
    >
      <DialogTrigger asChild>
        <Button colorPalette="blue" size="sm">
          <FaPlus fontSize="12px" />
          New Node
        </Button>
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Create New Node</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <Text mb={4} fontSize="sm">
              Add a new scene or moment in your story. This is where your
              adventure unfolds!
            </Text>
            <VStack gap={4}>
              <Field
                required
                invalid={!!errors.title}
                errorText={errors.title?.message}
                label="Node Title"
              >
                <Input
                  {...register("title", {
                    required: "Node title is required",
                    maxLength: {
                      value: 100,
                      message: "Title must be 100 characters or less",
                    },
                  })}
                  placeholder="Forest Entrance"
                  type="text"
                />
              </Field>
              <Field label="Content Format">
                <NativeSelectRoot size="sm">
                  <NativeSelectField
                    value={contentFormat}
                    onChange={(e) =>
                      setValue(
                        "content_format",
                        e.target.value as ContentFormat,
                        { shouldDirty: true },
                      )
                    }
                  >
                    <option value="html">Rich Text (HTML)</option>
                    <option value="text">Plain Text</option>
                    <option value="json">JSON (Advanced)</option>
                  </NativeSelectField>
                </NativeSelectRoot>
              </Field>
              <Field
                invalid={!!errors.content}
                errorText={errors.content?.message}
                label="Content"
              >
                <Textarea
                  {...register("content")}
                  placeholder="You stand before a dark forest. The trees loom overhead, their branches creating a canopy that blocks out most of the sunlight..."
                  rows={6}
                />
              </Field>

              <VStack align="stretch" gap={3} w="full">
                <Controller
                  control={control}
                  name="is_start_node"
                  render={({ field }) => (
                    <Field disabled={field.disabled} colorPalette="teal">
                      <Checkbox
                        checked={field.value}
                        onCheckedChange={({ checked }) =>
                          field.onChange(checked)
                        }
                        disabled={existingStartNode}
                      >
                        <Text fontSize="sm">
                          Start Node
                          {existingStartNode && (
                            <Text
                              as="span"
                              color="orange.600"
                              fontSize="xs"
                              ml={2}
                            >
                              (A start node already exists)
                            </Text>
                          )}
                        </Text>
                      </Checkbox>
                    </Field>
                  )}
                />

                <Controller
                  control={control}
                  name="is_end_node"
                  render={({ field }) => (
                    <Field disabled={field.disabled} colorPalette="teal">
                      <Checkbox
                        checked={field.value}
                        onCheckedChange={({ checked }) =>
                          field.onChange(checked)
                        }
                      >
                        <Text fontSize="sm">End Node</Text>
                      </Checkbox>
                    </Field>
                  )}
                />
              </VStack>

              {isStartNode && existingStartNode && (
                <Text fontSize="xl" color="orange.600">
                  Warning: Creating another start node will cause validation
                  errors. Only one start node is allowed per story version.
                </Text>
              )}
            </VStack>
          </DialogBody>

          <DialogFooter gap={2}>
            <DialogActionTrigger asChild>
              <Button
                variant="subtle"
                colorPalette="gray"
                disabled={isSubmitting}
              >
                Cancel
              </Button>
            </DialogActionTrigger>
            <Button
              variant="solid"
              colorPalette="blue"
              type="submit"
              disabled={!isValid || (isStartNode && existingStartNode)}
              loading={isSubmitting}
            >
              Create Node
            </Button>
          </DialogFooter>
        </form>
        <DialogCloseTrigger />
      </DialogContent>
    </DialogRoot>
  )
}

export default CreateNodeModal
