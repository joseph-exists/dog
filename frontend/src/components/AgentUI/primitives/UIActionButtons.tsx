import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import type { UIActionButtonsData } from "../types"

const layoutClasses = {
  horizontal: "flex flex-wrap gap-2",
  vertical: "flex flex-col gap-2",
  grid: "grid grid-cols-2 gap-2",
}

interface UIActionButtonsProps {
  data: UIActionButtonsData
  onAction?: (action: string) => void
}

export function UIActionButtons({ data, onAction }: UIActionButtonsProps) {
  const buttons = Array.isArray(data.buttons) ? data.buttons : []

  return (
    <div className={cn(layoutClasses[data.layout || "horizontal"])}>
      {buttons.map((btn, idx) => (
        <Button
          key={idx}
          variant={
            btn.variant === "primary"
              ? "default"
              : btn.variant === "outline"
                ? "outline"
                : btn.variant === "ghost"
                  ? "ghost"
                  : "secondary"
          }
          size="sm"
          disabled={btn.disabled}
          onClick={() => onAction?.(btn.action)}
        >
          {btn.label}
        </Button>
      ))}
    </div>
  )
}
