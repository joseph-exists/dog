import { Minus, Plus } from "lucide-react"
import type React from "react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface DemoCollapsibleSurfaceProps {
  title: string
  isCollapsed: boolean
  onToggle: () => void
  children: React.ReactNode
  className?: string
  contentClassName?: string
}

export function DemoCollapsibleSurface({
  title,
  isCollapsed,
  onToggle,
  children,
  className,
  contentClassName,
}: DemoCollapsibleSurfaceProps) {
  if (isCollapsed) {
    return (
      <div
        className={cn(
          "flex h-full min-h-0 flex-col overflow-hidden rounded-lg border bg-background/95",
          className,
        )}
      >
        <div className="flex h-12 items-center justify-between border-b border-border px-4">
          <span className="truncate text-sm font-medium text-foreground">
            {title}{" "}
            <span className="text-xs text-muted-foreground">(collapsed)</span>
          </span>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={onToggle}
            aria-label={`Expand ${title}`}
            aria-expanded={false}
          >
            <Plus className="h-4 w-4" />
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className={cn("relative h-full min-h-0", className)}>
      <div className="pointer-events-none absolute right-2 top-2 z-30">
        <Button
          type="button"
          variant="secondary"
          size="icon"
          className="pointer-events-auto h-8 w-8 shadow-sm"
          onClick={onToggle}
          aria-label={`Collapse ${title}`}
          aria-expanded={true}
        >
          <Minus className="h-4 w-4" />
        </Button>
      </div>
      <div className={cn("h-full min-h-0", contentClassName)}>{children}</div>
    </div>
  )
}
