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
  onEdit: () => void
  onPin: () => void
  onUnpin: () => void
  onToggleContext: (active: boolean) => void
  onDelete: () => void
}

export default function MessageActionMenu({
  message,
  onEdit,
  onPin,
  onUnpin,
  onToggleContext,
  onDelete,
}: MessageActionMenuProps) {
  const [isOpen, setIsOpen] = useState(false)

  // Use backend-provided permission flags directly
  const { can_edit, can_delete, can_pin, is_pinned, active_for_context } =
    message

  // Don't render if user has no permissions (toggle context is always allowed for participants)
  if (!can_edit && !can_pin && !can_delete) {
    return null
  }

  return (
    <DropdownMenu open={isOpen} onOpenChange={setIsOpen}>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon-sm"
          className="opacity-60 hover:opacity-100"
          aria-label="Message actions"
        >
          <MoreVertical className="h-4 w-4" />
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
