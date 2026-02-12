/**
 * AgentsShell
 *
 * Structural container for the agents page.
 * Composes: Page theme wrapper → AgentsHeader → Cards theme wrapper → AgentsLayout.
 *
 * Two nested theme wrappers enable the 4-layer cascade:
 *   Application (:root) → Page theme → Cards theme → Individual card presentation
 *
 * CSS custom property inheritance means inner wrappers override outer ones
 * for the same variable. No specificity hacks needed.
 *
 * See Presentation/REFERENCE.md §Two Scoping Levels.
 */

import * as React from "react"
import { cn } from "@/lib/utils"
import { AgentsHeader } from "./AgentsHeader"
import { AgentsLayout, type PanelConfig } from "./AgentsLayout"
import { getThemeById, getThemeStyle } from "./themes"

export interface AgentsShellProps {
  /** Page title */
  title: string
  /** Panel configurations */
  panels: PanelConfig[]
  /** Currently selected page theme ID */
  pageThemeId: string
  /** Currently selected cards theme ID */
  cardsThemeId: string
  /** Page theme change callback */
  onPageThemeChange: (themeId: string) => void
  /** Cards theme change callback */
  onCardsThemeChange: (themeId: string) => void
  /** Additional className */
  className?: string
}

export function AgentsShell({
  title,
  panels,
  pageThemeId,
  cardsThemeId,
  onPageThemeChange,
  onCardsThemeChange,
  className,
}: AgentsShellProps) {
  const [layoutMode, setLayoutMode] = React.useState<"panels" | "tabs">(
    "panels",
  )

  const pageTheme = getThemeById(pageThemeId)
  const cardsTheme = getThemeById(cardsThemeId)

  return (
    // Outermost: Page theme scope (affects header + content)
    // Transparent wrapper — only sets CSS variables, does not render a surface
    // Downstream components (Header, PanelContainer) render with inherited variables
    <div
      style={getThemeStyle(pageTheme)}
      className={cn("flex flex-col h-full", className)}
    >
      <AgentsHeader
        title={title}
        pageThemeId={pageThemeId}
        cardsThemeId={cardsThemeId}
        onPageThemeChange={onPageThemeChange}
        onCardsThemeChange={onCardsThemeChange}
        layoutMode={layoutMode}
        onLayoutModeChange={setLayoutMode}
      />

      {/* Inner: Cards theme scope (overrides page theme for card areas) */}
      {/* Transparent wrapper — only sets CSS variables, does not render a surface */}
      <div style={getThemeStyle(cardsTheme)} className="flex-1 min-h-0">
        <AgentsLayout panels={panels} mode={layoutMode} />
      </div>
    </div>
  )
}
