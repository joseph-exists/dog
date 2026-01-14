/**
 * useRoomPermissions Hook - Room-Level Authorization
 *
 * Purpose: Centralized permission checking for room operations.
 * Computes authorization flags based on current user and room ownership.
 *
 * Permission Rules:
 * - Edit message: Author OR owner (user messages), owner only (agent messages)
 * - Delete message: Owner only
 * - Pin message: Owner only
 * - Toggle context: Any participant (checked elsewhere via room membership)
 *
 * Phase 5 - Message Management Features
 */

import type { RoomViewModel } from "@/services/roomService"
import type { MessageViewModel } from "@/services/roomService"
import { useMemo } from "react"
import useAuth from "./useAuth"

export interface RoomPermissions {
  /** True if current user is the room owner */
  isOwner: boolean

  /** Check if user can edit a specific message */
  canEditMessage: (message: MessageViewModel) => boolean

  /** Check if user can delete messages (owner only) */
  canDeleteMessage: () => boolean

  /** Check if user can pin messages (owner only) */
  canPinMessage: () => boolean

  /** Check if user can toggle message context (any participant) */
  canToggleContext: () => boolean
}

/**
 * Hook for computing room-level permissions
 *
 * Memoizes permission checks based on user and room ownership.
 * Returns permission flags and checker functions.
 *
 * @param room - Current room data (null/undefined safe)
 * @returns Permission interface with flags and checker functions
 *
 * @example
 * ```tsx
 * const permissions = useRoomPermissions(room)
 *
 * if (permissions.isOwner) {
 *   // Show owner-only UI
 * }
 *
 * if (permissions.canEditMessage(message)) {
 *   // Show edit button
 * }
 * ```
 */
export function useRoomPermissions(
  room: RoomViewModel | null | undefined,
): RoomPermissions {
  const { user } = useAuth()

  return useMemo(() => {
    // Check if current user is room owner
    const isOwner = room?.creator_id === user?.id

    return {
      isOwner,

      /**
       * Can edit message rules:
       * - User messages: Author OR room owner can edit
       * - Agent messages: Only room owner can edit
       */
      canEditMessage: (message: MessageViewModel): boolean => {
        if (!user) return false

        if (message.sender_type === "agent") {
          return isOwner
        }

        return message.sender_id === user.id || isOwner
      },

      /**
       * Can delete message:
       * - Only room owner can delete any message
       */
      canDeleteMessage: (): boolean => {
        return isOwner
      },

      /**
       * Can pin message:
       * - Only room owner can pin messages
       */
      canPinMessage: (): boolean => {
        return isOwner
      },

      /**
       * Can toggle context:
       * - Any authenticated participant can toggle
       * - Room membership is validated on backend
       */
      canToggleContext: (): boolean => {
        return Boolean(user)
      },
    }
  }, [room?.creator_id, user])
}
