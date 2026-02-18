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
 *
 * Themes are resolved by the route via usePageThemes hook and passed
 * as ThemeViewModel objects. The shell converts tokens to CSS styles.
 */
import * as React from "react"
import { cn } from "@/lib/utils"
import {
  type ThemeViewModel,
  themeTokensToStyle,
} from "@/services/themeService"
import { StoryHeader, type StoryType } from "./StoryHeader"
import { type PanelConfig, StoryLayout } from "./StoryLayout"
import { StoryPlayerProvider } from "./StoryPlayer"

export interface StoryShellProps {
  /** Story ID for data fetching (required for player panels) */
  storyId?: string
  /** Page title */
  title: string
  /** Story type - controls header icon and available actions */
  type: StoryType
  /** Whether the current user can edit this story */
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

export function StoryShell({
  storyId,
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
}: StoryShellProps) {
  const [layoutMode, setLayoutMode] = React.useState<"panels" | "tabs">(
    "panels",
  )

  // Convert theme tokens to CSS style objects
  const pageThemeStyle = themeTokensToStyle(pageTheme?.tokens)
  const cardsThemeStyle = themeTokensToStyle(cardsTheme?.tokens)

  return (
    // Outermost: page theme scope (affects header and content)
    // Transparent wrapper - only sets CSS variables, does not render a surface
    <div
      style={pageThemeStyle}
      className={cn("flex flex-col h-full", className)}
    >
      <StoryHeader
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
      {/* Transparent wrapper - only sets CSS variables, does not render a surface */}
      <div style={cardsThemeStyle} className="flex-1 min-h-0">
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
