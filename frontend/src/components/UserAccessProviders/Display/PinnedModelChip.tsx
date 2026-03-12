import { GripVertical, Pin, Star } from "lucide-react"
import type { LLMModelPublic } from "@/client/types.gen"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

interface PinnedModelChipProps {
  model: LLMModelPublic
  dragHandleProps?: React.HTMLAttributes<HTMLSpanElement>
  isDragging?: boolean
}

export function PinnedModelChip({
  model,
  dragHandleProps,
  isDragging = false,
}: PinnedModelChipProps) {
  return (
    <Badge
      variant="secondary"
      className={cn(
        "gap-1 rounded-full border border-border/60 bg-secondary/60 px-3 py-1",
        isDragging && "opacity-70 shadow-sm",
      )}
    >
      <span
        className="inline-flex cursor-grab items-center text-muted-foreground active:cursor-grabbing"
        {...dragHandleProps}
      >
        <GripVertical className="h-3 w-3" />
      </span>
      <Pin className="h-3 w-3" />
      {model.display_name}
      {model.is_default ? <Star className="h-3 w-3" /> : null}
    </Badge>
  )
}
