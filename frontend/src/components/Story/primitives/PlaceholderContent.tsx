/**
 * PlaceholderContent Primitive
 *
 * Consistent "coming soon" or empty state for panels.
 * Used for placeholder panels and empty states.
 *
 * @example
 * ```tsx
 * <PlaceholderContent
 *   icon={Paintbrush}
 *   title="Canvas"
 *   description="Interactive canvas coming soon."
 * />
 * ```
 */

import type { LucideIcon } from "lucide-react"
import type * as React from "react"
import { cn } from "@/lib/utils"

interface PlaceholderContentProps {
  /** Icon to display */
  icon: LucideIcon
  /** Title text */
  title: string
  /** Description text */
  description?: string
  /** Optional action button */
  action?: React.ReactNode
  /** Additional className */
  className?: string
}

export function PlaceholderContent({
  icon: Icon,
  title,
  description,
  action,
  className,
}: PlaceholderContentProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center h-full gap-4 p-6 text-center",
        className,
      )}
    >
      {/* Icon in muted background circle */}
      <div className="flex items-center justify-center w-12 h-12 rounded-full bg-muted">
        <Icon className="w-6 h-6 text-muted-foreground" />
      </div>

      {/* Text content */}
      <div className="space-y-1">
        <h3 className="text-sm font-medium text-foreground">{title}</h3>
        {description && (
          <p className="text-sm text-muted-foreground">{description}</p>
        )}
      </div>

      {/* Optional action */}
      {action && <div className="mt-2">{action}</div>}
    </div>
  )
}
