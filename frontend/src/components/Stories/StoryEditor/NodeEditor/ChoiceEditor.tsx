import { useState, useEffect } from "react"
import { type SubmitHandler, useForm, Controller } from "react-hook-form"
import {
  Box,
  Button,
  DialogActionTrigger,
  Input,
  NativeSelectRoot,
  NativeSelectField,
  Separator,
  Text,
  VStack,
} from "@chakra-ui/react"

import type { NodeChoicePublic, StoryNodePublic } from "@/client"
import { useCreateChoice, useUpdateChoice } from "@/hooks/stories/useNodeChoices"
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
import StateConditionEditor from "../../shared/StateConditionEditor"

interface ChoiceEditorProps {
  fromNodeId: string
  availableNodes: StoryNodePublic[]
  choice?: NodeChoicePublic // If provided, edit mode; otherwise create mode
  trigger?: React.ReactNode
  onSuccess?: () => void
}

interface ChoiceFormData {
  text: string
  to_node_id: string
  order?: number
  requires_state: Record<string, unknown> | null
  sets_state: Record<string, unknown> | null
}

const ChoiceEditor = ({
  fromNodeId,
  availableNodes,
  choice,
  trigger,
  onSuccess,
}: ChoiceEditorProps) => {
  const [isOpen, setIsOpen] = useState(false)
  const isEditMode = !!choice

  const createMutation = useCreateChoice()
  const updateMutation = useUpdateChoice(fromNodeId)

  const {
    control,
    register,
    handleSubmit,
    reset,
    formState: { errors, isValid, isSubmitting },
  } = useForm<ChoiceFormData>({
    mode: "onBlur",
    defaultValues: {
      text: choice?.text || "",
      to_node_id: choice?.to_node_id || "",
      order: choice?.order || 0,
      requires_state: choice?.requires_state || null,
      sets_state: choice?.sets_state || null,
    },
  })

  // Reset form when choice changes (edit mode)
  useEffect(() => {
    if (choice) {
      reset({
        text: choice.text,
        to_node_id: choice.to_node_id,
        order: choice.order,
        requires_state: choice.requires_state,
        sets_state: choice.sets_state,
      })
    }
  }, [choice, reset])

  const onSubmit: SubmitHandler<ChoiceFormData> = (data) => {
    if (isEditMode) {
      updateMutation.mutate(
        {
          choiceId: choice.id,
          data: {
            text: data.text,
            to_node_id: data.to_node_id,
            order: data.order,
            requires_state: data.requires_state,
            sets_state: data.sets_state,
          },
        },
        {
          onSuccess: () => {
            setIsOpen(false)
            onSuccess?.()
          },
        }
      )
    } else {
      createMutation.mutate(
        {
          text: data.text,
          from_node_id: fromNodeId,
          to_node_id: data.to_node_id,
          order: data.order || 0,
          requires_state: data.requires_state,
          sets_state: data.sets_state,
        },
        {
          onSuccess: () => {
            reset()
            setIsOpen(false)
            onSuccess?.()
          },
        }
      )
    }
  }

  return (
    <DialogRoot
      size={{ base: "sm", md: "lg" }}
      placement="center"
      open={isOpen}
      onOpenChange={({ open }) => {
        setIsOpen(open)
        if (!open && !isEditMode) reset()
      }}
    >
      <DialogTrigger asChild>
        {trigger || <Button size="sm">Add Choice</Button>}
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>{isEditMode ? "Edit Choice" : "Add Choice"}</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <VStack gap={4} align="stretch">
              <Text fontSize="sm" color="fg.muted">
                {isEditMode
                  ? "Modify the choice and its conditions"
                  : "Create a branching path for your story"}
              </Text>

              <Field
                required
                invalid={!!errors.text}
                errorText={errors.text?.message}
                label="Choice Text"
              >
                <Input
                  {...register("text", {
                    required: "Choice text is required",
                    maxLength: {
                      value: 200,
                      message: "Choice text must be 200 characters or less",
                    },
                  })}
                  placeholder="Enter the dark forest"
                  type="text"
                />
              </Field>

              <Field
                required
                invalid={!!errors.to_node_id}
                errorText={errors.to_node_id?.message}
                label="Destination Node"
              >
                <NativeSelectRoot>
                  <NativeSelectField
                    {...register("to_node_id", {
                      required: "Destination node is required",
                    })}
                    placeholder="Select destination node"
                  >
                    <option value="">Select destination node</option>
                    {availableNodes.map((node) => (
                      <option key={node.id} value={node.id}>
                        {node.title}
                        {node.is_end_node && " (End)"}
                      </option>
                    ))}
                  </NativeSelectField>
                </NativeSelectRoot>
              </Field>

              <Field
                invalid={!!errors.order}
                errorText={errors.order?.message}
                label="Display Order"
                helperText="Lower numbers appear first"
              >
                <Input
                  {...register("order", {
                    valueAsNumber: true,
                  })}
                  type="number"
                  placeholder="0"
                />
              </Field>

              <Separator />

              <Box>
                <Text fontSize="sm" fontWeight="bold" mb={2}>
                  Advanced: Conditional Logic
                </Text>
                <Text fontSize="xs" color="fg.muted" mb={4}>
                  Control when this choice appears and what state changes it makes
                </Text>

                <VStack gap={4} align="stretch">
                  <Controller
                    control={control}
                    name="requires_state"
                    render={({ field }) => (
                      <StateConditionEditor
                        label="Show this choice only if:"
                        value={field.value ?? null}
                        onChange={field.onChange}
                      />
                    )}
                  />

                  <Controller
                    control={control}
                    name="sets_state"
                    render={({ field }) => (
                      <StateConditionEditor
                        label="When chosen, set state:"
                        value={field.value ?? null}
                        onChange={field.onChange}
                      />
                    )}
                  />
                </VStack>
              </Box>
            </VStack>
          </DialogBody>

          <DialogFooter gap={2}>
            <DialogActionTrigger asChild>
              <Button variant="subtle" colorPalette="gray" disabled={isSubmitting}>
                Cancel
              </Button>
            </DialogActionTrigger>
            <Button
              variant="solid"
              colorPalette="blue"
              type="submit"
              disabled={!isValid}
              loading={isSubmitting || createMutation.isPending || updateMutation.isPending}
            >
              {isEditMode ? "Update Choice" : "Create Choice"}
            </Button>
          </DialogFooter>
        </form>
        <DialogCloseTrigger />
      </DialogContent>
    </DialogRoot>
  )
}

export default ChoiceEditor
