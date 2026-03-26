// src/components/Page/primitives/BlockContainer.tsx

import { AlertCircle, GripVertical, Loader2, Settings, X } from "lucide-react"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface BlockContainerProps {
  /** Optional title displayed in header */
  title?: string
  /** Optional subtitle displayed under the title */
  subtitle?: string
  /** Optional metadata shown beside title/subtitle */
  metadata?: React.ReactNode
  /** Optional actions for header */
  headerActions?: React.ReactNode
  /** Optional toolbar shown below the title row */
  toolbar?: React.ReactNode
  /** Main content */
  children: React.ReactNode
  /** Optional footer content */
  footer?: React.ReactNode
  /** Additional CSS classes */
  className?: string
  /** Additional CSS classes for header */
  headerClassName?: string
  /** Additional CSS classes for body */
  bodyClassName?: string
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
  /** Compactness preset for spacing */
  density?: "compact" | "default" | "comfortable"
  /** Whether header should stick when body scrolls */
  stickyHeader?: boolean
  /** Whether the block is selected (shows highlight ring) */
  isSelected?: boolean
  /** Click handler for selection */
  onClick?: () => void
  /** Loading state */
  isLoading?: boolean
  /** Empty state content */
  emptyState?: React.ReactNode
  /** Error state content */
  errorState?: React.ReactNode
  /** Whether body should render emptyState instead of children */
  isEmpty?: boolean
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
  subtitle,
  metadata,
  headerActions,
  toolbar,
  children,
  footer,
  className,
  headerClassName,
  bodyClassName,
  scrollable = false,
  editMode = false,
  onRemove,
  onSettings,
  variant = "default",
  density = "default",
  stickyHeader = false,
  isSelected = false,
  onClick,
  isLoading = false,
  emptyState,
  errorState,
  isEmpty = false,
}: BlockContainerProps) {
  const showHeader =
    title || subtitle || metadata || headerActions || toolbar || editMode

  const variantStyles = {
    default: "border border-border bg-card",
    card: "border border-border bg-card shadow-sm",
    transparent: "border-transparent bg-transparent",
  }
  const densityStyles = {
    compact: {
      header: "px-3 py-2",
      body: "p-3",
      footer: "px-3 py-2",
      gap: "gap-1",
    },
    default: {
      header: "px-4 py-3",
      body: "p-4",
      footer: "px-4 py-3",
      gap: "gap-2",
    },
    comfortable: {
      header: "px-5 py-4",
      body: "p-5",
      footer: "px-5 py-4",
      gap: "gap-3",
    },
  }

  const content = (() => {
    if (isLoading) {
      return (
        <div className="flex min-h-[120px] items-center justify-center text-sm text-muted-foreground">
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          Loading block content...
        </div>
      )
    }

    if (errorState) {
      return typeof errorState === "string" ? (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Block error</AlertTitle>
          <AlertDescription>{errorState}</AlertDescription>
        </Alert>
      ) : (
        errorState
      )
    }

    if (isEmpty && emptyState) {
      return emptyState
    }

    return children
  })()

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
        <div
          className={cn(
            "border-b border-border bg-inherit",
            stickyHeader && "sticky top-0 z-10",
            headerClassName,
          )}
        >
          <div
            className={cn(
              "flex items-start justify-between",
              densityStyles[density].header,
            )}
          >
            <div className={cn("min-w-0 flex-1", densityStyles[density].gap)}>
              <div className="flex items-start gap-2">
                {editMode && (
                  <GripVertical className="mt-0.5 h-4 w-4 shrink-0 cursor-grab text-muted-foreground" />
                )}
                <div className="min-w-0 flex-1">
                  {title && (
                    <h3 className="text-sm font-medium text-foreground">
                      {title}
                    </h3>
                  )}
                  {subtitle && (
                    <p className="mt-1 text-xs text-muted-foreground">
                      {subtitle}
                    </p>
                  )}
                  {metadata && (
                    <div className="mt-2 flex flex-wrap items-center gap-2">
                      {metadata}
                    </div>
                  )}
                </div>
              </div>
            </div>
            <div className="ml-3 flex shrink-0 items-center gap-1">
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
          {toolbar && (
            <div className="border-t border-border/70 px-4 py-2">{toolbar}</div>
          )}
        </div>
      )}
      <div
        className={cn(
          "flex-1",
          densityStyles[density].body,
          scrollable && "overflow-y-auto",
          bodyClassName,
        )}
      >
        {content}
      </div>
      {footer && (
        <div
          className={cn(
            "border-t border-border",
            densityStyles[density].footer,
          )}
        >
          {footer}
        </div>
      )}
    </div>
  )
}
