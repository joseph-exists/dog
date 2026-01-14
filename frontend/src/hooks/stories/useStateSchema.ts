import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import {
  StoriesService,
  type StoryStateVariableBase,
  type StoryStateVariableUpdate,
} from "@/client"
import type { ApiError } from "@/client/core/ApiError"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

// Query hook for fetching state schema variables
export const useStateSchema = (storyId: string, version: number) => {
  return useQuery({
    queryKey: ["stories", storyId, "state-schema", version],
    queryFn: () =>
      StoriesService.readStoryStateSchema({
        storyId,
        version,
        skip: 0,
        limit: 100,
      }),
    enabled: !!storyId && version > 0,
  })
}

// Query hook for validating state schema
export const useValidateStateSchema = (storyId: string, version: number) => {
  return useQuery({
    queryKey: ["stories", storyId, "state-schema", version, "validate"],
    queryFn: () =>
      StoriesService.validateStoryStateSchema({ storyId, version }),
    enabled: !!storyId && version > 0,
  })
}

const { showSuccessToast, showErrorToast } = useCustomToast()

// Mutation hook for creating a state variable
export const useCreateStateVariable = (storyId: string, version: number) => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: StoryStateVariableBase) =>
      StoriesService.createStoryStateVariable({
        storyId,
        version,
        requestBody: data,
      }),
    onSuccess: () => {
      showSuccessToast("State variable created successfully!")
      queryClient.invalidateQueries({
        queryKey: ["stories", storyId, "state-schema", version],
      })
    },
    onError: (err: ApiError) => {
      handleError.call(showErrorToast, err as ApiError)
    },
  })
}

// Mutation hook for updating a state variable
export const useUpdateStateVariable = (storyId: string, version: number) => {
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()

  return useMutation({
    mutationFn: ({
      variableId,
      data,
    }: {
      variableId: string
      data: StoryStateVariableUpdate
    }) =>
      StoriesService.updateStoryStateVariable({
        storyId,
        version,
        variableId,
        requestBody: data,
      }),
    onSuccess: () => {
      showSuccessToast("State variable updated successfully!")
      queryClient.invalidateQueries({
        queryKey: ["stories", storyId, "state-schema", version],
      })
    },
    onError: (err: ApiError) => {
      handleError.call(showErrorToast, err as ApiError)
    },
  })
}

// Mutation hook for deleting a state variable
export const useDeleteStateVariable = (storyId: string, version: number) => {
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()

  return useMutation({
    mutationFn: (variableId: string) =>
      StoriesService.deleteStoryStateVariable({
        storyId,
        version,
        variableId,
      }),
    onSuccess: () => {
      showSuccessToast("State variable deleted successfully.")
      queryClient.invalidateQueries({
        queryKey: ["stories", storyId, "state-schema", version],
      })
    },
    onError: (err: ApiError) => {
      handleError.call(showErrorToast, err as ApiError)
    },
  })
}
