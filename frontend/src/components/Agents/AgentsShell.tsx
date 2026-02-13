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
import { AgentsHeader, type AgentType } from "./AgentsHeader"
import { AgentsLayout, type PanelConfig } from "./AgentsLayout"
// import { getThemeById, getThemeStyle } from "./themes"
import { getPageThemeById, getPageThemeStyle } from "@/components/Common/Themes/page_themes"
import { getCardThemeById, getCardThemeStyle } from "@/components/Common/Themes/card_themes"


export interface AgentsShellProps {
  /** Page title */
  title: string
  /** Agent type - controls header icon and available actions */
  type: AgentType
  /** Whether the current user can edit */
  canEdit: boolean
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
  type,
  canEdit,
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

  const pageTheme = getPageThemeById(pageThemeId)
  const cardsTheme = getCardThemeById(cardsThemeId)

  return (
    // Outermost: Page theme scope (affects header + content)
    // Transparent wrapper — only sets CSS variables, does not render a surface
    // Downstream components (Header, PanelContainer) render with inherited variables
    <div
      style={getPageThemeStyle(pageTheme)}
      className={cn("flex flex-col h-full", className)}
    >
      <AgentsHeader
        title={title}
        type={type}
        canEdit={canEdit}
        pageThemeId={pageThemeId}
        cardsThemeId={cardsThemeId}
        onPageThemeChange={onPageThemeChange}
        onCardsThemeChange={onCardsThemeChange}
        layoutMode={layoutMode}
        onLayoutModeChange={setLayoutMode}
      />

      {/* Inner: Cards theme scope (overrides page theme for card areas) */}
      {/* Transparent wrapper — only sets CSS variables, does not render a surface */}
      <div style={getCardThemeStyle(cardsTheme)} className="flex-1 min-h-0">
        <AgentsLayout panels={panels} mode={layoutMode} />
      </div>
    </div>
  )
}
