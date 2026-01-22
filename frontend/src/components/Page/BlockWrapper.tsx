// src/components/Page/BlockWrapper.tsx

import { cn } from "@/lib/utils"

interface BlockWrapperProps {
  blockId: string
  isEditing: boolean
  isSelected: boolean
  onSelect: (blockId: string) => void
  children: React.ReactNode
  className?: string
}

/**
 * BlockWrapper - Wraps blocks to add click-to-select behavior in edit mode
 *
 * In view mode: transparent pass-through (no visual changes)
 * In edit mode: shows hover effect, click selects block
 * When selected: shows highlight ring
 */
export function BlockWrapper({
  blockId,
  isEditing,
  isSelected,
  onSelect,
  children,
  className,
}: BlockWrapperProps) {
  const handleClick = () => {
    if (isEditing) {
      onSelect(blockId)
    }
  }

  // View mode: minimal wrapper
  if (!isEditing) {
    return <div className={className}>{children}</div>
  }

  // Edit mode: interactive wrapper
  return (
    <div
      className={cn(
        "relative rounded-lg transition-all",
        "cursor-pointer",
        // Hover effect in edit mode
        "hover:ring-2 hover:ring-muted-foreground/20",
        // Selected state
        isSelected && "ring-2 ring-primary",
        className
      )}
      onClick={handleClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault()
          handleClick()
        }
      }}
      aria-pressed={isSelected}
      aria-label="Select block for editing"
    >
      {children}
    </div>
  )
}
