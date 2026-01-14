/**
 * AddRoom Component
 *
 * Dialog for creating a new room with optional story association.
 */

import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import { Loader2, Plus } from "lucide-react"
import { useState } from "react"
import { type SubmitHandler, useForm } from "react-hook-form"

import type { ApiError } from "@/client/core/ApiError"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useStories } from "@/hooks/stories/useStories"
import useCustomToast from "@/hooks/useCustomToast"
import { cn } from "@/lib/utils"
import { type CreateRoomInput, RoomService } from "@/services/roomService"
import { handleError } from "@/utils"

const { showErrorToast } = useCustomToast()

interface AddRoomProps {
  /** Pre-select a story when creating the room */
  defaultStoryId?: string
  /** Custom trigger element (defaults to "Create Room" button) */
  trigger?: React.ReactNode
  /** Callback when dialog open state changes */
  onOpenChange?: (open: boolean) => void
}

export default function AddRoom({ defaultStoryId, trigger, onOpenChange }: AddRoomProps = {}) {
  const [isOpen, setIsOpen] = useState(false)
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const { showSuccessToast } = useCustomToast()
  const { data: storiesData, isLoading: isLoadingStories } = useStories()

  const handleOpenChange = (open: boolean) => {
    setIsOpen(open)
    onOpenChange?.(open)
  }

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isValid, isSubmitting },
  } = useForm<CreateRoomInput>({
    mode: "onBlur",
    defaultValues: {
      title: "",
      story_id: defaultStoryId || null,
    },
  })

  const mutation = useMutation({
    mutationFn: (data: CreateRoomInput) => RoomService.createRoom(data),
    onSuccess: (room) => {
      showSuccessToast("Room created successfully.")
      reset()
      handleOpenChange(false)
      navigate({ to: "/room/$roomId", params: { roomId: room.room_id } })
    },
    onError: (err: ApiError) => {
      handleError.call(showErrorToast, err as ApiError)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["rooms"] })
    },
  })

  const onSubmit: SubmitHandler<CreateRoomInput> = (data) => {
    const payload = {
      ...data,
      story_id: data.story_id || null,
    }
    mutation.mutate(payload)
  }

  return (
    <Dialog open={isOpen} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        {trigger || (
          <Button className="my-4">
            <Plus className="h-4 w-4" />
            Create Room
          </Button>
        )}
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Create New Room</DialogTitle>
            <DialogDescription>
              Create a collaborative space for story creation.
            </DialogDescription>
          </DialogHeader>

          <div className="flex flex-col gap-4 py-4">
            {/* Room Title Field */}
            <div className="space-y-2">
              <Label htmlFor="title">
                Room Title <span className="text-destructive">*</span>
              </Label>
              <Input
                id="title"
                {...register("title", {
                  required: "Room title is required",
                  minLength: {
                    value: 3,
                    message: "Title must be at least 3 characters",
                  },
                  maxLength: {
                    value: 100,
                    message: "Title must be less than 100 characters",
                  },
                })}
                placeholder="e.g., My Story Workshop"
                type="text"
                className={cn(errors.title && "border-destructive")}
              />
              {errors.title && (
                <p className="text-sm text-destructive">
                  {errors.title.message}
                </p>
              )}
            </div>

            {/* Story Selection Field */}
            <div className="space-y-2">
              <Label htmlFor="story_id">Link to Story (Optional)</Label>
              <select
                id="story_id"
                {...register("story_id")}
                className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
              >
                <option value="">
                  {isLoadingStories
                    ? "Loading stories..."
                    : "No story selected"}
                </option>
                {storiesData?.data.map((story) => (
                  <option key={story.id} value={story.id}>
                    {story.title}
                  </option>
                ))}
              </select>
              <p className="text-sm text-muted-foreground">
                Associate this room with a story for collaborative editing
              </p>
            </div>
          </div>

          <DialogFooter>
            <DialogClose asChild>
              <Button type="button" variant="outline" disabled={isSubmitting}>
                Cancel
              </Button>
            </DialogClose>
            <Button type="submit" disabled={!isValid || isSubmitting}>
              {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
              Create Room
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
