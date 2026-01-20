/**
 * EntityCardPopover
 *
 * Base popover wrapper for all entity cards (Agent, User, Doc).
 * Provides consistent structure: header, content, footer with actions.
 */

import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { cn } from "@/lib/utils"

interface EntityCardPopoverProps {
  /** Element that triggers the popover */
  trigger: React.ReactNode
  /** Header content (avatar, name, status) */
  header: React.ReactNode
  /** Main content area */
  children: React.ReactNode
  /** Footer content (action buttons) */
  footer?: React.ReactNode
  /** Popover alignment */
  align?: "start" | "center" | "end"
  /** Popover side */
  side?: "top" | "right" | "bottom" | "left"
  /** Additional className for content */
  className?: string
  /** Controlled open state */
  open?: boolean
  /** Controlled open change handler */
  onOpenChange?: (open: boolean) => void
}

export function EntityCardPopover({
  trigger,
  header,
  children,
  footer,
  align = "center",
  side = "bottom",
  className,
  open,
  onOpenChange,
}: EntityCardPopoverProps) {
  return (
    <Popover open={open} onOpenChange={onOpenChange}>
      <PopoverTrigger asChild>{trigger}</PopoverTrigger>
      <PopoverContent
        align={align}
        side={side}
        className={cn("w-80 p-0", className)}
      >
        <div className="border-b p-4">{header}</div>
        <div className="p-4">{children}</div>
        {footer && <div className="border-t bg-muted/30 p-3">{footer}</div>}
      </PopoverContent>
    </Popover>
  )
}
