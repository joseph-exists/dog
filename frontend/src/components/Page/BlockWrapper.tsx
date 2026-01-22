// src/components/Page/BlockWrapper.tsx

import { ArrowDown, ArrowUp, Eye, EyeOff, Trash2 } from "lucide-react"
import { useState } from "react"

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { Button } from "@/components/ui/button"
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { cn } from "@/lib/utils"

interface BlockWrapperProps {
  blockId: string
  isEditing: boolean
  isSelected: boolean
  isVisible?: boolean
  isFirst?: boolean
  isLast?: boolean
  onSelect: (blockId: string) => void
  onMoveUp?: (blockId: string) => void
  onMoveDown?: (blockId: string) => void
  onToggleVisibility?: (blockId: string) => void
  onDelete?: (blockId: string) => void
  children: React.ReactNode
  className?: string
}

/**
 * BlockWrapper - Wraps blocks to add click-to-select and toolbar in edit mode
 *
 * In view mode: transparent pass-through (no visual changes)
 * In edit mode: shows hover toolbar with reorder/visibility/delete actions
 * When selected: shows highlight ring
 */
export function BlockWrapper({
  blockId,
  isEditing,
  isSelected,
  isVisible = true,
  isFirst = false,
  isLast = false,
  onSelect,
  onMoveUp,
  onMoveDown,
  onToggleVisibility,
  onDelete,
  children,
  className,
}: BlockWrapperProps) {
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)

  const handleClick = (e: React.MouseEvent) => {
    // Don't select when clicking toolbar buttons
    if ((e.target as HTMLElement).closest("[data-toolbar]")) {
      return
    }
    if (isEditing) {
      onSelect(blockId)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault()
      if (isEditing) {
        onSelect(blockId)
      }
    }
  }

  // View mode: minimal wrapper, hide if not visible
  if (!isEditing) {
    if (!isVisible) return null
    return <div className={className}>{children}</div>
  }

  // Edit mode: interactive wrapper with toolbar
  return (
    <div
      className={cn(
        "group relative rounded-lg transition-all",
        "cursor-pointer",
        // Hover effect in edit mode
        "hover:ring-2 hover:ring-muted-foreground/20",
        // Selected state
        isSelected && "ring-2 ring-primary",
        // Hidden block styling
        !isVisible && "opacity-50",
        className,
      )}
      onClick={handleClick}
      role="button"
      tabIndex={0}
      onKeyDown={handleKeyDown}
      aria-pressed={isSelected}
      aria-label="Select block for editing"
    >
      {/* Hover Toolbar */}
      <div
        data-toolbar
        className={cn(
          "absolute -top-3 right-2 z-10",
          "flex items-center gap-1 p-1 rounded-md",
          "bg-background border shadow-sm",
          "opacity-0 group-hover:opacity-100 transition-opacity",
          // Always show when selected
          isSelected && "opacity-100",
        )}
      >
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={() => onMoveUp?.(blockId)}
              disabled={isFirst}
              aria-label="Move block up"
            >
              <ArrowUp className="h-4 w-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent>Move up</TooltipContent>
        </Tooltip>

        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={() => onMoveDown?.(blockId)}
              disabled={isLast}
              aria-label="Move block down"
            >
              <ArrowDown className="h-4 w-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent>Move down</TooltipContent>
        </Tooltip>

        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={() => onToggleVisibility?.(blockId)}
              aria-label={isVisible ? "Hide block" : "Show block"}
            >
              {isVisible ? (
                <Eye className="h-4 w-4" />
              ) : (
                <EyeOff className="h-4 w-4" />
              )}
            </Button>
          </TooltipTrigger>
          <TooltipContent>{isVisible ? "Hide" : "Show"}</TooltipContent>
        </Tooltip>

        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7 text-destructive hover:text-destructive"
              onClick={() => setShowDeleteDialog(true)}
              aria-label="Delete block"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent>Delete</TooltipContent>
        </Tooltip>
      </div>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Block</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this block? This action cannot be
              undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                onDelete?.(blockId)
                setShowDeleteDialog(false)
              }}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {children}
    </div>
  )
}
