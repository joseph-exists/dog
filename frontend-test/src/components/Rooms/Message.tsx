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

import { MessageBadge } from "@/components/ui/message-badge"
import { cn } from "@/lib/utils"
import type { MessageViewModel } from "@/services/roomService"
import MessageActionMenu from "./MessageActionMenu"

interface MessageProps {
  message: MessageViewModel
  isStreaming?: boolean
  onEdit?: () => void
  onPin?: () => void
  onUnpin?: () => void
  onToggleContext?: (active: boolean) => void
  onDelete?: () => void
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
  onEdit,
  onPin,
  onUnpin,
  onToggleContext,
  onDelete,
}: MessageProps) {
  const isAgent = message.sender_type === "agent"
  const isOwnMessage = message.is_own_message

  // Use message's built-in properties (from backend)
  const {
    is_pinned,
    active_for_context,
    edited_at,
    can_edit,
    can_delete,
    can_pin,
  } = message
  const hasAnyPermission = can_edit || can_delete || can_pin

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
      {/* Action menu - top right corner (only if user has any permissions) */}
      {hasAnyPermission && onEdit && !isStreaming && (
        <div className="absolute top-2 right-2">
          <MessageActionMenu
            message={message}
            onEdit={onEdit}
            onPin={onPin || (() => {})}
            onUnpin={onUnpin || (() => {})}
            onToggleContext={onToggleContext || (() => {})}
            onDelete={onDelete || (() => {})}
          />
        </div>
      )}

      {/* Sender name */}
      <p className="text-xs opacity-80 mb-1 font-medium">
        {message.sender_name}
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

      {/* Timestamp */}
      <p className="text-xs opacity-60 mt-1">
        {isStreaming ? "streaming..." : formatTimestamp(message.created_at)}
      </p>
    </div>
  )
}
