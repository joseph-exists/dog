/**
 * InteractivePreview Component
 *
 * Draggable panel preview for the layout settings dialog.
 * Allows reordering panels via drag and drop.
 *
 * @example
 * ```tsx
 * <InteractivePreview
 *   panels={panels}
 *   onReorder={(newPanels) => setPanels(newPanels)}
 *   onRemove={(panelId) => removePanel(panelId)}
 * />
 * ```
 */

import { AnimatePresence, motion, Reorder } from "framer-motion"
import { GripVertical, Minus, Plus, X } from "lucide-react"
import { useCallback } from "react"
import { Button } from "@/components/ui/button"
import {
  getTransition,
  springConfig,
  useReduceMotion,
} from "@/components/ui/motion"
import { cn } from "@/lib/utils"

// ============================================================================
// Types
// ============================================================================

export interface PreviewPanel {
  id: string
  kind: string
  prominence: "primary" | "auxiliary"
}

export interface InteractivePreviewProps {
  /** Panels to display */
  panels: PreviewPanel[]
  /** Called when panels are reordered */
  onReorder: (panels: PreviewPanel[]) => void
  /** Called when a panel is removed */
  onRemove?: (panelId: string) => void
  /** Called when a panel's collapsed state changes (preview only) */
  onToggleCollapse?: (panelId: string) => void
  /** Collapsed panel IDs (for preview) */
  collapsedPanels?: Set<string>
  /** Whether editing is disabled */
  disabled?: boolean
  /** Additional className */
  className?: string
}

// ============================================================================
// Panel Names
// ============================================================================

const panelNames: Record<string, string> = {
  chat: "Chat",
  storyEditor: "Story Editor",
  storyRuntime: "Story Runtime",
  storyPlayer: "Solo Story Player",
  repoExplorer: "Repo Explorer",
  fileViewer: "File Viewer",
  participantPanel: "Participants",
  workspaceConnections: "Workspace Links",
  debug: "Debug",
  canvas: "Canvas",
  a2ui: "Agent UI",
}

// ============================================================================
// PreviewPanelItem Component
// ============================================================================

interface PreviewPanelItemProps {
  panel: PreviewPanel
  isCollapsed?: boolean
  onRemove?: () => void
  onToggleCollapse?: () => void
  canRemove: boolean
  disabled?: boolean
}

function PreviewPanelItem({
  panel,
  isCollapsed,
  onRemove,
  onToggleCollapse,
  canRemove,
  disabled,
}: PreviewPanelItemProps) {
  const reduceMotion = useReduceMotion()

  return (
    <motion.div
      layout
      className={cn(
        "flex items-center gap-2 px-3 py-2 rounded-md border bg-card",
        "cursor-grab active:cursor-grabbing",
        isCollapsed && "opacity-60",
        disabled && "pointer-events-none opacity-50",
      )}
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={getTransition(springConfig.snappy, reduceMotion)}
    >
      {/* Drag handle */}
      <GripVertical className="h-4 w-4 text-muted-foreground shrink-0" />

      {/* Panel name */}
      <span className="flex-1 text-sm font-medium truncate">
        {panelNames[panel.kind] || panel.kind}
      </span>

      {/* Prominence badge */}
      <span
        className={cn(
          "text-xs px-1.5 py-0.5 rounded",
          panel.prominence === "primary"
            ? "bg-blue-500/10 text-blue-600"
            : "bg-green-500/10 text-green-600",
        )}
      >
        {panel.prominence === "primary" ? "P" : "A"}
      </span>

      {/* Collapse toggle */}
      {onToggleCollapse && (
        <Button
          variant="ghost"
          size="icon"
          className="h-6 w-6"
          onClick={(e) => {
            e.stopPropagation()
            onToggleCollapse()
          }}
        >
          {isCollapsed ? (
            <Plus className="h-3 w-3" />
          ) : (
            <Minus className="h-3 w-3" />
          )}
        </Button>
      )}

      {/* Remove button */}
      {canRemove && onRemove && (
        <Button
          variant="ghost"
          size="icon"
          className="h-6 w-6 text-muted-foreground hover:text-destructive"
          onClick={(e) => {
            e.stopPropagation()
            onRemove()
          }}
        >
          <X className="h-3 w-3" />
        </Button>
      )}
    </motion.div>
  )
}

