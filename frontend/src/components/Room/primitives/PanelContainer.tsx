/**
 * PanelContainer Primitive
 *
 * Standard container for all room panels.
 * Provides consistent header/content/footer structure.
 */

import * as React from "react"
import { cn } from "@/lib/utils"

interface PanelContainerProps {
  /** Panel title displayed in header */
  title?: string
  /** Optional header actions (right side) */
  headerActions?: React.ReactNode
  /** Optional footer content */
  footer?: React.ReactNode
  /** Main content */
  children: React.ReactNode
  /** Additional className for the container */
  className?: string
  /** Whether content area should scroll */
  scrollable?: boolean
}

export function PanelContainer({
  title,
  headerActions,
  footer,
  children,
  className,
  scrollable = true,
}: PanelContainerProps) {
  return (
    <div className={cn("flex flex-col h-full bg-background", className)}>
      {/* Header */}
      {(title || headerActions) && (
        <div className="flex items-center justify-between px-4 py-3 border-b border-border shrink-0">
          {title && (
            <h3 className="text-sm font-medium text-foreground">{title}</h3>
          )}
          {headerActions && (
            <div className="flex items-center gap-2">{headerActions}</div>
          )}
        </div>
      )}

      {/* Content */}
      <div
        className={cn(
          "flex-1 min-h-0",
          scrollable && "overflow-y-auto"
        )}
      >
        {children}
      </div>

      {/* Footer */}
      {footer && (
        <div className="shrink-0 border-t border-border">{footer}</div>
      )}
    </div>
  )
}
