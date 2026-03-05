/**
 * MiniPreview Primitive
 *
 * Small visual representation of a panel layout.
 * Used in preset picker, settings dialogs, and Users page.
 *
 * @example
 * ```tsx
 * <MiniPreview
 *   panels={[
 *     { id: "chat", kind: "chat", prominence: "primary" },
 *     { id: "participants", kind: "participantPanel", prominence: "auxiliary" },
 *   ]}
 * />
 * ```
 */

import { cn } from "@/lib/utils"

// ============================================================================
// Types
// ============================================================================

export interface MiniPreviewPanel {
  id: string
  kind: string
  prominence: "primary" | "auxiliary"
}

export interface MiniPreviewProps {
  /** Panels to display */
  panels: MiniPreviewPanel[]
  /** Width of the preview (default: 120) */
  width?: number
  /** Height of the preview (default: 80) */
  height?: number
  /** Show panel labels */
  showLabels?: boolean
  /** Optional override for panel labels */
  panelLabels?: Record<string, string>
  /** Optional override for panel colors/classes */
  panelColors?: Record<string, string>
  /** Additional className */
  className?: string
}

// ============================================================================
// Panel kind to display name mapping
// ============================================================================

const panelNames: Record<string, string> = {
  chat: "Chat",
  storyEditor: "Story",
  storyRuntime: "Runtime",
  participantPanel: "Participants",
  debug: "Debug",
  canvas: "Canvas",
  a2ui: "A2UI",
}

// ============================================================================
// Panel kind to color mapping (using CSS variables)
// ============================================================================

const panelColors: Record<string, string> = {
  chat: "bg-blue-500/20 border-blue-500/30",
  storyEditor: "bg-purple-500/20 border-purple-500/30",
  storyRuntime: "bg-amber-500/20 border-amber-500/30",
  participantPanel: "bg-green-500/20 border-green-500/30",
  debug: "bg-orange-500/20 border-orange-500/30",
  canvas: "bg-pink-500/20 border-pink-500/30",
  a2ui: "bg-cyan-500/20 border-cyan-500/30",
}

// ============================================================================
// MiniPreview Component
// ============================================================================

export function MiniPreview({
  panels,
  width = 120,
  height = 80,
  showLabels = true,
  panelLabels,
  panelColors: panelColorOverrides,
  className,
}: MiniPreviewProps) {
  const resolvedPanelNames = panelLabels ?? panelNames
  const resolvedPanelColors = panelColorOverrides ?? panelColors
  const primaryPanels = panels.filter((p) => p.prominence === "primary")
  const auxiliaryPanels = panels.filter((p) => p.prominence === "auxiliary")

  const hasPrimary = primaryPanels.length > 0
  const hasAuxiliary = auxiliaryPanels.length > 0

  // Calculate proportions
  const primaryWidth = hasAuxiliary ? 0.7 : 1
  const auxiliaryWidth = 0.3

  return (
    <div
      className={cn(
        "flex rounded border border-border bg-muted/30 overflow-hidden",
        className,
      )}
      style={{ width, height }}
      role="img"
      aria-label={`Layout preview: ${panels.map((p) => resolvedPanelNames[p.kind] || p.kind).join(", ")}`}
    >
      {/* Primary panels */}
      {hasPrimary && (
        <div
          className="flex gap-0.5 p-0.5"
          style={{ width: `${primaryWidth * 100}%` }}
        >
          {primaryPanels.map((panel) => (
            <div
              key={panel.id}
              className={cn(
                "flex-1 rounded-sm border flex items-center justify-center",
                resolvedPanelColors[panel.kind] || "bg-muted border-border",
              )}
            >
              {showLabels && (
                <span className="text-[8px] text-muted-foreground font-medium truncate px-0.5">
                  {resolvedPanelNames[panel.kind] || panel.kind}
                </span>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Auxiliary panels (stacked) */}
      {hasAuxiliary && (
        <div
          className="flex flex-col gap-0.5 p-0.5 border-l border-border"
          style={{ width: `${auxiliaryWidth * 100}%` }}
        >
          {auxiliaryPanels.map((panel) => (
            <div
              key={panel.id}
              className={cn(
                "flex-1 rounded-sm border flex items-center justify-center",
                resolvedPanelColors[panel.kind] || "bg-muted border-border",
              )}
            >
              {showLabels && (
                <span className="text-[6px] text-muted-foreground font-medium truncate px-0.5">
                  {resolvedPanelNames[panel.kind]?.substring(0, 3) ||
                    panel.kind.substring(0, 3)}
                </span>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Empty state */}
      {panels.length === 0 && (
        <div className="flex-1 flex items-center justify-center">
          <span className="text-[8px] text-muted-foreground">Empty</span>
        </div>
      )}
    </div>
  )
}
