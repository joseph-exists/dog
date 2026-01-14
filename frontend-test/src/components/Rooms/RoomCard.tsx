/**
 * RoomCard Component
 *
 * Displays individual room summary with:
 * - Room title
 * - Last activity timestamp (relative)
 * - Hover and click interactions
 */

import { MessageSquare } from "lucide-react"
import { cn } from "@/lib/utils"
import type { RoomViewModel } from "@/services/roomService"

interface RoomCardProps {
  room: RoomViewModel
  onClick: () => void
  isActive?: boolean
}

const formatRelativeTime = (date: Date): string => {
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return "Just now"
  if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? "s" : ""} ago`
  if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? "s" : ""} ago`
  return `${diffDays} day${diffDays > 1 ? "s" : ""} ago`
}

export default function RoomCard({
  room,
  onClick,
  isActive = false,
}: RoomCardProps) {
  return (
    <div
      onClick={onClick}
      className={cn(
        "flex flex-col p-4 border rounded-md cursor-pointer transition-all duration-200",
        isActive
          ? "border-primary bg-primary/10"
          : "border-border bg-transparent hover:bg-accent hover:border-primary",
      )}
    >
      <div className="flex items-center gap-2 mb-2">
        <MessageSquare className="h-4 w-4" />
        <span className="font-bold text-lg">
          {room.title || "Untitled Room"}
        </span>
      </div>

      <span className="text-sm text-muted-foreground">
        Last activity: {formatRelativeTime(room.last_activity)}
      </span>
    </div>
  )
}
