import { useMutation, useQueryClient } from "@tanstack/react-query"
import type { ApiError } from "@/client/core/ApiError"
import { StorynodesService, type StoryNodeCreate, type StoryNodeUpdate } from "@/client"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

// Mutation hook for creating a node
export const useCreateNode = (storyId: string) => {
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()

  return useMutation({
    mutationFn: (data: StoryNodeCreate) =>
      StorynodesService.createStorynode({ requestBody: data }),
    onSuccess: () => {
      showSuccessToast("Node created successfully!")
      queryClient.invalidateQueries({ queryKey: ["stories", storyId, "nodes"] })
    },
    onError: (err: ApiError) => {
      handleError(err)
    },
  })
}

// Mutation hook for updating a node
export const useUpdateNode = (storyId: string, nodeId: string) => {
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()

  return useMutation({
    mutationFn: (data: StoryNodeUpdate) =>
      StorynodesService.updateStorynode({ id: nodeId, requestBody: data }),
    onSuccess: () => {
      showSuccessToast("Node updated successfully!")
      queryClient.invalidateQueries({ queryKey: ["stories", storyId, "nodes"] })
      queryClient.invalidateQueries({ queryKey: ["nodes", nodeId] })
    },
    onError: (err: ApiError) => {
      handleError(err)
    },
  })
}

// Mutation hook for deleting a node
export const useDeleteNode = (storyId: string) => {
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()

  return useMutation({
    mutationFn: (nodeId: string) =>
      StorynodesService.deleteStorynode({ id: nodeId }),
    onSuccess: () => {
      showSuccessToast("Node deleted successfully.")
      queryClient.invalidateQueries({ queryKey: ["stories", storyId, "nodes"] })
    },
    onError: (err: ApiError) => {
      handleError(err)
    },
  })
}
