/**
 * UserCardPopover
 *
 * Popover component for displaying user details.
 * Shows avatar with initials, name, email, role, and join date.
 */

import { Clock, Mail, Shield } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { getInitials } from "@/utils"

import { EntityCardPopover } from "./EntityCardPopover"

export interface UserCardData {
  id: string
  name: string
  email?: string
  role?: "owner" | "member" | "viewer"
  joined_at?: string
  is_active?: boolean
}

interface UserCardPopoverProps {
  user: UserCardData
  trigger: React.ReactNode
  align?: "start" | "center" | "end"
}

const roleLabels = {
  owner: "Room Owner",
  member: "Member",
  viewer: "Viewer",
}

function formatJoinedDate(dateString: string): string {
  const date = new Date(dateString)
  return `Joined ${date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  })}`
}

export function UserCardPopover({
  user,
  trigger,
  align = "center",
}: UserCardPopoverProps) {
  const header = (
    <div className="flex items-center gap-3">
      <div className="relative">
        <div className="flex h-12 w-12 items-center justify-center rounded-full border bg-[hsl(var(--user-accent)/0.15)] text-[hsl(var(--user-accent))] border-[hsl(var(--user-accent)/0.3)] text-sm font-medium">
          {getInitials(user.name)}
        </div>
        {user.is_active && (
          <div className="absolute bottom-0 right-0 h-3 w-3 rounded-full border-2 border-background bg-green-500" />
        )}
      </div>
      <div className="flex-1 min-w-0">
        <h4 className="font-semibold truncate">{user.name}</h4>
        {user.is_active && (
          <span className="text-xs text-muted-foreground">Online</span>
        )}
      </div>
    </div>
  )

  const content = (
    <div className="space-y-3">
      {user.email && (
        <div className="flex items-center gap-2 text-sm">
          <Mail className="h-4 w-4 text-muted-foreground" />
          <span className="truncate">{user.email}</span>
        </div>
      )}
      {user.role && (
        <div className="flex items-center gap-2 text-sm">
          <Shield className="h-4 w-4 text-muted-foreground" />
          <Badge variant="secondary">{roleLabels[user.role]}</Badge>
        </div>
      )}
      {user.joined_at && (
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Clock className="h-4 w-4" />
          <span>{formatJoinedDate(user.joined_at)}</span>
        </div>
      )}
    </div>
  )

  return (
    <EntityCardPopover trigger={trigger} header={header} align={align}>
      {content}
    </EntityCardPopover>
  )
}
