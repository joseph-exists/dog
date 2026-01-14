/**
 * MessageBadge Component - UI Primitive
 *
 * Reusable status badge for message states:
 * - edited: Shows message was edited
 * - pinned: Shows message is pinned
 * - active: Shows message is active for context
 * - inactive: Shows message is not in context
 */

import { Pencil, Pin, CheckCircle, Circle } from "lucide-react"
import { cn } from "@/lib/utils"

export type MessageBadgeVariant = "edited" | "pinned" | "active" | "inactive"

export interface MessageBadgeProps {
  variant: MessageBadgeVariant
  timestamp?: string
  className?: string
}

const badgeConfig: Record<
  MessageBadgeVariant,
  { icon: typeof Pencil; colorClass: string; label: string }
> = {
  edited: {
    icon: Pencil,
    colorClass: "bg-muted text-muted-foreground",
    label: "Edited",
  },
  pinned: {
    icon: Pin,
    colorClass: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400",
    label: "Pinned",
  },
  active: {
    icon: CheckCircle,
    colorClass: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
    label: "Active for Context",
  },
  inactive: {
    icon: Circle,
    colorClass: "bg-muted text-muted-foreground",
    label: "Inactive",
  },
}

export function MessageBadge({
  variant,
  timestamp,
  className,
}: MessageBadgeProps) {
  const config = badgeConfig[variant]
  const Icon = config.icon
  const title = timestamp ? `${config.label} - ${timestamp}` : config.label

  return (
    <span
      title={title}
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium",
        config.colorClass,
        className
      )}
    >
      <Icon className="h-3 w-3" />
      {config.label}
    </span>
  )
}
