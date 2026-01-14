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
 */

import {
  Drawer,
  DrawerClose,
  DrawerContent,
  DrawerDescription,
  DrawerFooter,
  DrawerHeader,
  DrawerTitle,
} from "@/components/ui/drawer"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { cn } from "@/lib/utils"
import { useEffect } from "react"
import { useForm } from "react-hook-form"

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
 * Textarea component with consistent styling
 * Following the same pattern as shadcn Input component
 */
function Textarea({
  className,
  ...props
}: React.ComponentProps<"textarea">) {
  return (
    <textarea
      data-slot="textarea"
      className={cn(
        "placeholder:text-muted-foreground selection:bg-primary selection:text-primary-foreground dark:bg-input/30 border-input w-full min-w-0 rounded-md border bg-transparent px-3 py-2 text-base shadow-xs transition-[color,box-shadow] outline-none disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50 md:text-sm",
        "focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]",
        "aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive",
        "resize-none",
        className
      )}
      {...props}
    />
  )
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
    } catch {
      // Error handling via mutation error handler
      // Don't close drawer on error
    }
  }

  // Handle drawer open state change
  const handleOpenChange = (open: boolean) => {
    if (!open) {
      onClose()
    }
  }

  return (
    <Drawer direction="right" open={isOpen} onOpenChange={handleOpenChange}>
      <DrawerContent className="h-full w-full max-w-md">
        <form onSubmit={handleSubmit(onSubmit)} className="flex h-full flex-col">
          <DrawerHeader>
            <DrawerTitle>{title}</DrawerTitle>
            {description && (
              <DrawerDescription>{description}</DrawerDescription>
            )}
          </DrawerHeader>

          <div className="flex flex-1 flex-col gap-4 overflow-auto px-4">
            <div className="flex flex-col gap-2">
              <Label htmlFor="content">
                Message Content <span className="text-destructive">*</span>
              </Label>
              <Textarea
                id="content"
                rows={10}
                placeholder="Edit message content..."
                aria-invalid={!!errors.content}
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
              />
              {errors.content && (
                <p className="text-destructive text-sm">
                  {errors.content.message}
                </p>
              )}
            </div>

            <p className="text-muted-foreground text-xs">
              Note: Editing does not change whether this message is included
              in agent context.
            </p>
          </div>

          <DrawerFooter className="flex-row justify-end gap-2">
            <DrawerClose asChild>
              <Button variant="outline" disabled={isSaving}>
                Cancel
              </Button>
            </DrawerClose>
            <Button
              type="submit"
              disabled={!isDirty || !isValid || isSaving}
            >
              {isSaving ? "Saving..." : "Save Changes"}
            </Button>
          </DrawerFooter>
        </form>
      </DrawerContent>
    </Drawer>
  )
}

export default EditDrawer
