/**
 * EditDrawer Component
 *
 * Reusable slide-out panel for editing text content.
 * Uses React Hook Form for validation and state management.
 *
 * Features:
 * - Form validation (required, non-empty)
 * - Disable save if unchanged or invalid
 * - Loading state during save
 * - Auto-reset on open
 * - Accessible (keyboard navigation, focus management)
 *
 * Phase 5 - Message Management Features
 */

import { useEffect } from "react"
import { useForm } from "react-hook-form"
import {
  DrawerRoot,
  DrawerBackdrop,
  DrawerContent,
  DrawerHeader,
  DrawerTitle,
  DrawerBody,
  DrawerFooter,
  DrawerCloseTrigger,
} from "@chakra-ui/react"
import { Button, Textarea, VStack, Text } from "@chakra-ui/react"
import { Field } from "@/components/ui/field"

interface EditDrawerProps {
  /** Whether drawer is open */
  isOpen: boolean
  /** Callback to close drawer */
  onClose: () => void
  /** Callback to save changes (receives new content) */
  onSave: (content: string) => Promise<void>
  /** Initial content to edit */
  initialContent: string
  /** Drawer title (default: "Edit Message") */
  title?: string
  /** Optional description text */
  description?: string
  /** Whether save operation is in progress */
  isSaving?: boolean
}

interface EditForm {
  content: string
}

/**
 * EditDrawer - Generic slide-out panel for editing content
 *
 * Handles form state, validation, and submission.
 * Resets form when drawer opens with new content.
 *
 * @param isOpen - Controls drawer visibility
 * @param onClose - Called when drawer should close
 * @param onSave - Called with new content when save is clicked
 * @param initialContent - Content to edit
 * @param title - Drawer title (optional)
 * @param description - Helper text (optional)
 * @param isSaving - Loading state for save button
 *
 * @example
 * ```tsx
 * <EditDrawer
 *   isOpen={isEditDrawerOpen}
 *   onClose={() => setIsEditDrawerOpen(false)}
 *   onSave={async (content) => {
 *     await editMessage(messageId, content)
 *   }}
 *   initialContent={message.content}
 *   title="Edit Message"
 *   description="Changes will be visible to all participants."
 *   isSaving={isEditing}
 * />
 * ```
 */
const EditDrawer = ({
  isOpen,
  onClose,
  onSave,
  initialContent,
  title = "Edit Message",
  description,
  isSaving = false,
}: EditDrawerProps) => {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isDirty, isValid },
  } = useForm<EditForm>({
    mode: "onChange",
    defaultValues: {
      content: initialContent,
    },
  })

  // Reset form when drawer opens with new content
  useEffect(() => {
    if (isOpen) {
      reset({ content: initialContent })
    }
  }, [isOpen, initialContent, reset])

  const onSubmit = async (data: EditForm) => {
    try {
      await onSave(data.content)
      onClose()
    } catch (error) {
      // Error handling via mutation error handler
      // Don't close drawer on error
    }
  }

  return (
    <DrawerRoot
      open={isOpen}
      onOpenChange={(e) => !e.open && onClose()}
      size="md"
      placement="end"
    >
      <DrawerBackdrop />
      <DrawerContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DrawerHeader>
            <DrawerTitle>{title}</DrawerTitle>
          </DrawerHeader>
          <DrawerCloseTrigger />

          <DrawerBody>
            <VStack gap={4} align="stretch">
              {description && (
                <Text fontSize="sm" color="gray.600">
                  {description}
                </Text>
              )}

              <Field
                label="Message Content"
                required
                invalid={!!errors.content}
                errorText={errors.content?.message}
              >
                <Textarea
                  {...register("content", {
                    required: "Message content is required",
                    minLength: {
                      value: 1,
                      message: "Message cannot be empty",
                    },
                    validate: (value) => {
                      if (!value.trim()) {
                        return "Message cannot be only whitespace"
                      }
                      return true
                    },
                  })}
                  rows={10}
                  placeholder="Edit message content..."
                />
              </Field>

              <Text fontSize="xs" color="gray.500">
                Note: Editing does not change whether this message is included
                in agent context.
              </Text>
            </VStack>
          </DrawerBody>

          <DrawerFooter gap={2}>
            <Button variant="outline" onClick={onClose} disabled={isSaving}>
              Cancel
            </Button>
            <Button
              type="submit"
              colorPalette="blue"
              loading={isSaving}
              disabled={!isDirty || !isValid}
            >
              Save Changes
            </Button>
          </DrawerFooter>
        </form>
      </DrawerContent>
    </DrawerRoot>
  )
}

export default EditDrawer
