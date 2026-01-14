import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import {
  type NodeChoiceBase,
  type NodeChoiceCreate,
  NodeChoicesService,
  type NodeChoiceUpdate,
  StorynodesService,
} from "@/client"
import type { ApiError } from "@/client/core/ApiError"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

// Query hook for fetching choices from a node
export const useChoicesForNode = (nodeId: string | null) => {
  return useQuery({
    queryKey: ["nodes", nodeId, "choices"],
    queryFn: () =>
      StorynodesService.readNodeChoices({
        nodeId: nodeId!,
        skip: 0,
        limit: 100,
      }),
    enabled: !!nodeId, // Only run query if nodeId exists
  })
}

const { showErrorToast } = useCustomToast()

// Mutation hook for creating a choice from a node (simpler API)
export const useCreateChoiceFromNode = (nodeId: string) => {
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()

  return useMutation({
    mutationFn: (data: NodeChoiceBase) =>
      StorynodesService.createNodeChoiceFromNode({ nodeId, requestBody: data }),
    onSuccess: () => {
      showSuccessToast("Choice created successfully!")
      queryClient.invalidateQueries({ queryKey: ["nodes", nodeId, "choices"] })
    },
    onError: (err: ApiError) => {
      handleError.call(showErrorToast, err as ApiError)
    },
  })
}

// Mutation hook for creating a choice (full API with from/to node IDs)
export const useCreateChoice = () => {
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()

  return useMutation({
    mutationFn: (data: NodeChoiceCreate) =>
      NodeChoicesService.createNodeChoice({ requestBody: data }),
    onSuccess: (result) => {
      showSuccessToast("Choice created successfully!")
      queryClient.invalidateQueries({
        queryKey: ["nodes", result.from_node_id, "choices"],
      })
    },
    onError: (err: ApiError) => {
      handleError.call(showErrorToast, err as ApiError)
    },
  })
}

// Mutation hook for updating a choice
export const useUpdateChoice = (fromNodeId: string) => {
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()

  return useMutation({
    mutationFn: ({
      choiceId,
      data,
    }: {
      choiceId: string
      data: NodeChoiceUpdate
    }) => NodeChoicesService.updateNodeChoice({ choiceId, requestBody: data }),
    onSuccess: () => {
      showSuccessToast("Choice updated successfully!")
      queryClient.invalidateQueries({
        queryKey: ["nodes", fromNodeId, "choices"],
      })
    },
    onError: (err: ApiError) => {
      handleError.call(showErrorToast, err as ApiError)
    },
  })
}

// Mutation hook for deleting a choice
export const useDeleteChoice = (fromNodeId: string | null) => {
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()

  return useMutation({
    mutationFn: (choiceId: string) =>
      NodeChoicesService.deleteNodeChoice({ choiceId }),
    onSuccess: () => {
      showSuccessToast("Choice deleted successfully.")
      if (fromNodeId) {
        queryClient.invalidateQueries({
          queryKey: ["nodes", fromNodeId, "choices"],
        })
      }
    },
    onError: (err: ApiError) => {
      handleError.call(showErrorToast, err as ApiError)
    },
  })
}
