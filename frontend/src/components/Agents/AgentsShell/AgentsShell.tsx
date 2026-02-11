/**
 * AgentsShell
 *
 * Structural container for the agents page.
 * Composes: AgentsHeader → ambient theme wrapper div → AgentsLayout.
 *
 * The ambient theme wrapper is the architectural centerpiece:
 * a div with CSS custom properties from the selected theme.
 * All panel content inherits these variables. AgentCards with
 * their own presentation override via CSS specificity (closer scope wins).
 *
 * See Presentation/REFERENCE.md §Two Scoping Levels.
 */

import * as React from "react"
import { cn } from "@/lib/utils"
import { getThemeById } from "./themes"
import { AgentsHeader } from "./AgentsHeader"
import { type PanelConfig, AgentsLayout } from "./AgentsLayout"

export interface AgentsShellProps {
  /** Page title */
  title: string
  /** Panel configurations */
  panels: PanelConfig[]
  /** Currently selected theme ID */
  selectedThemeId: string
  /** Theme change callback */
  onThemeChange: (themeId: string) => void
  /** Additional className */
  className?: string
}

export function AgentsShell({
  title,
  panels,
  selectedThemeId,
  onThemeChange,
  className,
}: AgentsShellProps) {
  const [layoutMode, setLayoutMode] = React.useState<"panels" | "tabs">(
    "panels",
  )

  const ambientTheme = getThemeById(selectedThemeId)

  return (
    <div className={cn("flex flex-col h-full", className)}>
      <AgentsHeader
        title={title}
        selectedThemeId={selectedThemeId}
        onThemeChange={onThemeChange}
        layoutMode={layoutMode}
        onLayoutModeChange={setLayoutMode}
      />

      {/* Ambient theme wrapper — sets CSS variables for all panel content */}
      <div style={ambientTheme.style} className="flex-1 min-h-0">
        <AgentsLayout panels={panels} mode={layoutMode} />
      </div>
    </div>
  )
}
