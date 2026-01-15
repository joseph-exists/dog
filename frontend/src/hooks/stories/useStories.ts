import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { StoriesService, type StoryCreate } from "@/client"
import type { ApiError } from "@/client/core/ApiError"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

// Query hook for fetching stories
export const useStories = () => {
  return useQuery({
    queryKey: ["stories"],
    queryFn: () => StoriesService.readStories({ skip: 0, limit: 100 }),
  })
}

const { showErrorToast } = useCustomToast()

// Mutation hook for creating a story
export const useCreateStory = () => {
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()

  return useMutation({
    mutationFn: (data: StoryCreate) =>
      StoriesService.createStory({ requestBody: data }),
    onSuccess: () => {
      showSuccessToast("Story created successfully!")
      queryClient.invalidateQueries({ queryKey: ["stories"] })
    },
    onError: (err: ApiError) => {
      handleError.call(showErrorToast, err as ApiError)
    },
  })
}

// Mutation hook for deleting a story
export const useDeleteStory = () => {
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()

  return useMutation({
    mutationFn: (storyId: string) =>
      StoriesService.deleteStory({ id: storyId }),
    onSuccess: () => {
      showSuccessToast("Story deleted successfully.")
      queryClient.invalidateQueries({ queryKey: ["stories"] })
    },
    onError: (err: ApiError) => {
      handleError.call(showErrorToast, err as ApiError)
    },
  })
}

// Mutation hook for publishing a story
export const usePublishStory = () => {
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()

  return useMutation({
    mutationFn: (storyId: string) =>
      StoriesService.publishStory({ id: storyId }),
    onSuccess: (data) => {
      showSuccessToast(
        `Story published as v${data.published_version}! Now visible in catalog.`,
      )
      queryClient.invalidateQueries({ queryKey: ["stories"] })
      queryClient.invalidateQueries({ queryKey: ["stories", data.id] })
    },
    onError: (err: ApiError) => {
      handleError.call(showErrorToast, err as ApiError)
    },
  })
}

// Mutation hook for unpublishing a story
export const useUnpublishStory = () => {
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()

  return useMutation({
    mutationFn: (storyId: string) =>
      StoriesService.unpublishStory({ id: storyId }),
    onSuccess: (data) => {
      showSuccessToast("Story unpublished. Hidden from catalog.")
      queryClient.invalidateQueries({ queryKey: ["stories"] })
      queryClient.invalidateQueries({ queryKey: ["stories", data.id] })
    },
    onError: (err: ApiError) => {
      handleError.call(showErrorToast, err as ApiError)
    },
  })
}

// Mutation hook for creating a new version of a published story
export const useCreateNewVersion = () => {
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()

  return useMutation({
    mutationFn: (storyId: string) =>
      StoriesService.createNewStoryVersion({ id: storyId }),
    onSuccess: (data) => {
      showSuccessToast(
        `Version ${data.current_version} created! You can now edit without affecting published version.`,
      )
      queryClient.invalidateQueries({ queryKey: ["stories"] })
      queryClient.invalidateQueries({ queryKey: ["stories", data.id] })
      queryClient.invalidateQueries({ queryKey: ["stories", data.id, "nodes"] })
    },
    onError: (err: ApiError) => {
      handleError.call(showErrorToast, err as ApiError)
    },
  })
}

// Mutation hook for cloning a story (creates new story with same metadata)
export const useCloneStory = () => {
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()

  return useMutation({
    mutationFn: async (sourceStory: {
      title: string
      description?: string | null
    }) => {
      // Create a new story with copied metadata
      const clonedStory = await StoriesService.createStory({
        requestBody: {
          title: `${sourceStory.title} (Copy)`,
          description: sourceStory.description || undefined,
        },
      })
      return clonedStory
    },
    onSuccess: (data) => {
      showSuccessToast(`Story cloned! "${data.title}" created as a new draft.`)
      queryClient.invalidateQueries({ queryKey: ["stories"] })
    },
    onError: (err: ApiError) => {
      handleError.call(showErrorToast, err as ApiError)
    },
  })
}