// ============================================================================
// InteractivePreview Component
// ============================================================================

export function InteractivePreview({
  panels,
  onReorder,
  onRemove,
  onToggleCollapse,
  collapsedPanels = new Set(),
  disabled = false,
  className,
}: InteractivePreviewProps) {
  const primaryPanels = panels.filter((p) => p.prominence === "primary")
  const auxiliaryPanels = panels.filter((p) => p.prominence === "auxiliary")

  // Can't remove the last panel
  const canRemove = panels.length > 1

  const handleReorder = useCallback(
    (type: "primary" | "auxiliary", newOrder: PreviewPanel[]) => {
      if (type === "primary") {
        onReorder([...newOrder, ...auxiliaryPanels])
      } else {
        onReorder([...primaryPanels, ...newOrder])
      }
    },
    [primaryPanels, auxiliaryPanels, onReorder],
  )

  return (
    <div className={cn("space-y-4", className)}>
      {/* Primary panels */}
      <div>
        <h4 className="text-xs font-medium text-muted-foreground mb-2">
          Primary Panels
        </h4>
        <Reorder.Group
          axis="y"
          values={primaryPanels}
          onReorder={(newOrder) => handleReorder("primary", newOrder)}
          className="space-y-2"
        >
          <AnimatePresence mode="popLayout">
            {primaryPanels.map((panel) => (
              <Reorder.Item
                key={panel.id}
                value={panel}
                dragListener={!disabled}
              >
                <PreviewPanelItem
                  panel={panel}
                  isCollapsed={collapsedPanels.has(panel.id)}
                  onRemove={onRemove ? () => onRemove(panel.id) : undefined}
                  onToggleCollapse={
                    onToggleCollapse
                      ? () => onToggleCollapse(panel.id)
                      : undefined
                  }
                  canRemove={canRemove}
                  disabled={disabled}
                />
              </Reorder.Item>
            ))}
          </AnimatePresence>
        </Reorder.Group>
        {primaryPanels.length === 0 && (
          <p className="text-sm text-muted-foreground text-center py-4">
            No primary panels
          </p>
        )}
      </div>

      {/* Auxiliary panels */}
      <div>
        <h4 className="text-xs font-medium text-muted-foreground mb-2">
          Auxiliary Panels
        </h4>
        <Reorder.Group
          axis="y"
          values={auxiliaryPanels}
          onReorder={(newOrder) => handleReorder("auxiliary", newOrder)}
          className="space-y-2"
        >
          <AnimatePresence mode="popLayout">
            {auxiliaryPanels.map((panel) => (
              <Reorder.Item
                key={panel.id}
                value={panel}
                dragListener={!disabled}
              >
                <PreviewPanelItem
                  panel={panel}
                  isCollapsed={collapsedPanels.has(panel.id)}
                  onRemove={onRemove ? () => onRemove(panel.id) : undefined}
                  onToggleCollapse={
                    onToggleCollapse
                      ? () => onToggleCollapse(panel.id)
                      : undefined
                  }
                  canRemove={canRemove}
                  disabled={disabled}
                />
              </Reorder.Item>
            ))}
          </AnimatePresence>
        </Reorder.Group>
        {auxiliaryPanels.length === 0 && (
          <p className="text-sm text-muted-foreground text-center py-4">
            No auxiliary panels
          </p>
        )}
      </div>

      {/* Help text */}
      <p className="text-xs text-muted-foreground text-center">
        Drag panels to reorder - P = Primary, A = Auxiliary
      </p>
    </div>
  )
}
