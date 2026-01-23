import { useMutation, useQueryClient } from "@tanstack/react-query"
import {
  type StoryNodeCreate,
  type StoryNodeUpdate,
  StorynodesService,
} from "@/client"
import type { ApiError } from "@/client/core/ApiError"
import { showErrorToast, showSuccessToast } from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

// Mutation hook for creating a node
export const useCreateNode = (storyId: string) => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: StoryNodeCreate) =>
      StorynodesService.createStorynode({ requestBody: data }),
    onSuccess: () => {
      showSuccessToast("Node created successfully!")
      queryClient.invalidateQueries({ queryKey: ["stories", storyId, "nodes"] })
    },
    onError: (err: ApiError) => {
      handleError.call(showErrorToast, err as ApiError)
    },
  })
}

// Mutation hook for updating a node
export const useUpdateNode = (storyId: string, nodeId: string) => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: StoryNodeUpdate) =>
      StorynodesService.updateStorynode({ id: nodeId, requestBody: data }),
    onSuccess: () => {
      showSuccessToast("Node updated successfully!")
      queryClient.invalidateQueries({ queryKey: ["stories", storyId, "nodes"] })
      queryClient.invalidateQueries({ queryKey: ["nodes", nodeId] })
    },
    onError: (err: ApiError) => {
      handleError.call(showErrorToast, err as ApiError)
    },
  })
}

// Mutation hook for deleting a node
export const useDeleteNode = (storyId: string) => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (nodeId: string) =>
      StorynodesService.deleteStorynode({ id: nodeId }),
    onSuccess: () => {
      showSuccessToast("Node deleted successfully.")
      queryClient.invalidateQueries({ queryKey: ["stories", storyId, "nodes"] })
    },
    onError: (err: ApiError) => {
      handleError.call(showErrorToast, err as ApiError)
    },
  })
}
