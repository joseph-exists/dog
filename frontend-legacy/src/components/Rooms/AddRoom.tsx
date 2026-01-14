import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import { useState } from "react"
import { type SubmitHandler, useForm } from "react-hook-form"
import { FaPlus } from "react-icons/fa"

import type { ApiError } from "@/client/core/ApiError"
import { useStories } from "@/hooks/stories/useStories"
import useCustomToast from "@/hooks/useCustomToast"
import { type CreateRoomInput, RoomService } from "@/services/roomService"
import { handleError } from "@/utils"
import {
  Button,
  DialogActionTrigger,
  DialogTitle,
  Input,
  NativeSelectField,
  NativeSelectRoot,
  Text,
  VStack,
} from "@chakra-ui/react"
import {
  DialogBody,
  DialogCloseTrigger,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogRoot,
  DialogTrigger,
} from "../ui/dialog"
import { Field } from "../ui/field"

const AddRoom = () => {
  const [isOpen, setIsOpen] = useState(false)
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const { showSuccessToast } = useCustomToast()
  const { data: storiesData, isLoading: isLoadingStories } = useStories()

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isValid, isSubmitting },
  } = useForm<CreateRoomInput>({
    mode: "onBlur",
    defaultValues: {
      title: "",
      story_id: null,
    },
  })

  const mutation = useMutation({
    mutationFn: (data: CreateRoomInput) => RoomService.createRoom(data),
    onSuccess: (room) => {
      showSuccessToast("Room created successfully.")
      reset()
      setIsOpen(false)
      // Navigate to the new room
      navigate({ to: "/room/$roomId", params: { roomId: room.room_id } })
    },
    onError: (err: ApiError) => {
      handleError(err)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["rooms"] })
    },
  })

  const onSubmit: SubmitHandler<CreateRoomInput> = (data) => {
    // Convert empty string to null for story_id
    const payload = {
      ...data,
      story_id: data.story_id || null,
    }
    mutation.mutate(payload)
  }

  return (
    <DialogRoot
      size={{ base: "xs", md: "md" }}
      placement="center"
      open={isOpen}
      onOpenChange={({ open }) => setIsOpen(open)}
    >
      <DialogTrigger asChild>
        <Button value="add-room" my={4}>
          <FaPlus fontSize="16px" />
          Create Room
        </Button>
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Create New Room</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <Text mb={4}>Create a collaborative space for story creation.</Text>
            <VStack gap={4}>
              <Field
                required
                invalid={!!errors.title}
                errorText={errors.title?.message}
                label="Room Title"
              >
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
                />
              </Field>

              <Field
                label="Link to Story (Optional)"
                helperText="Associate this room with a story for collaborative editing"
              >
                <NativeSelectRoot>
                  <NativeSelectField {...register("story_id")}>
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
                  </NativeSelectField>
                </NativeSelectRoot>
              </Field>
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
              type="submit"
              disabled={!isValid}
              loading={isSubmitting}
            >
              Create Room
            </Button>
          </DialogFooter>
        </form>
        <DialogCloseTrigger />
      </DialogContent>
    </DialogRoot>
  )
}

export default AddRoom
