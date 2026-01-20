/**
 * CollapsiblePanel Primitive
 *
 * Wraps any panel with collapse/expand functionality.
 * Animated height transition with content fade.
 *
 * @example
 * ```tsx
 * const [collapsed, setCollapsed] = useState(false)
 *
 * <CollapsiblePanel
 *   isCollapsed={collapsed}
 *   onToggle={() => setCollapsed(!collapsed)}
 *   title="Chat"
 * >
 *   <ChatPanel />
 * </CollapsiblePanel>
 * ```
 */

import { AnimatePresence, motion } from "framer-motion"
import { Minus, Plus } from "lucide-react"
import * as React from "react"
import { Button } from "@/components/ui/button"
import {
  getTransition,
  instantTransition,
  transitions,
  useReduceMotion,
} from "@/components/ui/motion"
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { cn } from "@/lib/utils"

// ============================================================================
// Types
// ============================================================================

export interface CollapsiblePanelProps {
  /** Whether the panel is collapsed */
  isCollapsed: boolean
  /** Called when collapse state should toggle */
  onToggle: () => void
  /** Panel title (shown in collapsed state) */
  title: string
  /** Children to render when expanded */
  children: React.ReactNode
  /** Height when collapsed (default: title bar only) */
  collapsedHeight?: number
  /** Additional className for outer wrapper */
  className?: string
  /** Additional className for collapsed title bar */
  titleBarClassName?: string
  /** Keyboard shortcut hint for tooltip */
  shortcutHint?: string
}

// ============================================================================
// CollapseButton Component
// ============================================================================

interface CollapseButtonProps {
  isCollapsed: boolean
  onToggle: () => void
  shortcutHint?: string
}

export function CollapseButton({
  isCollapsed,
  onToggle,
  shortcutHint,
}: CollapseButtonProps) {
  const Icon = isCollapsed ? Plus : Minus
  const label = isCollapsed ? "Expand panel" : "Collapse panel"
  const fullLabel = shortcutHint ? `${label} (${shortcutHint})` : label

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8"
          onClick={onToggle}
          aria-label={fullLabel}
          aria-expanded={!isCollapsed}
        >
          <Icon className="h-4 w-4" />
        </Button>
      </TooltipTrigger>
      <TooltipContent side="bottom">
        <p>{fullLabel}</p>
      </TooltipContent>
    </Tooltip>
  )
}

// ============================================================================
// CollapsiblePanel Component
// ============================================================================

export function CollapsiblePanel({
  isCollapsed,
  onToggle,
  title,
  children,
  collapsedHeight = 48,
  className,
  titleBarClassName,
  shortcutHint,
}: CollapsiblePanelProps) {
  const reduceMotion = useReduceMotion()

  return (
    <motion.div
      className={cn("flex flex-col overflow-hidden", className)}
      initial={false}
      animate={{
        height: isCollapsed ? collapsedHeight : "auto",
      }}
      transition={getTransition(transitions.collapse, reduceMotion)}
    >
      {/* Collapsed title bar - always visible */}
      {isCollapsed && (
        <div
          className={cn(
            "flex items-center justify-between px-4 h-12 bg-background border-b border-border",
            titleBarClassName,
          )}
        >
          <span className="text-sm font-medium text-muted-foreground">
            {title} <span className="text-xs">(collapsed)</span>
          </span>
          <CollapseButton
            isCollapsed={isCollapsed}
            onToggle={onToggle}
            shortcutHint={shortcutHint}
          />
        </div>
      )}

      {/* Content - animated */}
      <AnimatePresence mode="wait">
        {!isCollapsed && (
          <motion.div
            key="content"
            className="flex-1 min-h-0"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={reduceMotion ? instantTransition : transitions.fade}
          >
            {children}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

// ============================================================================
// Hook for managing collapse state
// ============================================================================

/**
 * useCollapsiblePanels
 *
 * Manages collapse state for multiple panels with localStorage persistence.
 *
 * @example
 * ```tsx
 * const { isCollapsed, toggle, collapseAll, expandAll } = useCollapsiblePanels({
 *   panelIds: ["chat", "agents", "debug"],
 *   storageKey: "room-panel-collapsed",
 * })
 *
 * <CollapsiblePanel isCollapsed={isCollapsed("chat")} onToggle={() => toggle("chat")}>
 * ```
 */
export function useCollapsiblePanels(options: {
  panelIds: string[]
  storageKey?: string
  defaultCollapsed?: string[]
}) {
  const { panelIds, storageKey, defaultCollapsed = [] } = options

  const [collapsed, setCollapsed] = React.useState<Set<string>>(() => {
    if (storageKey && typeof window !== "undefined") {
      const stored = localStorage.getItem(storageKey)
      if (stored) {
        try {
          return new Set(JSON.parse(stored))
        } catch {
          // Invalid JSON, use defaults
        }
      }
    }
    return new Set(defaultCollapsed)
  })

  // Persist to localStorage
  React.useEffect(() => {
    if (storageKey && typeof window !== "undefined") {
      localStorage.setItem(storageKey, JSON.stringify([...collapsed]))
    }
  }, [collapsed, storageKey])

  const isCollapsed = React.useCallback(
    (panelId: string) => collapsed.has(panelId),
    [collapsed],
  )

  const toggle = React.useCallback((panelId: string) => {
    setCollapsed((prev) => {
      const next = new Set(prev)
      if (next.has(panelId)) {
        next.delete(panelId)
      } else {
        next.add(panelId)
      }
      return next
    })
  }, [])

  const collapseAll = React.useCallback(() => {
    setCollapsed(new Set(panelIds))
  }, [panelIds])

  const expandAll = React.useCallback(() => {
    setCollapsed(new Set())
  }, [])

  return { isCollapsed, toggle, collapseAll, expandAll }
}
