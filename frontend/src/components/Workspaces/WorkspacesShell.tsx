/**
 * WorkspacesShell
 *
 * Structural container for the workspace detail page.
 * Composes: Page theme wrapper → WorkspacesHeader → Cards theme wrapper → WorkspacesLayout.
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
 * layoutMode state lives here so both the header toggle and layout renderer
 * stay in sync without prop-drilling through an intermediate component.
 */

import * as React from "react"
import { cn } from "@/lib/utils"
import {
  type ThemeViewModel,
  themeTokensToStyle,
} from "@/services/themeService"
import { WorkspacesHeader } from "./WorkspacesHeader"
import { type PanelConfig, WorkspacesLayout } from "./WorkspacesLayout"

export interface WorkspacesShellProps {
  title: string
  description: string
  panels: PanelConfig[]
  pageTheme: ThemeViewModel | null
  cardsTheme: ThemeViewModel | null
  availablePageThemes: ThemeViewModel[]
  availableCardThemes: ThemeViewModel[]
  onPageThemeChange: (themeId: string) => void
  onCardsThemeChange: (themeId: string) => void
  backHref?: string
  defaultLayoutMode?: "panels" | "tabs"
  className?: string
}

export function WorkspacesShell({
  title,
  description,
  panels,
  pageTheme,
  cardsTheme,
  availablePageThemes,
  availableCardThemes,
  onPageThemeChange,
  onCardsThemeChange,
  backHref,
  defaultLayoutMode = "tabs",
  className,
}: WorkspacesShellProps) {
  const [layoutMode, setLayoutMode] = React.useState<"panels" | "tabs">(
    defaultLayoutMode,
  )

  // Convert theme tokens to CSS style objects
  const pageThemeStyle = themeTokensToStyle(pageTheme?.tokens)
  const cardsThemeStyle = themeTokensToStyle(cardsTheme?.tokens)

  return (
    // Outermost: Page theme scope (affects header + content)
    // Transparent wrapper — only sets CSS variables, does not render a surface
    <div
      style={pageThemeStyle}
      className={cn("flex flex-col h-full", className)}
    >
      <WorkspacesHeader
        title={title}
        description={description}
        pageTheme={pageTheme}
        cardsTheme={cardsTheme}
        availablePageThemes={availablePageThemes}
        availableCardThemes={availableCardThemes}
        onPageThemeChange={onPageThemeChange}
        onCardsThemeChange={onCardsThemeChange}
        backHref={backHref}
        layoutMode={layoutMode}
        onLayoutModeChange={setLayoutMode}
      />

      {/* Inner: Cards theme scope (overrides page theme for card areas) */}
      {/* Transparent wrapper — only sets CSS variables, does not render a surface */}
      <div style={cardsThemeStyle} className="flex-1 min-h-0">
        <WorkspacesLayout panels={panels} mode={layoutMode} />
      </div>
    </div>
  )
}
