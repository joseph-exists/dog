/**
 * CreateStoryModal - Dialog for creating new stories
 *
 * Uses react-hook-form for validation and the useCreateStory mutation.
 * Opens as a Dialog with title and description fields.
 */

import { Plus } from "lucide-react"
import { useState } from "react"
import { type SubmitHandler, useForm } from "react-hook-form"

import type { StoryCreate } from "@/client"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useCreateStory } from "@/hooks/stories/useStories"
import { cn } from "@/lib/utils"

/** Textarea with consistent styling */
function Textarea({ className, ...props }: React.ComponentProps<"textarea">) {
  return (
    <textarea
      className={cn(
        "placeholder:text-muted-foreground border-input w-full rounded-md border bg-transparent px-3 py-2 text-sm shadow-xs outline-none",
        "focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]",
        "disabled:cursor-not-allowed disabled:opacity-50",
        "resize-none",
        className,
      )}
      {...props}
    />
  )
}

const CreateStoryModal = () => {
  const [isOpen, setIsOpen] = useState(false)
  const mutation = useCreateStory()

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isValid, isSubmitting },
  } = useForm<StoryCreate>({
    mode: "onBlur",
    defaultValues: {
      title: "",
      description: "",
      is_published: false,
    },
  })

  const onSubmit: SubmitHandler<StoryCreate> = (data) => {
    mutation.mutate(data, {
      onSuccess: () => {
        reset()
        setIsOpen(false)
      },
    })
  }

  const handleOpenChange = (open: boolean) => {
    setIsOpen(open)
    if (!open) reset()
  }

  return (
    <Dialog open={isOpen} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          New Story
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Create New Story</DialogTitle>
            <DialogDescription>
              Begin crafting your adventure! Give your story a title and
              description to get started.
            </DialogDescription>
          </DialogHeader>

          <div className="flex flex-col gap-4 py-4">
            <div className="flex flex-col gap-2">
              <Label htmlFor="title">
                Story Title <span className="text-destructive">*</span>
              </Label>
              <Input
                id="title"
                placeholder="The Dark Forest Adventure"
                {...register("title", {
                  required: "Story title is required",
                  maxLength: {
                    value: 100,
                    message: "Title must be 100 characters or less",
                  },
                })}
              />
              {errors.title && (
                <p className="text-destructive text-sm">
                  {errors.title.message}
                </p>
              )}
            </div>

            <div className="flex flex-col gap-2">
              <Label htmlFor="description">Description (optional)</Label>
              <Textarea
                id="description"
                rows={4}
                placeholder="A spooky journey through an enchanted forest filled with mysteries and choices..."
                {...register("description", {
                  maxLength: {
                    value: 500,
                    message: "Description must be 500 characters or less",
                  },
                })}
              />
              {errors.description && (
                <p className="text-destructive text-sm">
                  {errors.description.message}
                </p>
              )}
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setIsOpen(false)}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={!isValid || isSubmitting}>
              {isSubmitting ? "Creating..." : "Create Story"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export default CreateStoryModal
