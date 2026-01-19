/**
 * ActionBar Primitive
 *
 * Horizontal row of icon buttons for panel headers and footers.
 */

import * as React from "react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import type { LucideIcon } from "lucide-react"

export interface ActionItem {
  /** Unique identifier */
  id: string
  /** Icon component */
  icon: LucideIcon
  /** Tooltip label */
  label: string
  /** Click handler */
  onClick: () => void
  /** Whether action is disabled */
  disabled?: boolean
  /** Variant for visual distinction */
  variant?: "default" | "destructive"
}

interface ActionBarProps {
  /** Array of action items */
  actions: ActionItem[]
  /** Size of buttons */
  size?: "sm" | "default"
  /** Additional className */
  className?: string
}

export function ActionBar({
  actions,
  size = "sm",
  className,
}: ActionBarProps) {
  return (
    <div className={cn("flex items-center gap-1", className)}>
      {actions.map((action) => (
        <Tooltip key={action.id}>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size={size === "sm" ? "icon" : "default"}
              onClick={action.onClick}
              disabled={action.disabled}
              className={cn(
                size === "sm" && "h-8 w-8",
                action.variant === "destructive" && "text-destructive hover:text-destructive"
              )}
            >
              <action.icon className={cn(size === "sm" ? "h-4 w-4" : "h-5 w-5")} />
              <span className="sr-only">{action.label}</span>
            </Button>
          </TooltipTrigger>
          <TooltipContent side="bottom">
            <p>{action.label}</p>
          </TooltipContent>
        </Tooltip>
      ))}
    </div>
  )
}
