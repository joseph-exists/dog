/**
 * MessageActionMenu Component
 *
 * Dropdown menu with message management actions:
 * - Edit (author or owner for user messages, owner for agent messages)
 * - Pin/Unpin (owner only)
 * - Toggle Context (any participant)
 * - Delete (owner only)
 *
 * Displays only actions the current user is permitted to perform.
 *
 * Phase 5 - Message Management Features
 */

import { useState } from "react"
import {
  MenuRoot,
  MenuTrigger,
  MenuContent,
  MenuItem,
  MenuSeparator,
} from "@chakra-ui/react"
import { IconButton } from "@chakra-ui/react"
import {
  FaEdit,
  FaThumbtack,
  FaTrash,
  FaEye,
  FaEyeSlash,
  FaEllipsisV,
} from "react-icons/fa"
import type { MessageViewModel, RoomViewModel } from "@/services/roomService"
import { useRoomPermissions } from "@/hooks/useRoomPermissions"

interface MessageActionMenuProps {
  message: MessageViewModel
  room: RoomViewModel
  onEdit: () => void
  onPin: () => void
  onUnpin: () => void
  onToggleContext: (active: boolean) => void
  onDelete: () => void
  isPinned: boolean
  isActiveForContext: boolean
}

/**
 * MessageActionMenu - Context menu for message operations
 *
 * Shows only permitted actions based on user permissions.
 * Uses IconButton trigger with vertical ellipsis icon.
 *
 * @param message - Message to perform actions on
 * @param room - Current room (for permission checks)
 * @param onEdit - Callback when edit is clicked
 * @param onPin - Callback when pin is clicked
 * @param onUnpin - Callback when unpin is clicked
 * @param onToggleContext - Callback when toggle context is clicked
 * @param onDelete - Callback when delete is clicked
 * @param isPinned - Whether message is currently pinned
 * @param isActiveForContext - Whether message is active for context
 *
 * @example
 * ```tsx
 * <MessageActionMenu
 *   message={message}
 *   room={room}
 *   onEdit={() => setEditingMessage(message)}
 *   onPin={() => pinMutation.mutate(message.message_id)}
 *   onUnpin={() => unpinMutation.mutate(message.message_id)}
 *   onToggleContext={(active) => toggleMutation.mutate({ messageId: message.message_id, active })}
 *   onDelete={() => deleteMutation.mutate(message.message_id)}
 *   isPinned={message.is_pinned}
 *   isActiveForContext={message.active_for_context}
 * />
 * ```
 */
const MessageActionMenu = ({
  message,
  room,
  onEdit,
  onPin,
  onUnpin,
  onToggleContext,
  onDelete,
  isPinned,
  isActiveForContext,
}: MessageActionMenuProps) => {
  const permissions = useRoomPermissions(room)
  const [isOpen, setIsOpen] = useState(false)

  // Don't render if user has no permissions
  if (
    !permissions.canEditMessage(message) &&
    !permissions.canPinMessage() &&
    !permissions.canToggleContext() &&
    !permissions.canDeleteMessage()
  ) {
    return null
  }

  return (
    <MenuRoot open={isOpen} onOpenChange={(e) => setIsOpen(e.open)}>
      <MenuTrigger asChild>
        <IconButton
          aria-label="Message actions"
          variant="ghost"
          size="xs"
          opacity={0.6}
          _hover={{ opacity: 1 }}
        >
          <FaEllipsisV />
        </IconButton>
      </MenuTrigger>
      <MenuContent>
        {/* Edit action - author or owner for user messages, owner for agent */}
        {permissions.canEditMessage(message) && (
          <MenuItem value="edit" onClick={onEdit}>
            <FaEdit />
            Edit
          </MenuItem>
        )}

        {/* Pin/Unpin - owner only */}
        {permissions.canPinMessage() && (
          <MenuItem
            value={isPinned ? "unpin" : "pin"}
            onClick={isPinned ? onUnpin : onPin}
          >
            <FaThumbtack />
            {isPinned ? "Unpin" : "Pin"}
          </MenuItem>
        )}

        {/* Toggle context - any participant */}
        {permissions.canToggleContext() && (
          <>
            {(permissions.canEditMessage(message) || permissions.canPinMessage()) && (
              <MenuSeparator />
            )}
            <MenuItem
              value="toggle-context"
              onClick={() => onToggleContext(!isActiveForContext)}
            >
              {isActiveForContext ? <FaEyeSlash /> : <FaEye />}
              {isActiveForContext
                ? "Remove from Context"
                : "Add to Context"}
            </MenuItem>
          </>
        )}

        {/* Delete - owner only */}
        {permissions.canDeleteMessage() && (
          <>
            <MenuSeparator />
            <MenuItem
              value="delete"
              onClick={onDelete}
              color="red.600"
              _hover={{ bg: "red.50" }}
            >
              <FaTrash />
              Delete
            </MenuItem>
          </>
        )}
      </MenuContent>
    </MenuRoot>
  )
}

export default MessageActionMenu
