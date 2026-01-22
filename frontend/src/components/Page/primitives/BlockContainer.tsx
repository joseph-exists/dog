// src/components/Page/primitives/BlockContainer.tsx

import { GripVertical, Settings, X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface BlockContainerProps {
  /** Optional title displayed in header */
  title?: string
  /** Optional actions for header */
  headerActions?: React.ReactNode
  /** Main content */
  children: React.ReactNode
  /** Additional CSS classes */
  className?: string
  /** Whether content should scroll */
  scrollable?: boolean
  /** Edit mode - shows drag handle and controls */
  editMode?: boolean
  /** Called when remove button clicked in edit mode */
  onRemove?: () => void
  /** Called when settings button clicked in edit mode */
  onSettings?: () => void
  /** Visual variant for the container */
  variant?: "default" | "card" | "transparent"
  /** Whether the block is selected (shows highlight ring) */
  isSelected?: boolean
  /** Click handler for selection */
  onClick?: () => void
}

/**
 * BlockContainer - Wrapper for page blocks
 *
 * Provides consistent styling and edit mode controls for all block types.
 * - Optional header with title and actions
 * - Edit mode shows drag handle, settings, and remove buttons
 * - Scrollable content area
 */
export function BlockContainer({
  title,
  headerActions,
  children,
  className,
  scrollable = false,
  editMode = false,
  onRemove,
  onSettings,
  variant = "default",
  isSelected = false,
  onClick,
}: BlockContainerProps) {
  const showHeader = title || headerActions || editMode

  const variantStyles = {
    default: "border border-border bg-card",
    card: "border border-border bg-card shadow-sm",
    transparent: "border-transparent bg-transparent",
  }

  return (
    <div
      className={cn(
        "flex flex-col rounded-lg",
        variantStyles[variant],
        isSelected && "ring-2 ring-primary",
        onClick && "cursor-pointer",
        className,
      )}
      onClick={onClick}
      role={onClick ? "button" : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={
        onClick
          ? (e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault()
                onClick()
              }
            }
          : undefined
      }
    >
      {showHeader && (
        <div className="flex items-center justify-between px-4 py-3 border-b border-border">
          <div className="flex items-center gap-2">
            {editMode && (
              <GripVertical className="h-4 w-4 text-muted-foreground cursor-grab" />
            )}
            {title && (
              <h3 className="text-sm font-medium text-foreground">{title}</h3>
            )}
          </div>
          <div className="flex items-center gap-1">
            {headerActions}
            {editMode && onSettings && (
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7"
                onClick={(e) => {
                  e.stopPropagation()
                  onSettings?.()
                }}
                aria-label="Block settings"
              >
                <Settings className="h-3.5 w-3.5" />
              </Button>
            )}
            {editMode && onRemove && (
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7 text-muted-foreground hover:text-destructive"
                onClick={(e) => {
                  e.stopPropagation()
                  onRemove?.()
                }}
                aria-label="Remove block"
              >
                <X className="h-3.5 w-3.5" />
              </Button>
            )}
          </div>
        </div>
      )}
      <div className={cn("flex-1", scrollable && "overflow-y-auto")}>
        {children}
      </div>
    </div>
  )
}
