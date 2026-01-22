// src/components/Page/editor/BlockPalette.tsx

import { ChevronLeft, ChevronRight, LayoutGrid } from "lucide-react"
import { BLOCK_TYPES, type BlockType } from "@/components/Page/registry"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { BlockPaletteItem } from "./BlockPaletteItem"

interface BlockPaletteProps {
  onAddBlock: (type: BlockType, column: "primary" | "auxiliary") => void
  targetColumn: "primary" | "auxiliary"
  className?: string
  isOpen?: boolean
  onToggle?: () => void
}

/**
 * BlockPalette - Sidebar listing all available block types
 *
 * Displays draggable/clickable block type items.
 * Can be collapsed to save space.
 */
export function BlockPalette({
  onAddBlock,
  targetColumn,
  className,
  isOpen = true,
  onToggle,
}: BlockPaletteProps) {
  const handleAddBlock = (type: BlockType) => {
    onAddBlock(type, targetColumn)
  }

  if (!isOpen) {
    return (
      <div
        className={cn(
          "flex flex-col border-r border-border bg-background",
          className
        )}
      >
        <Button
          variant="ghost"
          size="icon"
          onClick={onToggle}
          className="m-2"
          aria-label="Open block palette"
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    )
  }

  return (
    <div
      className={cn(
        "flex flex-col w-[220px] border-r border-border bg-background shrink-0",
        className
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-border">
        <div className="flex items-center gap-2">
          <LayoutGrid className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-medium">Blocks</span>
        </div>
        {onToggle && (
          <Button
            variant="ghost"
            size="icon"
            onClick={onToggle}
            className="h-7 w-7"
            aria-label="Close block palette"
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
        )}
      </div>

      {/* Block list */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-2 space-y-1">
          {BLOCK_TYPES.map((blockType) => (
            <BlockPaletteItem
              key={blockType.type}
              blockType={blockType}
              onClick={handleAddBlock}
            />
          ))}
        </div>
      </div>

      {/* Footer hint */}
      <div className="px-3 py-2 border-t border-border">
        <p className="text-xs text-muted-foreground">
          Click or drag blocks to add them to the {targetColumn} column
        </p>
      </div>
    </div>
  )
}
