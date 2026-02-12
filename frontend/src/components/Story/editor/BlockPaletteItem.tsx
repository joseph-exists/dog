// src/components/Page/editor/BlockPaletteItem.tsx

import type { BlockType, BlockTypeDefinition } from "@/components/Page/registry"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface BlockPaletteItemProps {
  blockType: BlockTypeDefinition
  onDragStart?: (type: BlockType) => void
  onDragEnd?: () => void
  onClick?: (type: BlockType) => void
}

export function BlockPaletteItem({
  blockType,
  onDragStart,
  onDragEnd,
  onClick,
}: BlockPaletteItemProps) {
  const Icon = blockType.icon

  const handleDragStart = (e: React.DragEvent) => {
    e.dataTransfer.setData("application/x-block-type", blockType.type)
    e.dataTransfer.effectAllowed = "copy"
    onDragStart?.(blockType.type)
  }

  const handleDragEnd = () => {
    onDragEnd?.()
  }

  const handleClick = () => {
    onClick?.(blockType.type)
  }

  return (
    <Button
      variant="ghost"
      className={cn(
        "w-full justify-start gap-2 h-auto py-2 px-3",
        "cursor-grab active:cursor-grabbing",
      )}
      draggable
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
      onClick={handleClick}
      title={blockType.description}
    >
      <Icon className="h-4 w-4 shrink-0" />
      <span className="text-sm truncate">{blockType.label}</span>
    </Button>
  )
}
