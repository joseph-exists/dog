// src/components/Page/blocks/ActivityFeedBlock.tsx
import { Activity, MessageSquare, Settings, UserPlus } from "lucide-react"

import { BlockContainer } from "../primitives"

export interface ActivityItem {
  id: string
  type: "message" | "joined" | "updated" | "other"
  description: string
  timestamp: Date
}

export interface ActivityFeedBlockConfig {
  maxItems: number
}

export interface ActivityFeedContent {
  activities: ActivityItem[]
}

export interface ActivityFeedBlockProps {
  config: ActivityFeedBlockConfig
  content?: ActivityFeedContent
  className?: string
}

const activityIcons = {
  message: MessageSquare,
  joined: UserPlus,
  updated: Settings,
  other: Activity,
}

/**
 * Format a date as relative time (e.g., "2 hours ago", "3 days ago")
 */
function formatRelativeTime(date: Date): string {
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffSeconds = Math.floor(diffMs / 1000)
  const diffMinutes = Math.floor(diffSeconds / 60)
  const diffHours = Math.floor(diffMinutes / 60)
  const diffDays = Math.floor(diffHours / 24)
  const diffWeeks = Math.floor(diffDays / 7)
  const diffMonths = Math.floor(diffDays / 30)
  const diffYears = Math.floor(diffDays / 365)

  if (diffSeconds < 60) {
    return "just now"
  }
  if (diffMinutes < 60) {
    return `${diffMinutes} minute${diffMinutes === 1 ? "" : "s"} ago`
  }
  if (diffHours < 24) {
    return `${diffHours} hour${diffHours === 1 ? "" : "s"} ago`
  }
  if (diffDays < 7) {
    return `${diffDays} day${diffDays === 1 ? "" : "s"} ago`
  }
  if (diffWeeks < 4) {
    return `${diffWeeks} week${diffWeeks === 1 ? "" : "s"} ago`
  }
  if (diffMonths < 12) {
    return `${diffMonths} month${diffMonths === 1 ? "" : "s"} ago`
  }
  return `${diffYears} year${diffYears === 1 ? "" : "s"} ago`
}

/**
 * ActivityFeedBlock - Displays a timeline of recent activities
 *
 * Shows a vertical timeline with icons, descriptions, and relative timestamps.
 * Activities are limited to config.maxItems.
 * Returns null if no activities are provided.
 * View-only block - no edit functionality.
 */
export function ActivityFeedBlock({
  config,
  content,
  className,
}: ActivityFeedBlockProps) {
  const activities = content?.activities || []

  if (activities.length === 0) {
    return null
  }

  const visibleActivities = activities.slice(0, config.maxItems)

  return (
    <BlockContainer title="Activity" scrollable className={className}>
      <div className="relative p-4">
        {/* Vertical timeline line */}
        <div className="absolute left-7 top-4 bottom-4 w-px bg-border" />

        <div className="space-y-4">
          {visibleActivities.map((activity) => {
            const Icon = activityIcons[activity.type]

            return (
              <div
                key={activity.id}
                className="relative flex items-start gap-3"
              >
                {/* Icon in circle */}
                <div className="relative z-10 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-muted border border-border">
                  <Icon className="h-3 w-3 text-muted-foreground" />
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0 pt-0.5">
                  <p className="text-sm text-foreground">
                    {activity.description}
                  </p>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    {formatRelativeTime(activity.timestamp)}
                  </p>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </BlockContainer>
  )
}
