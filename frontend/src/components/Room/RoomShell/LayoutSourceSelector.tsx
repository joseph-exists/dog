/**
 * LayoutSourceSelector Component
 *
 * Card-style selector for choosing layout source (room default, user default, custom).
 * Highlights the active source and shows clear descriptions.
 */

import { Link } from "@tanstack/react-router"
import { ExternalLink, Globe, Pencil, User } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

// ============================================================================
// Types
// ============================================================================

export type LayoutSource =
  | "room_override"
  | "room_defaults"
  | "user_defaults"
  | "system_defaults"
  | "custom"

export interface LayoutSourceSelectorProps {
  /** Current source of the layout */
  currentSource: LayoutSource
  /** Called when source selection changes */
  onSourceChange: (source: LayoutSource) => void
  /** Whether the current user is the room owner */
  isRoomOwner: boolean
  /** Whether room has custom defaults set */
  hasRoomDefaults: boolean
  /** The original source when the dialog was opened (for showing "Active" badge) */
  savedSource?: LayoutSource
  /** Additional className */
  className?: string
}

// ============================================================================
// Component
// ============================================================================

export function LayoutSourceSelector({
  currentSource,
  onSourceChange,
  hasRoomDefaults,
  savedSource,
  className,
}: LayoutSourceSelectorProps) {
  // Normalize source for comparison
  const selectedValue =
    currentSource === "room_override" ? "custom" : currentSource
  const activeValue = savedSource
    ? savedSource === "room_override"
      ? "custom"
      : savedSource
    : selectedValue

  const options: {
    value: string
    icon: typeof User
    label: string
    description: string
    link?: { to: string; label: string }
    show: boolean
  }[] = [
    {
      value: "room_defaults",
      icon: Globe,
      label: "Room default",
      description: "Layout set by the room owner for all participants",
      show: hasRoomDefaults,
    },
    {
      value: "user_defaults",
      icon: User,
      label: "My default",
      description: "Your personal default layout for all rooms",
      link: { to: "/settings", label: "Edit defaults" },
      show: true,
    },
    {
      value: "custom",
      icon: Pencil,
      label: "Custom for this room",
      description: "A unique layout just for this room",
      show: true,
    },
  ]

  return (
    <div className={cn("space-y-2", className)}>
      <h4 className="text-sm font-medium">Layout Source</h4>
      <div className="grid gap-2">
        {options
          .filter((o) => o.show)
          .map((option) => {
            const isSelected = selectedValue === option.value
            const isActive = activeValue === option.value && !isSelected
            const Icon = option.icon

            return (
              <button
                key={option.value}
                type="button"
                onClick={() => onSourceChange(option.value as LayoutSource)}
                className={cn(
                  "flex items-start gap-3 rounded-lg border p-3 text-left transition-colors",
                  isSelected
                    ? "border-primary bg-primary/5 ring-1 ring-primary/20"
                    : "border-border hover:border-primary/40 hover:bg-accent/50",
                )}
              >
                <div
                  className={cn(
                    "mt-0.5 rounded-md p-1.5",
                    isSelected
                      ? "bg-primary/10 text-primary"
                      : "bg-muted text-muted-foreground",
                  )}
                >
                  <Icon className="h-4 w-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span
                      className={cn(
                        "text-sm font-medium",
                        isSelected && "text-primary",
                      )}
                    >
                      {option.label}
                    </span>
                    {isSelected && (
                      <Badge
                        variant="secondary"
                        className="text-[10px] px-1.5 py-0 h-4 bg-primary/10 text-primary border-0"
                      >
                        Selected
                      </Badge>
                    )}
                    {isActive && (
                      <Badge
                        variant="outline"
                        className="text-[10px] px-1.5 py-0 h-4"
                      >
                        Saved
                      </Badge>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    {option.description}
                  </p>
                </div>
                {option.link && (
                  <Link
                    to={option.link.to}
                    //onClick={(e) => e.stopPropagation()}
                    onClick={(e: React.MouseEvent<HTMLAnchorElement>) => e.stopPropagation()}
                    className="text-xs text-primary hover:underline flex items-center gap-1 mt-1 shrink-0"
                  >
                    {option.link.label} <ExternalLink className="h-3 w-3" />
                  </Link>
                )}
              </button>
            )
          })}
      </div>
    </div>
  )
}
