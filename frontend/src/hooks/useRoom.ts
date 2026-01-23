/**
 * useRoom Hook - Aggregate Room State Management
 *
 * Purpose: Provide comprehensive room state by aggregating room metadata,
 * messages, and participants. This is a higher-level hook that coordinates
 * multiple data sources.
 *
 * Features:
 * - Aggregates room, messages, and participants
 * - Provides derived state (user role, active agents/users)
 * - Delegates to useRoomMessages for message operations
 * - Manages participant operations
 * - Polling coordination for all data sources
 *
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useCallback, useMemo } from "react"
import type { ApiError } from "@/client"
import { showErrorToast } from "@/hooks/useCustomToast"
import type {
  MessageViewModel,
  ParticipantViewModel,
  RoomViewModel,
} from "@/services/roomService"
import { RoomService } from "@/services/roomService"
import { handleError } from "@/utils"
import useAuth from "./useAuth"
import { useRoomMessages } from "./useRoomMessages"

export interface UseRoomOptions {
  autoScrollToBottom?: boolean
  onDeleteSuccess?: () => void // callback when room is deleted no crash-crash
  /** Include internal agent-to-agent messages in message queries (debug only). */
  includeInternalMessages?: boolean
}

export interface UseRoomResult {
  // Room State
  room: RoomViewModel | undefined
  messages: MessageViewModel[]
  participants: ParticipantViewModel[]

  // Loading States
  isLoadingRoom: boolean
  isLoadingMessages: boolean
  isLoadingParticipants: boolean

  // Error States
  roomError: Error | null
  messagesError: Error | null
  participantsError: Error | null

  // Actions
  sendMessage: (content: string) => Promise<void>
  addParticipant: (
    participantId: string,
    type: "user" | "agent",
  ) => Promise<void>
  removeParticipant: (participantId: string) => Promise<void>
  loadMoreMessages: () => Promise<void>
  updateRoom: (data: { title?: string | null }) => Promise<void>
  deleteRoom: () => Promise<void>

  isUpdatingRoom: boolean
  isDeletingRoom: boolean
  // Pagination
  hasMoreMessages: boolean
  isLoadingMoreMessages: boolean

  // Message Sending
  isSending: boolean

  // Phase 5: Message Management Actions
  editMessage: (messageId: string, content: string) => Promise<void>
  isEditing: boolean
  pinMessage: (messageId: string) => Promise<void>
  isPinning: boolean
  unpinMessage: (messageId: string) => Promise<void>
  isUnpinning: boolean
  toggleContext: (messageId: string, active: boolean) => Promise<void>
  isTogglingContext: boolean
  deleteMessage: (messageId: string) => Promise<void>
  isDeleting: boolean

  // Derived State
  currentUserRole: "owner" | "member" | null
  activeAgents: ParticipantViewModel[]
  activeUsers: ParticipantViewModel[]
}

/**
 * Hook for comprehensive room state management
 *
 * Aggregates room metadata, messages, and participants into a single interface.
 * Provides all necessary operations for room interaction.
 *
 * @param roomId - Room UUID
 * @param options - Configuration options
 * @returns Comprehensive room state and operations
 *
 * @example
 * ```tsx
 * const {
 *   room,
 *   messages,
 *   participants,
 *   sendMessage,
 *   addParticipant,
 *   currentUserRole,
 *   activeAgents,
 *   isLoadingRoom
 * } = useRoom(roomId, { enablePolling: true });
 *
 * // Send a message
 * await sendMessage("Hello, everyone!");
 *
 * // Add an agent to the room
 * if (currentUserRole === 'owner') {
 *   await addParticipant('StoryAdvisor', 'agent');
 * }
 * ```
 */
