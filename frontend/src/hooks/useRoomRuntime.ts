/**
 * useRoomRuntime Hook
 *
 * Purpose: Fetch and mutate the room runtime projection for StoryPanel.
 * Handles optimistic concurrency via expected_revision and exposes UI flags.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useCallback, useState } from "react"
import type { ApiError } from "@/client"
import useCustomToast from "@/hooks/useCustomToast"
import {
  RoomRuntimeService,
  type RoomRuntimeViewModel,
} from "@/services/roomRuntimeService"
import { handleError } from "@/utils"

export interface UseRoomRuntimeResult {
  runtime: RoomRuntimeViewModel | null
  isLoading: boolean
  error: ApiError | null
  refetch: () => Promise<unknown>

  start: (params: { userPersonaId: string; storyVersion?: number | null }) => Promise<void>
  advance: (choiceId: string) => Promise<void>
  rewind: (targetChoiceId: string) => Promise<void>
  reset: () => Promise<void>

  isStarting: boolean
  isAdvancing: boolean
  isRewinding: boolean
  isResetting: boolean
  pendingChoiceId: string | null
}

const { showErrorToast } = useCustomToast()

const RUNTIME_QUERY_KEY = (roomId: string) => ["rooms", roomId, "runtime"]

function shouldTreatAsNoRuntime(error: ApiError): boolean {
  return error.status === 404 || error.status === 410
}

function handleRuntimeMutationError(
  error: ApiError,
  onRefetch: () => void,
) {
  if (error.status === 403) {
    showErrorToast("You don't have permission to modify this runtime.")
    onRefetch()
    return
  }

  if (error.status === 409) {
    showErrorToast("Story updated by someone else.")
    onRefetch()
    return
  }

  if (error.status === 422) {
    showErrorToast("That choice is no longer valid.")
    onRefetch()
    return
  }

  handleError.call(showErrorToast, error)
}

export function useRoomRuntime(roomId: string): UseRoomRuntimeResult {
  const queryClient = useQueryClient()
  const [pendingChoiceId, setPendingChoiceId] = useState<string | null>(null)

  const runtimeQueryKey = RUNTIME_QUERY_KEY(roomId)

  const {
    data: runtime = null,
    isLoading,
    error,
    refetch,
  } = useQuery<RoomRuntimeViewModel | null, ApiError>({
    queryKey: runtimeQueryKey,
    queryFn: async () => {
      try {
        return await RoomRuntimeService.getRuntime(roomId)
      } catch (err) {
        if (err instanceof Error && "status" in err) {
          const apiError = err as ApiError
          if (shouldTreatAsNoRuntime(apiError)) {
            return null
          }
        }
        throw err
      }
    },
    refetchInterval: false,
    refetchIntervalInBackground: false,
  })

  const invalidateRuntime = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: runtimeQueryKey })
  }, [queryClient, runtimeQueryKey])

  const { mutateAsync: advanceMutation, isPending: isAdvancing } = useMutation<
    RoomRuntimeViewModel,
    ApiError,
    string
  >({
    mutationFn: (choiceId: string) =>
      RoomRuntimeService.advance(roomId, {
        choice_id: choiceId,
        expected_revision: runtime?.revision ?? null,
      }),
    onMutate: (choiceId) => {
      setPendingChoiceId(choiceId)
    },
    onSuccess: (nextRuntime) => {
      queryClient.setQueryData(runtimeQueryKey, nextRuntime)
    },
    onError: (error) => {
      handleRuntimeMutationError(error, invalidateRuntime)
    },
    onSettled: () => {
      setPendingChoiceId(null)
    },
  })

  const { mutateAsync: rewindMutation, isPending: isRewinding } = useMutation<
    RoomRuntimeViewModel,
    ApiError,
    string
  >({
    mutationFn: (targetChoiceId: string) =>
      RoomRuntimeService.rewind(roomId, {
        target_choice_id: targetChoiceId,
        expected_revision: runtime?.revision ?? null,
      }),
    onSuccess: (nextRuntime) => {
      queryClient.setQueryData(runtimeQueryKey, nextRuntime)
    },
    onError: (error) => {
      handleRuntimeMutationError(error, invalidateRuntime)
    },
  })

  const { mutateAsync: resetMutation, isPending: isResetting } = useMutation<
    RoomRuntimeViewModel,
    ApiError,
    void
  >({
    mutationFn: () =>
      RoomRuntimeService.reset(roomId, {
        expected_revision: runtime?.revision ?? null,
      }),
    onSuccess: (nextRuntime) => {
      queryClient.setQueryData(runtimeQueryKey, nextRuntime)
    },
    onError: (error) => {
      handleRuntimeMutationError(error, invalidateRuntime)
    },
  })

  const { mutateAsync: startMutation, isPending: isStarting } = useMutation<
    RoomRuntimeViewModel,
    ApiError,
    { userPersonaId: string; storyVersion?: number | null }
  >({
    mutationFn: ({ userPersonaId, storyVersion }) =>
      RoomRuntimeService.startRuntime(roomId, {
        user_persona_id: userPersonaId,
        story_version: storyVersion ?? null,
        expected_revision: runtime?.revision ?? null,
      }),
    onSuccess: (nextRuntime) => {
      queryClient.setQueryData(runtimeQueryKey, nextRuntime)
    },
    onError: (error) => {
      handleRuntimeMutationError(error, invalidateRuntime)
    },
  })

  const advance = useCallback(
    async (choiceId: string) => {
      await advanceMutation(choiceId)
    },
    [advanceMutation],
  )

  const start = useCallback(
    async (params: { userPersonaId: string; storyVersion?: number | null }) => {
      await startMutation(params)
    },
    [startMutation],
  )

  const rewind = useCallback(
    async (targetChoiceId: string) => {
      await rewindMutation(targetChoiceId)
    },
    [rewindMutation],
  )

  const reset = useCallback(async () => {
    await resetMutation()
  }, [resetMutation])

  return {
    runtime,
    isLoading,
    error: error ?? null,
    refetch,
    start,
    advance,
    rewind,
    reset,
    isStarting,
    isAdvancing,
    isRewinding,
    isResetting,
    pendingChoiceId,
  }
}
