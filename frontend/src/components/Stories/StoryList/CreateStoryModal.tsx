import { useState } from "react"
import { type SubmitHandler, useForm } from "react-hook-form"
import { Button, DialogActionTrigger, Input, Text, Textarea, VStack } from "@chakra-ui/react"
import { FaPlus } from "react-icons/fa"

import type { StoryCreate } from "@/client"
import { useCreateStory } from "@/hooks/stories/useStories"
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

  return (
    <DialogRoot
      size={{ base: "xs", md: "md" }}
      placement="center"
      open={isOpen}
      onOpenChange={({ open }) => {
        setIsOpen(open)
        if (!open) reset()
      }}
    >
      <DialogTrigger asChild>
        <Button colorPalette="blue" my={4}>
          <FaPlus fontSize="16px" />
          New Story
        </Button>
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Create New Story</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <Text mb={4} color="gray.600">
              Begin crafting your adventure! Give your story a title and description to get started.
            </Text>
            <VStack gap={4}>
              <Field
                required
                invalid={!!errors.title}
                errorText={errors.title?.message}
                label="Story Title"
              >
                <Input
                  {...register("title", {
                    required: "Story title is required",
                    maxLength: {
                      value: 100,
                      message: "Title must be 100 characters or less",
                    },
                  })}
                  placeholder="The Dark Forest Adventure"
                  type="text"
                />
              </Field>

              <Field
                invalid={!!errors.description}
                errorText={errors.description?.message}
                label="Description (optional)"
              >
                <Textarea
                  {...register("description", {
                    maxLength: {
                      value: 500,
                      message: "Description must be 500 characters or less",
                    },
                  })}
                  placeholder="A spooky journey through an enchanted forest filled with mysteries and choices..."
                  rows={4}
                />
              </Field>
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
              loading={isSubmitting}
            >
              Create Story
            </Button>
          </DialogFooter>
        </form>
        <DialogCloseTrigger />
      </DialogContent>
    </DialogRoot>
  )
}

export default CreateStoryModal
