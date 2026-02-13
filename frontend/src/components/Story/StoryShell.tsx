// src/components/Story/StoryShell.tsx
/**
 * StoryShell - Main container that orchestrates the Story page layout
 *
 * ARCHITECTURE DECISION: StoryPlayerProvider wraps StoryLayout so that
 * all panels can access shared player state via context. The shell knows
 * the storyId (from route params) and passes it to the provider.
 *
 * THEMING: Uses two-layer theme cascade:
 * 1. Page theme (outer) - affects header and overall page
 * 2. Cards theme (inner) - affects panel content areas
 */
import * as React from "react"
import { cn } from "@/lib/utils"
import { StoryHeader } from "./StoryHeader"
import { StoryLayout, type PanelConfig } from "./StoryLayout"
import {
  getPageThemeById,
  getPageThemeStyle,
} from "@/components/Common/Themes/page_themes"
import {
  getCardThemeById,
  getCardThemeStyle,
} from "@/components/Common/Themes/card_themes"
import { StoryPlayerProvider } from "./StoryPlayer"

export interface StoryShellProps {
  /** Story ID for data fetching (required for player panels) */
  storyId?: string
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

export function StoryShell({
  storyId,
  title,
  panels,
  pageThemeId,
  cardsThemeId,
  onPageThemeChange,
  onCardsThemeChange,
  className,
}: StoryShellProps) {
  const [layoutMode, setLayoutMode] = React.useState<"panels" | "tabs">("panels")

  const pageTheme = getPageThemeById(pageThemeId)
  const cardsTheme = getCardThemeById(cardsThemeId)

  return (
    // Outermost: page theme scope (affects header and content)
    // Transparent wrapper - only sets CSS variables, does not render a surface
    <div
      style={getPageThemeStyle(pageTheme)}
      className={cn("flex flex-col h-full", className)}
    >
      <StoryHeader
        title={title}
        pageThemeId={pageThemeId}
        cardsThemeId={cardsThemeId}
        onPageThemeChange={onPageThemeChange}
        onCardsThemeChange={onCardsThemeChange}
        layoutMode={layoutMode}
        onLayoutModeChange={setLayoutMode}
      />

      {/* Inner: Cards theme scope (overrides page theme for card areas) */}
      {/* Transparent wrapper - only sets CSS variables, does not render a surface */}
      <div style={getCardThemeStyle(cardsTheme)} className="flex-1 min-h-0">
        {/*
          ARCHITECTURE DECISION: Provider wraps layout so all panels
          can access shared player state without prop drilling.
          Only wrap when storyId is provided (player pages vs. listing pages).
          See StoryPlayerProvider for context shape.
        */}
        {storyId ? (
          <StoryPlayerProvider storyId={storyId}>
            <StoryLayout panels={panels} mode={layoutMode} />
          </StoryPlayerProvider>
        ) : (
          <StoryLayout panels={panels} mode={layoutMode} />
        )}
      </div>
    </div>
  )
}
