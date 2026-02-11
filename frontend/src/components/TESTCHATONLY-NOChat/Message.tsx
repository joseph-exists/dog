/**
 * Message Component
 *
 * Displays individual message with:
 * - Sender name
 * - Message content
 * - Timestamp (relative format)
 * - Visual distinction for user/agent/own messages
 * - Streaming indicator for real-time agent responses
 * - Status badges (edited, pinned, active/inactive)
 * - Action menu (edit, pin, delete, toggle context)
 */

import { AgentUIRenderer } from "@/components/AgentUI"
import MessageActionMenu from "@/components/Room/RoomMessages/MessageActionMenu"
import { Badge } from "@/components/ui/badge"
import { MessageBadge } from "@/components/ui/message-badge"
import { cn } from "@/lib/utils"
import type { MessageViewModel } from "@/services/roomService"

interface MessageProps {
  message: MessageViewModel
  isStreaming?: boolean
  /** Whether current user is the room owner (grants full permissions) */
  isRoomOwner?: boolean
  onEdit?: () => void
  onPin?: () => void
  onUnpin?: () => void
  onToggleContext?: (active: boolean) => void
  onDelete?: () => void
  /** Handle AG-UI action button clicks within the message. */
  onUiAction?: (action: string, message: MessageViewModel) => void
}

/**
 * Format timestamp as relative time
 */
const formatTimestamp = (date: Date): string => {
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return "Just now"
  if (diffMins < 60) return `${diffMins} min ago`
  if (diffHours < 24) return `${diffHours}h ago`
  return `${diffDays}d ago`
}

export default function Message({
  message,
  isStreaming = false,
  isRoomOwner = false,
  onEdit,
  onPin,
  onUnpin,
  onToggleContext,
  onDelete,
  onUiAction,
}: MessageProps) {
  const isAgent = message.sender_type !== "user"
  const isOwnMessage = message.is_own_message
  const isInternal = message.sender_type === "agent_internal"

  // Use message's built-in properties (from backend)
  const { is_pinned, active_for_context, edited_at } = message

  // Room owners have full permissions on all messages
  // Otherwise, use backend-provided permission flags
  const can_edit = isRoomOwner || message.can_edit
  const can_delete = isRoomOwner || message.can_delete
  const can_pin = isRoomOwner || message.can_pin

  // Show menu if user has any management permissions OR if toggle context is available
  // (toggle context is available to all participants, even without edit/pin/delete permissions)
  const hasAnyPermission = can_edit || can_delete || can_pin
  const hasAnyAction = hasAnyPermission || onToggleContext

  return (
    <div
      className={cn(
        // Base layout
        "relative max-w-[70%] p-3 rounded-md break-words",
        // Alignment based on sender
        isAgent ? "self-start" : "self-end",
        // Background and text colors
        isOwnMessage
          ? "bg-primary text-primary-foreground"
          : isAgent
            ? "bg-muted text-foreground"
            : "bg-primary/90 text-primary-foreground",
        // Streaming animation
        isStreaming && "border-2 border-primary/50 animate-pulse",
      )}
    >
      {/* Action menu - top right corner (if user has any actions available) */}
      {hasAnyAction && !isStreaming && (
        <div className="absolute -top-1 -right-1 z-10">
          <MessageActionMenu
            message={message}
            canEdit={can_edit}
            canDelete={can_delete}
            canPin={can_pin}
            onEdit={onEdit || (() => {})}
            onPin={onPin || (() => {})}
            onUnpin={onUnpin || (() => {})}
            onToggleContext={onToggleContext || (() => {})}
            onDelete={onDelete || (() => {})}
          />
        </div>
      )}

      {/* Sender name */}
      <p className="text-xs opacity-80 mb-1 font-medium flex items-center gap-2">
        <span>{message.sender_name}</span>
        {isInternal && (
          <Badge variant="outline" className="text-[10px]">
            internal
          </Badge>
        )}
        {isStreaming && (
          <span className="ml-2 text-xs opacity-60">typing...</span>
        )}
      </p>

      {/* Status badges */}
      {!isStreaming && (edited_at || is_pinned) && (
        <div className="flex gap-2 mb-2 flex-wrap">
          {edited_at && <MessageBadge variant="edited" timestamp={edited_at} />}
          {is_pinned && <MessageBadge variant="pinned" />}
          <MessageBadge variant={active_for_context ? "active" : "inactive"} />
        </div>
      )}

      {/* Message content */}
      <p className="whitespace-pre-wrap">{message.content}</p>

      {/* Agent UI components */}
      {message.ui_components && message.ui_components.length > 0 && (
        <div className="mt-3 space-y-2">
          {message.ui_components.map((component, index) => (
            <AgentUIRenderer
              key={component.id || `${component.type}-${index}`}
              component={component}
              onAction={(action) => onUiAction?.(action, message)}
            />
          ))}
        </div>
      )}

      {/* Timestamp */}
      <p className="text-xs opacity-60 mt-1">
        {isStreaming ? "streaming..." : formatTimestamp(message.created_at)}
      </p>
    </div>
  )
}
