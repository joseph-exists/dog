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
 * Themes are resolved by the route via usePageThemes hook and passed
 * as ThemeViewModel objects. The shell converts tokens to CSS styles.
 *
 * See Presentation/REFERENCE.md §Two Scoping Levels.
 */

import * as React from "react"
import { cn } from "@/lib/utils"
import {
  type ThemeViewModel,
  themeTokensToStyle,
} from "@/services/themeService"
import { AgentsHeader, type AgentType } from "./AgentsHeader"
import { AgentsLayout, type PanelConfig } from "./AgentsLayout"

export interface AgentsShellProps {
  /** Page title */
  title: string
  /** Agent type - controls header icon and available actions */
  type: AgentType
  /** Whether the current user can edit */
  canEdit: boolean
  /** Panel configurations */
  panels: PanelConfig[]
  /** Resolved page theme (from usePageThemes hook) */
  pageTheme: ThemeViewModel | null
  /** Resolved cards theme (from usePageThemes hook) */
  cardsTheme: ThemeViewModel | null
  /** Available page themes for picker */
  availablePageThemes: ThemeViewModel[]
  /** Available card themes for picker */
  availableCardThemes: ThemeViewModel[]
  /** Page theme change callback */
  onPageThemeChange: (themeId: string) => void
  /** Cards theme change callback */
  onCardsThemeChange: (themeId: string) => void
  /** Whether themes are still loading */
  isLoadingThemes?: boolean
  /** Additional className */
  className?: string
}

export function AgentsShell({
  title,
  type,
  canEdit,
  panels,
  pageTheme,
  cardsTheme,
  availablePageThemes,
  availableCardThemes,
  onPageThemeChange,
  onCardsThemeChange,
  // isLoadingThemes,
  className,
}: AgentsShellProps) {
  const [layoutMode, setLayoutMode] = React.useState<"panels" | "tabs">(
    "panels",
  )

  // Convert theme tokens to CSS style objects
  const pageThemeStyle = themeTokensToStyle(pageTheme?.tokens)
  const cardsThemeStyle = themeTokensToStyle(cardsTheme?.tokens)

  return (
    // Outermost: Page theme scope (affects header + content)
    // Transparent wrapper — only sets CSS variables, does not render a surface
    // Downstream components (Header, PanelContainer) render with inherited variables
    <div
      style={pageThemeStyle}
      className={cn("flex flex-col h-full", className)}
    >
      <AgentsHeader
        title={title}
        type={type}
        canEdit={canEdit}
        // Pass theme info to header for picker
        pageTheme={pageTheme}
        cardsTheme={cardsTheme}
        availablePageThemes={availablePageThemes}
        availableCardThemes={availableCardThemes}
        onPageThemeChange={onPageThemeChange}
        onCardsThemeChange={onCardsThemeChange}
        layoutMode={layoutMode}
        onLayoutModeChange={setLayoutMode}
      />

      {/* Inner: Cards theme scope (overrides page theme for card areas) */}
      {/* Transparent wrapper — only sets CSS variables, does not render a surface */}
      <div style={cardsThemeStyle} className="flex-1 min-h-0">
        <AgentsLayout panels={panels} mode={layoutMode} />
      </div>
    </div>
  )
}
