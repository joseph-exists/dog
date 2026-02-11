/**
 * MessageActionMenu Component
 *
 * Dropdown menu with message management actions:
 * - Edit (author or owner for user messages, owner for agent messages)
 * - Pin/Unpin (owner only)
 * - Toggle Context (any participant)
 * - Delete (owner only)
 *
 * Permissions are provided by the backend on each message (can_edit, can_delete, can_pin).
 * This eliminates client-side permission computation and ensures single source of truth.
 */

import { Eye, EyeOff, MoreVertical, Pencil, Pin, Trash2 } from "lucide-react"
import { useState } from "react"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import type { MessageViewModel } from "@/services/roomService"

interface MessageActionMenuProps {
  message: MessageViewModel
  /** Override permission flags (e.g., for room owners) */
  canEdit?: boolean
  canDelete?: boolean
  canPin?: boolean
  onEdit: () => void
  onPin: () => void
  onUnpin: () => void
  onToggleContext: (active: boolean) => void
  onDelete: () => void
}

export default function MessageActionMenu({
  message,
  canEdit,
  canDelete,
  canPin,
  onEdit,
  onPin,
  onUnpin,
  onToggleContext,
  onDelete,
}: MessageActionMenuProps) {
  const [isOpen, setIsOpen] = useState(false)

  // Use override props if provided, otherwise fall back to message's permission flags
  const can_edit = canEdit ?? message.can_edit
  const can_delete = canDelete ?? message.can_delete
  const can_pin = canPin ?? message.can_pin
  const { is_pinned, active_for_context } = message

  // Toggle context is always available to participants, so don't early return
  // The menu will always show at least the toggle context option

  return (
    <DropdownMenu open={isOpen} onOpenChange={setIsOpen}>
      <DropdownMenuTrigger asChild>
        <Button
          variant="outline"
          size="icon-sm"
          className="h-6 w-6 bg-background/80 backdrop-blur-sm border-border/50 hover:bg-background hover:border-border"
          aria-label="Message actions"
        >
          <MoreVertical className="h-3 w-3" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        {/* Edit action - backend determines permission */}
        {can_edit && (
          <DropdownMenuItem onClick={onEdit}>
            <Pencil className="h-4 w-4" />
            Edit
          </DropdownMenuItem>
        )}

        {/* Pin/Unpin - backend determines permission */}
        {can_pin && (
          <DropdownMenuItem onClick={is_pinned ? onUnpin : onPin}>
            <Pin className="h-4 w-4" />
            {is_pinned ? "Unpin" : "Pin"}
          </DropdownMenuItem>
        )}

        {/* Toggle context - any participant can toggle (backend validates membership) */}
        {(can_edit || can_pin) && <DropdownMenuSeparator />}
        <DropdownMenuItem onClick={() => onToggleContext(!active_for_context)}>
          {active_for_context ? (
            <EyeOff className="h-4 w-4" />
          ) : (
            <Eye className="h-4 w-4" />
          )}
          {active_for_context ? "Remove from Context" : "Add to Context"}
        </DropdownMenuItem>

        {/* Delete - backend determines permission */}
        {can_delete && (
          <>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={onDelete} variant="destructive">
              <Trash2 className="h-4 w-4" />
              Delete
            </DropdownMenuItem>
          </>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