export function useRoom(
  roomId: string,
  options?: UseRoomOptions,
): UseRoomResult {
  const queryClient = useQueryClient()
  const { user } = useAuth()

  // Options with defaults
  const includeInternalMessages = options?.includeInternalMessages ?? false

  // Query keys
  const roomQueryKey = ["rooms", roomId]
  const participantsQueryKey = ["rooms", roomId, "participants"]

  // ==========================================================================
  // Data Queries
  // ==========================================================================

  // Fetch room metadata
  const {
    data: room,
    isLoading: isLoadingRoom,
    error: roomError,
  } = useQuery({
    queryKey: roomQueryKey,
    queryFn: () => RoomService.getRoom(roomId),
    refetchInterval: false,
    refetchIntervalInBackground: false,
  })

  // Fetch participants with polling
  const {
    data: participants = [],
    isLoading: isLoadingParticipants,
    error: participantsError,
  } = useQuery({
    queryKey: participantsQueryKey,
    queryFn: () => RoomService.getParticipants(roomId),
    refetchInterval: false,
    refetchIntervalInBackground: false,
    placeholderData: (previousData) => previousData,
  })

  // Delegate message operations to useRoomMessages
  const {
    messages,
    isLoading: isLoadingMessages,
    error: messagesError,
    hasMore: hasMoreMessages,
    loadMore: loadMoreMessages,
    isLoadingMore: isLoadingMoreMessages,
    sendMessage,
    isSending,
    // Phase 5: Message management
    editMessage,
    isEditing,
    pinMessage,
    isPinning,
    unpinMessage,
    isUnpinning,
    toggleContext,
    isTogglingContext,
    deleteMessage: deleteMessageFn,
    isDeleting,
  } = useRoomMessages(roomId, {
    includeInternalMessages,
  })

  // ==========================================================================
  // Participant Mutations
  // ==========================================================================

  // Add participant mutation
  const addParticipantMutation = useMutation({
    mutationFn: async ({
      participantId,
      type,
    }: {
      participantId: string
      type: "user" | "agent"
    }) => {
      return await RoomService.addParticipant(roomId, {
        participant_id: participantId,
        participant_type: type,
        role: "member",
      })
    },
    onSuccess: () => {
      // Invalidate participants to refetch
      queryClient.invalidateQueries({ queryKey: participantsQueryKey })
    },
    onError: (err: ApiError) => {
      handleError.call(showErrorToast, err as ApiError)
    },
  })

  // Remove participant mutation
  const removeParticipantMutation = useMutation({
    mutationFn: async (participantId: string) => {
      return await RoomService.removeParticipant(roomId, participantId)
    },
    onSuccess: () => {
      // Invalidate participants to refetch
      queryClient.invalidateQueries({ queryKey: participantsQueryKey })
    },
    onError: (err: ApiError) => {
      handleError.call(showErrorToast, err as ApiError)
    },
  })

  // Update room mutation
  const updateRoomMutation = useMutation({
    mutationFn: async (data: { title?: string | null }) => {
      return await RoomService.updateRoom(roomId, data)
    },
    onSuccess: () => {
      // Invalidate room metadata to refetch
      queryClient.invalidateQueries({ queryKey: roomQueryKey })
    },
    onError: (err: ApiError) => {
      handleError.call(showErrorToast, err as ApiError)
    },
  })
  const deleteRoomMutation = useMutation({
    mutationFn: async () => {
      // Call service method (will throw error if backend not ready)
      await RoomService.deleteRoom(roomId)
    },
    onSuccess: () => {
      // Invalidate queries
      queryClient.invalidateQueries({ queryKey: ["rooms"] })
      queryClient.invalidateQueries({ queryKey: roomQueryKey })

      // Call optional callback (component provides navigation)
      options?.onDeleteSuccess?.()
    },
    onError: (err: ApiError) => {
      handleError.call(showErrorToast, err as ApiError)
    },
  })

  // ==========================================================================
  // Action Wrappers
  // ==========================================================================

  const addParticipant = useCallback(
    async (participantId: string, type: "user" | "agent") => {
      await addParticipantMutation.mutateAsync({ participantId, type })
    },
    [addParticipantMutation],
  )

  const removeParticipant = useCallback(
    async (participantId: string) => {
      await removeParticipantMutation.mutateAsync(participantId)
    },
    [removeParticipantMutation],
  )

  const updateRoom = useCallback(
    async (data: { title?: string | null }) => {
      await updateRoomMutation.mutateAsync(data)
    },
    [updateRoomMutation],
  )

  const deleteRoom = useCallback(async () => {
    await deleteRoomMutation.mutateAsync()
  }, [deleteRoomMutation])

  // ==========================================================================
  // Derived State
  // ==========================================================================

  // Current user's role in the room
  const currentUserRole = useMemo(() => {
    if (!user?.id || !participants.length) return null

    const userParticipant = participants.find(
      (p) => p.participant_type === "user" && p.participant_id === user.id,
    )

    return userParticipant?.role ?? null
  }, [user?.id, participants])

  // Active agents in the room
  const activeAgents = useMemo(() => {
    return participants.filter(
      (p) => p.participant_type === "agent" && p.is_active,
    )
  }, [participants])

  // Active users in the room
  const activeUsers = useMemo(() => {
    return participants.filter(
      (p) => p.participant_type === "user" && p.is_active,
    )
  }, [participants])

  // ==========================================================================
  // Return Value
  // ==========================================================================

  return {
    // Room State
    room,
    messages,
    participants,

    // Loading States
    isLoadingRoom,
    isLoadingMessages,
    isLoadingParticipants,

    // Error States
    roomError: roomError as Error | null,
    messagesError,
    participantsError: participantsError as Error | null,

    // Actions
    sendMessage,
    addParticipant,
    removeParticipant,
    loadMoreMessages,

    // Pagination
    hasMoreMessages,
    isLoadingMoreMessages,

    // Message Sending
    isSending,

    // Phase 5: Message Management (from useRoomMessages)
    editMessage,
    isEditing,
    pinMessage,
    isPinning,
    unpinMessage,
    isUnpinning,
    toggleContext,
    isTogglingContext,
    deleteMessage: deleteMessageFn,
    isDeleting,

    // Derived State
    currentUserRole,
    activeAgents,
    activeUsers,

    // Room Management
    updateRoom,
    deleteRoom,
    isUpdatingRoom: updateRoomMutation.isPending,
    isDeletingRoom: deleteRoomMutation.isPending,
  }
}
